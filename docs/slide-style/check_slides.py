#!/usr/bin/env python3
"""三视口逐页校验 HTML 幻灯片是否溢出(借鉴 archify 的 visual-check 纪律:不许用裁切假装通过)。

用法:
    python3 check_slides.py deck.slides.html [more.html ...] [--shots DIR] [--viewports 1440x900,1600x1000,1920x1080]

检查项(每个视口 × 每一页):
  1. 文档不出现滚动条:documentElement.scrollWidth <= innerWidth 且 scrollHeight <= innerHeight
  2. 页内任何元素的内容不超出自身盒子:scrollHeight <= clientHeight + 1 且 scrollWidth <= clientWidth + 1
     (含 overflow:visible 的元素——那正是会"压到相邻区块"的情况;overflow:hidden 的元素同样报,
      因为裁切不是通过。标了 data-allow-overflow 的元素跳过。)
  3. 页内任何元素的外框不超出 .slide 的外框(spill)。
可选 --shots 每页每视口截一张图,便于人工复核。

依赖:playwright(pip install playwright && playwright install chromium)。
幻灯片需暴露 window.__go(i) 翻页,或使用 .slide.active 约定;本仓库各 deck 均满足。
"""
import argparse
import os
import sys
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover
    print("需要 playwright:pip install playwright && playwright install chromium", file=sys.stderr)
    sys.exit(2)

JS_PAGE_REPORT = r"""
() => {
  const slide = document.querySelector('.slide.active');
  if (!slide) return { error: 'no .slide.active' };
  const sr = slide.getBoundingClientRect();
  const doc = document.documentElement;
  const out = {
    docOverflow: (doc.scrollWidth > window.innerWidth) || (doc.scrollHeight > window.innerHeight),
    docSize: [doc.scrollWidth, doc.scrollHeight, window.innerWidth, window.innerHeight],
    overflow: [], spill: []
  };
  const desc = (el) => {
    let s = el.tagName.toLowerCase();
    if (el.id) s += '#' + el.id;
    if (el.classList.length) s += '.' + [...el.classList].slice(0, 3).join('.');
    const t = (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 28);
    return s + (t ? ' “' + t + '”' : '');
  };
  slide.querySelectorAll('*').forEach((el) => {
    if (el.closest('[data-allow-overflow]')) return;
    if (el.tagName === 'svg' || el.closest('svg')) return;
    if (el.tagName === 'TR' || el.tagName === 'TBODY') return;  // rowspan 单元格会让 tr 的 scrollHeight 天然大于自身
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.display === 'inline' || cs.position === 'absolute' || cs.position === 'fixed') return;
    const dh = el.scrollHeight - el.clientHeight, dw = el.scrollWidth - el.clientWidth;
    if ((dh > 1 || dw > 1) && el.clientHeight > 0) {
      out.overflow.push({ el: desc(el), dh, dw, h: el.clientHeight, w: el.clientWidth });
    }
    const r = el.getBoundingClientRect();
    if (r.width > 0 && (r.right > sr.right + 1 || r.bottom > sr.bottom + 1 || r.left < sr.left - 1 || r.top < sr.top - 1)) {
      out.spill.push({ el: desc(el), right: Math.round(r.right - sr.right), bottom: Math.round(r.bottom - sr.bottom) });
    }
  });
  return out;
}
"""


def check(html: Path, viewports, shots) -> int:
    failures = 0
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for (w, h) in viewports:
            page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
            page.goto(html.resolve().as_uri())
            page.wait_for_timeout(200)
            n = page.evaluate("document.querySelectorAll('.slide').length")
            print(f"\n== {html.name} @ {w}x{h} · {n} 页")
            for i in range(n):
                page.evaluate(f"window.__go ? window.__go({i}) : document.querySelectorAll('.slide').forEach((s,j)=>s.classList.toggle('active', j==={i}))")
                page.wait_for_timeout(60)
                rep = page.evaluate(JS_PAGE_REPORT)
                if rep.get("error"):
                    print(f"  P{i+1}: {rep['error']}"); failures += 1; continue
                bad = rep["docOverflow"] or rep["overflow"] or rep["spill"]
                mark = "FAIL" if bad else "ok  "
                print(f"  {mark} P{i+1}")
                if rep["docOverflow"]:
                    print(f"       文档滚动:scroll {rep['docSize'][0]}x{rep['docSize'][1]} > viewport {rep['docSize'][2]}x{rep['docSize'][3]}")
                for o in rep["overflow"][:12]:
                    print(f"       内容溢出 +{o['dh']}px 高 / +{o['dw']}px 宽 (盒 {o['w']}x{o['h']}) ← {o['el']}")
                for s in rep["spill"][:8]:
                    print(f"       出页 右{s['right']:+d} 下{s['bottom']:+d} ← {s['el']}")
                if bad:
                    failures += 1
                if shots:
                    shots.mkdir(parents=True, exist_ok=True)
                    page.screenshot(path=str(shots / f"{html.stem}.{w}x{h}.p{i+1:02d}.png"))
            page.close()
        browser.close()
    return failures


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--viewports", default="1440x900,1600x1000,1920x1080")
    ap.add_argument("--shots", default=None, help="截图输出目录(可选)")
    a = ap.parse_args()
    vps = [tuple(int(x) for x in v.split("x")) for v in a.viewports.split(",")]
    total = 0
    for f in a.files:
        total += check(Path(f), vps, Path(a.shots) if a.shots else None)
    print(f"\n共 {total} 处失败" if total else "\n全部通过")
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
