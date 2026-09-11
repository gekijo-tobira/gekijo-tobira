#!/usr/bin/env python3
"""記事の h2/h3 に id を振り、frontmatter に toc 配列を作って <Toc> を差し込む。

冪等（何度流しても同じ結果）。見出しを足したあとに流し直せば toc も更新される。
id は出現順の連番（sec-1, sec-1-1 …）。見出しの順番を入れ替えると
id も変わるので、公開済みのアンカーを共有したあとは順番を変えないこと。
"""
import io, re, sys, os

FILES = ['how-to-get-tickets', 'after-winning-tickets', 'akb48-cdtv-sukiish']
ROOT = os.path.join(os.path.dirname(__file__), '..')


def build(path):
    s = io.open(path, encoding='utf-8').read()

    # 1) 既存の id を一旦剥がす（冪等にするため）
    s = re.sub(r'<h([23]) id="sec-[0-9-]+">', r'<h\1>', s)

    # 2) 出現順に id を振りながら toc を組み立てる
    toc, h2i, h3i = [], 0, 0
    out, pos = [], 0
    for m in re.finditer(r'<h([23])>([^<\n]+)</h\1>', s):
        lvl, text = m.group(1), m.group(2).strip()
        if lvl == '2':
            h2i += 1; h3i = 0
            hid = 'sec-%d' % h2i
            toc.append({'id': hid, 'text': text, 'children': []})
        else:
            if not toc:          # h2 より前に h3 がある場合は目次に出さない
                continue
            h3i += 1
            hid = 'sec-%d-%d' % (h2i, h3i)
            toc[-1]['children'].append({'id': hid, 'text': text})
        out.append(s[pos:m.start()])
        out.append('<h%s id="%s">%s</h%s>' % (lvl, hid, text, lvl))
        pos = m.end()
    out.append(s[pos:])
    s = ''.join(out)

    # 3) frontmatter の toc 定義を差し替え（無ければ末尾に追加）
    def esc(t):
        return t.replace('\\', '\\\\').replace("'", "\\'")

    lines = ['const toc = [']
    for item in toc:
        lines.append("  { id: '%s', text: '%s', children: [" % (item['id'], esc(item['text'])))
        for c in item['children']:
            lines.append("    { id: '%s', text: '%s' }," % (c['id'], esc(c['text'])))
        lines.append('  ] },')
    lines.append('];')
    toc_src = '\n'.join(lines)

    if re.search(r'^const toc = \[.*?^\];', s, re.S | re.M):
        s = re.sub(r'^const toc = \[.*?^\];', lambda _: toc_src, s, flags=re.S | re.M)
    else:
        fm = re.match(r'^---\n(.*?)\n---\n', s, re.S)
        if not fm:
            print('NG frontmatter が見つからない: %s' % path); sys.exit(1)
        s = s[:fm.end(1)] + '\n\n' + toc_src + s[fm.end(1):]

    # 4) import を追加
    if "from '../../components/Toc.astro'" not in s:
        s = re.sub(r"(import .*?Layout\.astro';\n)",
                   r"\1import Toc from '../../components/Toc.astro';\n", s, count=1)

    # 5) 最初の h2 の直前に <Toc> を置く（既にあれば何もしない）
    if '<Toc items={toc} />' not in s:
        m = re.search(r'\n([ \t]*)<h2 id="sec-1">', s)
        if not m:
            print('NG h2 が無い: %s' % path); sys.exit(1)
        indent = m.group(1)
        s = s[:m.start()] + '\n' + indent + '<Toc items={toc} />\n' + s[m.start():]

    io.open(path, 'w', encoding='utf-8').write(s)
    print('OK %-24s h2 %d / h3 %d' % (os.path.basename(path), len(toc), sum(len(i['children']) for i in toc)))


for f in FILES:
    build(os.path.join(ROOT, 'src/pages/articles/%s.astro' % f))
