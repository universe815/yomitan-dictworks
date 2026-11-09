"""Convert the 2026-04-19 adjective MDX without rewriting source prose.

Requires mdict-utils, lxml and fastjsonschema. Run from any directory.
"""
from __future__ import annotations

import argparse
import hashlib
import html as html_std
import json
import re
import unicodedata
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import quote, unquote

import fastjsonschema
from lxml import html
from mdict_utils.base.readmdict import MDX

ROOT = Path(__file__).resolve().parents[1]
for output_dir in ('dictionary-output', 'reports'):
    (ROOT / output_dir).mkdir(parents=True, exist_ok=True)
TITLE = '现代日语形容词用法词典（中文版）'
REVISION = '2026.11.09.1'
SOURCE_URL = 'https://forum.freemdict.com/t/topic/43714'
CSS = '''
[data-sc-madj="entry"] { line-height:1.75; color:inherit; overflow-wrap:anywhere; }
[data-sc-madj="hw_header"] { font-size:1.2em; font-weight:700; border-bottom:2px solid #408080; padding-bottom:.3em; margin-bottom:.6em; }
[data-sc-madj="hw_kanji"] { opacity:.8; font-size:.9em; }
[data-sc-madj="definition"] { margin:.5em 0; font-weight:600; }
[data-sc-madj="examples_section"] { border-left:3px solid #829d9d; padding-left:.75em; margin:.65em 0; }
[data-sc-madj="example_item"] { margin:.5em 0; }
[data-sc-madj="cn"] { display:block; color:var(--madj-translation,#24558a); margin-left:1.2em; }
[data-sc-madj="item_id"], [data-sc-madj="group_id"] { font-weight:700; margin-right:.35em; }
[data-sc-madj="section"] { margin:.8em 0; }
[data-sc-madj="section_title"] { display:block; font-weight:700; border-bottom:1px solid #829d9d; padding-bottom:.2em; }
[data-sc-madj="paragraph"] { margin:.4em 0; }
[data-sc-madj="comparison"] { border-left:3px solid #829d9d; margin:.5em 0; padding:.3em .7em; background:rgba(100,150,150,.09); }
[data-sc-madj="references"] { border-top:1px dashed #829d9d; margin-top:.8em; padding-top:.4em; }
[data-sc-madj="entry"] a { color:var(--madj-translation,#24558a); text-decoration:underline; }
[data-sc-madj="page_num"] { text-align:right; opacity:.65; font-size:.8em; margin-top:.6em; }
[data-sc-madj="emphasis"] { font-weight:700; color:inherit; }
[data-sc-madj="underline"] { text-decoration:underline; text-underline-offset:.2em; }
[data-sc-madj="unresolved"] { text-decoration:underline dotted; opacity:.8; }
[data-sc-madj="entry"] rt { font-size:.55em; }
@media (prefers-color-scheme:dark) { [data-sc-madj="entry"] { --madj-translation:#82bfff; } }
:root[data-theme="dark"] [data-sc-madj="entry"], [data-theme="dark"] [data-sc-madj="entry"] { --madj-translation:#82bfff; }
'''

def plain(value):
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return ''.join(map(plain, value))
    if isinstance(value, dict):
        return plain(value.get('content', ''))
    return ''

def compact(value):
    return re.sub(r'\s+', '', value)

def normalized(value):
    value = unicodedata.normalize('NFKC', unquote(value)).strip().rstrip('。．.')
    return re.sub(r'^[~〜～]+', '', value).strip()

def kana_reading(value):
    value = re.sub(r'[ⅠⅡI]+$', '', normalized(value))
    value = ''.join(chr(ord(c)-96) if 'ァ' <= c <= 'ヶ' else c for c in value)
    return value if re.fullmatch(r'[ぁ-ゖー]+', value) else ''

def walk(value):
    if isinstance(value, dict):
        yield value
        yield from walk(value.get('content'))
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)

