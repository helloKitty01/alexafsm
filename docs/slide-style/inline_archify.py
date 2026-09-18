#!/usr/bin/env python3
"""把 archify deliver 出的 HTML 里的 SVG 抽成可内联进幻灯片的片段,并保留动态钩子。

用法:
    python3 inline_archify.py spec.json delivered.html --suffix wu [--out fragment.json]

输出(JSON):
    { "svg": "<svg class=\"archify\" ...>…</svg>", "chapters": [ {"l": 章名, "t": 说明, "n": [节点 id…], "e": [边 id…]} … ] }

做了什么:
  1. 只取 <svg>…</svg>;去掉背景 grid 矩形与 pattern、data-preset / data-quality-profile(由幻灯片的 html[data-*] 接管)。
  2. 所有 id 加页内唯一后缀,同步替换 url(#…) / aria-labelledby / href="#…";一页可放多张图。
  3. 去掉 tabindex / role="button" / aria-pressed / aria-label(幻灯片里不需要可聚焦节点),
     但保留 data-node-id / data-edge-id / data-edge-from / data-edge-to / data-animate / --step / data-composition-points,
     这些是幻灯片分章高亮与 trace 动画的钩子。
  4. sequence 的消息只有 data-composition-edge-*,统一补成 data-edge-*,让五种图型在幻灯片侧用同一套选择器。
  5. 章节:非 sequence 图取 meta.views(n = focus,e = 两端都在 focus 内的边);
     sequence 图按 segments 切章(e = y 落在段内的消息,n = 这些消息涉及的参与者),views 数量一致时借用其 note。
"""
import argparse
import json
import re
import sys

EDGE_COLLECTION = {
    'architecture': 'connections',
    'workflow': 'edges',
    'dataflow': 'flows',
    'lifecycle': 'transitions',
}


def extract_svg(html: str) -> str:
    a = html.find('<svg viewBox')
    if a < 0:
        a = html.find('<svg ')
    b = html.find('</svg>', a)
    if a < 0 or b < 0:
        sys.exit('no <svg> found')
    return html[a:b + 6]


def clean_svg(svg: str, suffix: str) -> str:
    # 根元素:去 preset / quality,加 class
    svg = re.sub(r'\sdata-preset="[^"]*"', '', svg, count=1)
    svg = re.sub(r'\sdata-quality-profile="[^"]*"', '', svg, count=1)
    svg = svg.replace('<svg ', '<svg class="archify" ', 1)
    # 背景网格
    svg = re.sub(r'\s*<pattern id="grid".*?</pattern>', '', svg, flags=re.S)
    svg = re.sub(r'\s*<!-- Background Grid -->\s*<rect[^>]*fill="url\(#grid\)"[^>]*/>', '', svg)
    svg = re.sub(r'\s*<rect[^>]*fill="url\(#grid\)"[^>]*/>', '', svg)
    # 可聚焦属性
    svg = re.sub(r'\s(tabindex|role|aria-pressed|aria-label)="[^"]*"', '', svg)
    # sequence 消息:补 data-edge-*
    def fix_msg(m):
        tag = m.group(0)
        if 'data-edge-id=' in tag:
            return tag
        fr = re.search(r'data-composition-edge-from="([^"]*)"', tag)
        to = re.search(r'data-composition-edge-to="([^"]*)"', tag)
        eid = re.search(r'data-composition-edge-id="([^"]*)"', tag)
        if not (fr and to):
            return tag
        add = f' data-edge-from="{fr.group(1)}" data-edge-to="{to.group(1)}"'
        if eid:
            add += f' data-edge-id="{eid.group(1)}"'
        return tag.replace('<path ', '<path' + add + ' ', 1)
    svg = re.sub(r'<path [^>]*data-composition-edge-from[^>]*>', fix_msg, svg)
    # id 后缀
    ids = set(re.findall(r'\sid="([^"]+)"', svg))
    for i in sorted(ids, key=len, reverse=True):
        svg = svg.replace(f'id="{i}"', f'id="{i}-{suffix}"')
        svg = svg.replace(f'url(#{i})', f'url(#{i}-{suffix})')
        svg = svg.replace(f'href="#{i}"', f'href="#{i}-{suffix}"')
    def fix_labelled(m):
        return 'aria-labelledby="' + ' '.join(f'{x}-{suffix}' for x in m.group(1).split()) + '"'
    svg = re.sub(r'aria-labelledby="([^"]+)"', fix_labelled, svg)
    # 压缩多余空行
    svg = re.sub(r'\n\s*\n+', '\n', svg)
    return svg


def chapters_from_spec(spec: dict) -> list:
    kind = spec.get('diagram_type')
    meta = spec.get('meta', {})
    views = meta.get('views') or []
    out = []
    if kind == 'sequence':
        msgs = spec.get('messages', [])
        segs = spec.get('segments', [])
        for i, sg in enumerate(segs):
            in_seg = [m for m in msgs if sg['from'] <= m['y'] <= sg['to']]
            e = [m.get('id') or f"{m['from']}-{m['to']}" for m in in_seg]
            n = []
            for m in in_seg:
                for p in (m['from'], m['to']):
                    if p not in n:
                        n.append(p)
            note = views[i].get('note', '') if len(views) == len(segs) else ''
            out.append({'l': sg.get('label', f'第 {i + 1} 段'), 't': note, 'n': n, 'e': e})
        return out
    coll = spec.get(EDGE_COLLECTION.get(kind, 'edges'), [])
    for v in views:
        focus = set(v.get('focus', []))
        e = [c.get('id') or f"{c['from']}-{c['to']}" for c in coll if c['from'] in focus and c['to'] in focus]
        out.append({'l': v.get('label', v.get('id')), 't': v.get('note', ''), 'n': list(v.get('focus', [])), 'e': e})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('spec')
    ap.add_argument('html')
    ap.add_argument('--suffix', required=True)
    ap.add_argument('--out')
    a = ap.parse_args()
    spec = json.load(open(a.spec, encoding='utf8'))
    html = open(a.html, encoding='utf8').read()
    frag = {'svg': clean_svg(extract_svg(html), a.suffix), 'chapters': chapters_from_spec(spec),
            'type': spec.get('diagram_type'), 'title': spec.get('meta', {}).get('title', '')}
    s = json.dumps(frag, ensure_ascii=False, indent=1)
    if a.out:
        open(a.out, 'w', encoding='utf8').write(s)
    else:
        print(s)


if __name__ == '__main__':
    main()