def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, default=ROOT/'sources/modern-adjective.mdx')
    args = parser.parse_args()
    mdx = MDX(str(args.source))
    source_rows = [(k.decode('utf-8'), v.decode('utf-8')) for k,v in mdx.items()]
    bodies, redirects = {}, defaultdict(set)
    redirect_count = 0
    for key, value in source_rows:
        if value.strip().startswith('@@@LINK='):
            redirects[key].add(value.strip()[8:])
            redirect_count += 1
        else:
            assert key not in bodies, f'Duplicate body: {key}'
            bodies[key] = html.fromstring(value).xpath('//*[@class="entry"]')[0]
    aliases = defaultdict(set)
    def resolve(target, seen):
        if target in bodies:
            return {target}
        assert target not in seen, f'Redirect cycle: {target}'
        assert target in redirects, f'Missing redirect body: {target}'
        return set().union(*(resolve(t,seen|{target}) for t in redirects[target]))
    for alias, destinations in redirects.items():
        for target in destinations:
            for body_key in resolve(target,{alias}):
                aliases[body_key].add(alias)

    readings = {}
    for key, doc in bodies.items():
        reading = ''.join(doc.xpath('.//*[@class="hw_reading"]/text()'))
        readings[key] = [kana_reading(s) for s in reading.split('・') if kana_reading(s)]
        aliases[key].add(key)
        for text in [reading, ''.join(doc.xpath('.//*[@class="hw_kanji"]/text()')).strip('【】')]:
            for part in text.split('・'):
                if part.strip():
                    aliases[key].add(part.strip())
                    aliases[key].add(normalized(part))
        for r in readings[key]:
            aliases[key].add(r)
    known = {a for values in aliases.values() for a in values if a}
    normalized_lookup = defaultdict(set)
    for word in known:
        normalized_lookup[normalized(word)].add(word)
    # Prefer a normalized searchable form; otherwise retain the original headword.
    targets = {n: n if n in words else sorted(words)[0] for n,words in normalized_lookup.items()}
    unresolved, normalized_links = [], []
    stats = Counter()

    def convert(element, source_key):
        tag = element.tag
        assert isinstance(tag,str)
        children = []
        if element.text:
            children.append(element.text)
        for child in element:
            node = convert(child, source_key)
            if node is not None:
                children.append(node)
            if child.tail:
                children.append(child.tail)
        if tag == 'br':
            return {'tag':'br'}
        if tag in {'link','script','style'}:
            return None
        if tag == 'a':
            href = element.get('href','')
            assert href.startswith('entry://'), href
            original = unquote(href[8:])
            target = targets.get(normalized(original))
            if target:
                stats['resolved_links'] += 1
                if target != original:
                    normalized_links.append({'entry':source_key,'original':original,'target':target})
                return {'tag':'a','href':'?query='+quote(target,safe=''),'content':children}
            unresolved.append({'entry':source_key,'target':original,'label':plain(children)})
            return {'tag':'span','data':{'madj':'unresolved'},'title':'原始参照在本源文件中未找到对应词条，保留原文。','content':children}
        allowed = {'div','span','p','b','u','ruby','rt'}
        assert tag in allowed, f'Unhandled HTML tag: {tag}'
        out_tag = {'p':'div','b':'span','u':'span'}.get(tag,tag)
        marker = element.get('class','').split()
        marker = 'comparison' if 'comparison' in marker else marker[0] if marker else {'p':'paragraph','b':'emphasis','u':'underline'}.get(tag,'')
        node = {'tag':out_tag,'content':children}
        if marker:
            node['data'] = {'madj':marker}
        if marker in {'cn','definition','section_content'}:
            node['lang'] = 'zh'
        elif marker in {'ja','hw_reading','hw_kanji'} or tag in {'ruby','rt'}:
            node['lang'] = 'ja'
        # Structural fallbacks remain legible when a reader ignores styles.css.
        if marker == 'cn':
            node['tag'] = 'div'
        if tag == 'b':
            node['style'] = {'fontWeight':'bold'}
        if tag == 'u':
            node['style'] = {'textDecorationLine':'underline'}
        stats['node_'+out_tag] += 1
        return node

    entries, sequence_map, source_metrics = [], {}, Counter()
    for sequence, (key,doc) in enumerate(bodies.items(),1):
        content = convert(doc,key)
        assert compact(''.join(doc.itertext())) == compact(plain(content)), f'Text loss in {key}'
        sequence_map[key] = sequence
        source_metrics['bodies'] += 1
        source_metrics['japanese_examples'] += len(doc.xpath('.//*[@class="ja"]'))
        source_metrics['chinese_examples'] += len(doc.xpath('.//*[@class="cn"]'))
        source_metrics['ruby'] += len(doc.xpath('.//ruby'))
        source_metrics['source_links'] += len(doc.xpath('.//a'))
        source_metrics['comparison_blocks'] += len(doc.xpath('.//*[contains(@class,"comparison")]'))
        for alias in sorted(aliases[key]):
            if not alias:
                continue
            reading = kana_reading(alias)
            if not reading and len(set(readings[key])) == 1:
                reading = readings[key][0]
            # Source has no reliable per-headword POS annotation: do not invent rules.
            entries.append([alias,reading,'用法 OCR','',0,[{'type':'structured-content','content':content}],sequence,''])

    index = {'title':TITLE,'revision':REVISION,'format':3,'sequenced':True,
             'author':'原书作者及译者；MDX 整理：wynick27；Yomitan 本地转换',
             'url':SOURCE_URL,'sourceLanguage':'ja','targetLanguage':'zh',
             'description':'2026.04.19 MDX 转换；1009 篇正文，保留释义、例句、用法辨析、注音和页码。原数据来自 OCR，未经全书人工校订；未能可靠对应的参照保留为文字。',
             'attribution':'第三方原书及译本内容的权利归原权利人。源 MDX 制作者：wynick27。转换未新增或改写释义；本地构建，未配置公开更新。'}
    tags = [['用法','dictionary',0,'形容词及相关表达用法',0],['OCR','source',1,'源数据经 OCR 和一次校对，可能残留文字错误',0]]
    schema_names = {'index':'dictionary-index-schema.json','term':'dictionary-term-bank-v3-schema.json','tag':'dictionary-tag-bank-v3-schema.json'}
    validators = {k:fastjsonschema.compile(json.loads((ROOT/'schemas'/n).read_text(encoding='utf-8'))) for k,n in schema_names.items()}
    validators['index'](index)
    validators['tag'](tags)
    out = ROOT/'dictionary-output/现代日语形容词用法词典-Yomitan.zip'
    out.parent.mkdir(exist_ok=True)
    def write(z,name,value):
        data = value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,separators=(',',':'))
        info = zipfile.ZipInfo(name,date_time=(2026,11,9,0,0,0))
        info.compress_type = zipfile.ZIP_DEFLATED
        z.writestr(info,data.encode('utf-8'))
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        write(z,'index.json',index)
        write(z,'tag_bank_1.json',tags)
        write(z,'styles.css',CSS)
        for offset in range(0,len(entries),500):
            bank = entries[offset:offset+500]
            validators['term'](bank)
            write(z,f'term_bank_{offset//500+1}.json',bank)

    # Independent readback from the delivered archive.
    with zipfile.ZipFile(out) as z:
        assert z.testzip() is None
        final = [e for n in z.namelist() if n.startswith('term_bank_') for e in json.loads(z.read(n))]
    actual_terms = {e[0] for e in final}
    assert len(final) == len(entries)
    assert {e[6] for e in final} == set(sequence_map.values())
    assert set(k for k,v in source_rows) <= actual_terms
    assert len({(e[0],e[1],e[6]) for e in final}) == len(final)
    actual_sequences = defaultdict(set)
    for entry in final:
        actual_sequences[entry[0]].add(entry[6])
    for alias, destinations in redirects.items():
        expected = {sequence_map[k] for target in destinations for k in resolve(target,{alias})}
        assert expected <= actual_sequences[alias], f'Lost redirect meaning: {alias}'
    final_by_sequence = {e[6]: e[5][0]['content'] for e in final}
    for key,sequence in sequence_map.items():
        assert compact(''.join(bodies[key].itertext())) == compact(plain(final_by_sequence[sequence]))
    for content in final_by_sequence.values():
        for node in walk(content):
            if node.get('tag')=='a':
                assert unquote(node['href'].split('?query=',1)[1]) in actual_terms
    for term in ['相容れない','あいいれない','あつい','厚い','熱い','大きい','あかぬけた','あかぬけした','気持ち良い']:
        assert term in actual_terms,term
    assert len({e[6] for e in final if e[0]=='あつい'}) == 2
    issues = {'unresolved_references':unresolved,'normalized_link_targets':normalized_links,
              'examples_without_chinese_translation':[k for k,d in bodies.items() if len(d.xpath('.//*[@class="ja"]'))!=len(d.xpath('.//*[@class="cn"]'))],
              'notes':['源文件未提供可靠逐词词性，rules 字段留空；未验证独立词典的活用还原。','未推测修正 OCR 错字或断裂参照，正文逐字保留（忽略排版空白）。','多读音条目的汉字别名未猜配读音；无法确定时 reading 留空。']}
    report = {'title':TITLE,'revision':REVISION,'source_url':SOURCE_URL,
              'source_sha256':hashlib.sha256(args.source.read_bytes()).hexdigest(),
              'source_records':len(source_rows),'source_redirects':redirect_count,**source_metrics,
              'search_records':len(final),'unique_search_terms':len(actual_terms),
              'resolved_links':stats['resolved_links'],'unresolved_references':len(unresolved),
              'normalized_link_targets':len(normalized_links),'official_schema_valid':True,
              'all_source_keys_preserved':True,'all_redirect_destinations_preserved':True,'all_body_text_preserved':True,
              'archive_crc_valid':True,'all_clickable_links_resolve':True,
              'browser_import_tested':False,'zip_bytes':out.stat().st_size,
              'zip_sha256':hashlib.sha256(out.read_bytes()).hexdigest()}
    write_json(ROOT/'reports/modern-adjective-qa.json',report)
    write_json(ROOT/'reports/modern-adjective-source-issues.json',issues)
    # A static preview uses exactly the structured content emitted to the ZIP.
    def render(value):
        if isinstance(value,str):return html_std.escape(value)
        if isinstance(value,list):return ''.join(map(render,value))
        tag=value['tag'];attrs=''
        if value.get('data'):attrs+=' data-sc-madj="'+html_std.escape(value['data']['madj'])+'"'
        if value.get('title'):attrs+=' title="'+html_std.escape(value['title'])+'"'
        if value.get('href'):attrs+=' href="'+html_std.escape(value['href'])+'"'
        return '<'+tag+attrs+'>'+render(value.get('content',[]))+('' if tag=='br' else '</'+tag+'>')
    selected = ['あいいれない【相容れない】','あついⅠ【厚い・篤い】','あついⅡ【熱い・暑い】','きはずかしい【気恥ずかしい】']
    preview = '<!doctype html><html lang="zh"><meta charset="utf-8"><title>形容词词典预览</title><style>'+CSS+'body{font-family:Meiryo,Microsoft YaHei,sans-serif;margin:24px;background:#eee}main{display:grid;grid-template-columns:1fr 1fr;gap:24px}.pane{padding:24px;background:white}.dark{background:#202327;color:#e4e7eb;--madj-translation:#82bfff}article{border-bottom:1px solid #888;padding-bottom:24px;margin-bottom:24px}</style><main>'
    for dark in [False,True]:
        preview += '<section class="pane '+('dark' if dark else '')+'">'
        for k in selected:preview+='<article>'+render(final_by_sequence[sequence_map[k]])+'</article>'
        preview+='</section>'
    preview+='</main></html>'
    (ROOT/'reports/modern-adjective-preview.html').write_text(preview,encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
