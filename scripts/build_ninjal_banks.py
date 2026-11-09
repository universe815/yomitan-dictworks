"""Build local NINJAL public-web snapshots; never infer missing source entries."""
from pathlib import Path
from collections import Counter, defaultdict
from urllib.parse import quote, urljoin
import json, re, hashlib, zipfile, html as escape
from lxml import html
import fastjsonschema

ROOT = Path(__file__).resolve().parents[1]
for output_dir in ('dictionary-output', 'reports'):
    (ROOT / output_dir).mkdir(parents=True, exist_ok=True)
BASE = 'https://www2.ninjal.ac.jp/'
CSS = '''
[data-sc-ninjal="root"]{line-height:1.85;overflow-wrap:anywhere;color:inherit}
[data-sc-ninjal="single-verb"],[data-sc-ninjal="heading"]{font-size:1.25em;font-weight:bold;margin:.4em 0}
[data-sc-ninjal="sense-block"]{border-top:1px solid #8999aa;padding:.7em 0}
[data-sc-ninjal="sense-number"]{font-weight:bold}
[data-sc-ninjal="headword-example"],[data-sc-ninjal="example"]{border-left:3px solid #819da6;padding-left:.7em;margin:.65em 0}
[data-sc-ninjal="headword"],[data-sc-ninjal="case-marker"]{font-weight:bold}
[data-sc-ninjal="argument-label"]{display:inline-block;background:rgba(120,150,170,.13);padding:.1em .3em;margin:.1em}
[data-sc-ninjal="conj-badge"]{padding:0 .4em;font-size:.9em}
[data-sc-ninjal="conj-row"]{display:flex;gap:1em;border-bottom:1px dotted #aaa}
[data-sc-ninjal="conj-label"]{min-width:7em}
[data-sc-ninjal="cacc"]{display:inline-block;border-top:2px solid #c48ca7;border-right:2px solid #c48ca7}
[data-sc-ninjal="entry-meta"],[data-sc-ninjal="note"]{font-size:.88em;opacity:.85}
[data-sc-ninjal="root"] table{width:100%;border-collapse:collapse}
[data-sc-ninjal="root"] td{vertical-align:top}
[data-sc-ninjal="root"] summary{cursor:pointer;font-weight:bold}
[data-sc-ninjal="root"] details{margin:.4em 0;padding:.3em .5em;background:rgba(120,150,170,.07)}
[data-sc-ninjal="root"] a{color:inherit;text-decoration:underline}
'''

def save(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')

def node(tag, content, marker=None, **kw):
    n = dict(tag=tag, content=content, **kw)
    if marker: n['data'] = {'ninjal':marker}
    return n

def text(n):
    if isinstance(n,str): return n
    if isinstance(n,list): return ''.join(text(x) for x in n)
    return text(n.get('content',[]))

def compact(s): return re.sub(r'\s+','',s)

def convert(e, url=''):
    children = [e.text] if e.text else []
    for c in e:
        if isinstance(c.tag,str) and c.tag not in {'script','style','button','i'}:
            children.append(convert(c,url))
        if c.tail: children.append(c.tail)
    t=e.tag
    mapped={'h1':'div','h2':'div','h3':'div','p':'div','b':'span','strong':'span','sup':'span','em':'span'}.get(t,t)
    assert mapped in {'div','span','ruby','rt','rp','table','tbody','tr','td','th','details','summary','a','br','ul','ol','li'},t
    n=node(mapped,children,(e.get('class','').split() or [None])[0])
    if t in {'b','strong'}: n['style']={'fontWeight':'bold'}
    if t=='sup': n['style']={'verticalAlign':'super','fontSize':'.75em'}
    if t=='em': n['style']={'fontStyle':'italic'}
    if t=='a':
        n.pop('data',None)
        n['href']=urljoin(url,e.get('href',''))
    if t=='br':n.pop('content',None)
    if t in {'td','th'}:
        for attr in ('rowspan','colspan'):
            if e.get(attr): n[{'rowspan':'rowSpan','colspan':'colSpan'}[attr]]=int(e.get(attr))
    return n

def fragment(s):
    e=html.fragment_fromstring(s,create_parent='div')
    n=convert(e)
    assert compact(e.text_content())==compact(text(n))
    return n

def link(label, term): return node('a',label,href='?query='+quote(term))

def walk(n):
    if isinstance(n,dict):
        yield n
        yield from walk(n.get('content',[]))
    elif isinstance(n,list):
        for c in n:yield from walk(c)

def finish(name,title,filename,url,entries,stats,manifest,preview):
    index=dict(title=title,revision='2026.11.09.1',format=3,sequenced=True,sourceLanguage='ja',targetLanguage='ja',url=url,
        author='国立国語研究所／プラシャント・パルデシほか；Yomitan 本地转换',
        description=stats['description'],attribution='原文及署名归原权利人。来源为官网公开网页／JSON，非官方转换；数据仓库许可证尚未核实，仅保存于本地。')
    validators={k:fastjsonschema.compile(json.loads((ROOT/'schemas'/f'dictionary-{v}-schema.json').read_text(encoding='utf-8')),use_default=False) for k,v in {'index':'index','term':'term-bank-v3'}.items()}
    validators['index'](index)
    # Validate the same recursive schema once per distinct node. Validating an
    # entire deeply nested tree through oneOf repeatedly is needlessly costly.
    term_schema=json.loads((ROOT/'schemas/dictionary-term-bank-v3-schema.json').read_text(encoding='utf-8'))
    validate_node=fastjsonschema.compile({'$ref':'#/definitions/structuredContent','definitions':term_schema['definitions']},use_default=False)
    validated_nodes=set()
    def validate_content(c):
        if isinstance(c,str):return
        if isinstance(c,list):
            for child in c:validate_content(child)
            return
        assert isinstance(c,dict),type(c)
        if id(c) in validated_nodes:return
        shallow=dict(c)
        if 'content' in shallow:shallow['content']=''
        validate_node(shallow)
        if 'content' in c:validate_content(c['content'])
        validated_nodes.add(id(c))
    def validate_terms(batch):
        shallow=[]
        for entry in batch:
            for gloss in entry[5]:validate_content(gloss['content'])
            copy=list(entry)
            copy[5]=[{**g,'content':''} for g in entry[5]]
            shallow.append(copy)
        validators['term'](shallow)
    terms={e[0] for e in entries}
    seen=set()
    for e in entries:
        assert (e[0],e[1],e[6]) not in seen
        seen.add((e[0],e[1],e[6]))
        for n in walk(e[5]):
            if n.get('href','').startswith('?query='):
                from urllib.parse import unquote
                assert unquote(n['href'][7:]) in terms
    out=ROOT/'dictionary-output'/filename
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        def put(key,value):
            if not isinstance(value,str):value=json.dumps(value,ensure_ascii=False,separators=(',',':'))
            info=zipfile.ZipInfo(key,(2026,11,9,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,value.encode('utf-8'))
        put('index.json',index);put('styles.css',CSS)
        for offset in range(0,len(entries),100):
            batch=entries[offset:offset+100];validate_terms(batch)
            put(f'term_bank_{offset//100+1}.json',batch)
    with zipfile.ZipFile(out) as z:
        assert z.testzip() is None
        actual=[e for k in z.namelist() if k.startswith('term_bank_') for e in json.loads(z.read(k))]
        assert actual==entries
    stats.update(title=title,search_records=len(entries),unique_search_terms=len(terms),official_schema_valid=True,archive_crc_valid=True,
        internal_links_resolve=True,browser_import_tested=False,zip_bytes=out.stat().st_size,zip_sha256=hashlib.sha256(out.read_bytes()).hexdigest())
    save(ROOT/'reports'/f'{name}-qa.json',stats)
    save(ROOT/'reports'/f'{name}-source-manifest.json',manifest)
    def render(n):
        if isinstance(n,str):return escape.escape(n)
        if isinstance(n,list):return ''.join(map(render,n))
        t=n['tag']; attrs=''
        if n.get('data'):attrs+=' data-sc-ninjal="'+escape.escape(n['data']['ninjal'])+'"'
        if n.get('href'):attrs+=' href="'+escape.escape(n['href'])+'"'
        if n.get('style'):attrs+=' style="'+';'.join(re.sub('[A-Z]',lambda m:'-'+m[0].lower(),k)+':'+str(v) for k,v in n['style'].items())+'"'
        return '<'+t+attrs+'>'+render(n.get('content',[]))+('' if t=='br' else '</'+t+'>')
    doc='<!doctype html><html lang="ja"><meta charset="utf-8"><title>'+title+'</title><style>'+CSS+'body{font-family:Meiryo,sans-serif;margin:24px;background:#eee}main{display:grid;grid-template-columns:1fr 1fr;gap:20px}.pane{min-width:0;padding:20px;background:white}.dark{background:#202327;color:#e4e7eb}article{margin-bottom:30px}</style><main>'
    for dark in (False,True):
        doc+='<section class="pane '+('dark' if dark else '')+'">'+''.join('<article>'+render(n)+'</article>' for n in preview)+'</section>'
    (ROOT/'reports'/f'{name}-preview.html').write_text(doc+'</main></html>',encoding='utf-8')
    print(json.dumps(stats,ensure_ascii=False),flush=True)

def source_record(p,url):
    b=p.read_bytes()
    return dict(file=str(p.relative_to(ROOT)),url=url,bytes=len(b),sha256=hashlib.sha256(b).hexdigest())

def verbs():
    source=ROOT/'sources/ninjal-verb-headwords.js'
    data=json.loads(re.sub(r';\s*$','',re.sub(r'^var single_verb_headwords\s*=\s*','',source.read_text(encoding='utf-8'))))
    heads=[e for group in data.values() for e in group]
    stats=Counter();entries=[];manifest=[source_record(source,BASE+'basicverbbank/js/single_verb_headwords.js')];preview=[]
    for seq,h in enumerate(heads,1):
        p=ROOT/'sources/ninjal-verbs'/(h['headword_key']+'.html')
        url=BASE+'basicverbbank/single_headwords/'+quote(h['headword_key'])+'.html'
        doc=html.parse(str(p)).xpath('//div[@class="content headword single"]')
        assert len(doc)==1,h
        d=doc[0]
        for c in d.xpath('.//script|.//style|.//button|.//i'):c.drop_tree()
        n=convert(d,url);n['data']={'ninjal':'root'}
        assert compact(d.text_content())==compact(text(n)),h
        n['content'].append(node('div',node('a','出典：日本語基本動詞バンク',href=url),'note'))
        stats['senses']+=len(d.xpath('.//div[@class="sense-block"]'))
        stats['examples']+=len(d.xpath('.//div[@class="headword-example"]'))
        stats['ruby']+=len(d.xpath('.//ruby'))
        stats['conjugation_tables']+=len(d.xpath('.//details[@class="conjugation"]'))
        hd=html.fragment_fromstring(h['headword'],create_parent='span')
        for c in hd.xpath('.//sup|.//rt|.//rp'):c.drop_tree()
        aliases={a.strip() for a in hd.text_content().split('・')}|{h['reading']}
        badges=d.xpath('.//span[@class="conj-badge"]/text()')
        rule='v5' if '1グループ' in badges else 'v1' if '2グループ' in badges else ''
        if '3グループ' in badges:
            if h['reading'].endswith('する'):rule='vs'
            elif h['reading']=='くる':rule='vk'
        for a in sorted(aliases):
            if a:entries.append([a,h['reading'],'',rule,0,[{'type':'structured-content','content':n}],seq,''])
        manifest.append(source_record(p,url))
        if h['reading'] in {'あいつぐ','あう','たべる'}:preview.append(n)
    stats=dict(stats,source_headword_pages=len(heads),all_indexed_pages_preserved=True,all_body_text_preserved=True,
        description='官网词条网页快照，754 个索引词头；保留释义、振假名、格结构、例句和活用表。官网介绍称 800 基本动词，本次公开索引实际为 754 项；不等同于仓库原始数据完整导出。自他动词对照保留官网链接；音频不包含。')
    finish('ninjal-verbs','日本語基本動詞バンク〔NINJAL・网页快照〕','日本語基本動詞バンク-NINJAL-Yomitan.zip',BASE+'basicverbbank/',entries,stats,manifest,preview[:3])

def cases():
    surfaces=dict(ga='が',wo='を',ni='に',he='へ',de='で',kara='から',made='まで',yori='より',to='と')
    entries=[];manifest=[];stats=Counter();mismatches=[];seq=0;preview=[]
    for stem,surface in surfaces.items():
        folder=stem+'-kaku';p=ROOT/'sources/ninjal-cases'/(folder+'_summary.json')
        summary=json.loads(p.read_text(encoding='utf-8'));particle=summary['particle']
        manifest.append(source_record(p,BASE+'caseparticlebank/thematic_roles/'+p.name))
        overview=[node('div',f'{surface}【{particle}】','heading')]
        total=0
        for role in summary['roles']:
            label=role['role'];term=surface+'〈'+label+'〉'
            rp=p.parent/folder/(label+'.json');examples=json.loads(rp.read_text(encoding='utf-8'))
            manifest.append(source_record(rp,BASE+'caseparticlebank/thematic_roles/'+folder+'/'+quote(label)+'.json?v=20261022f'))
            total+=len(examples);stats['example_instances']+=len(examples);stats['role_groups']+=1
            if len(examples)!=role['total_count']:mismatches.append(dict(particle=particle,role=label,summary=role['total_count'],actual=len(examples)))
            content=[node('div',term,'heading'),node('div',f'{len(examples)} 用例。典型的＝項／周辺的＝付加詞。','note')]
            groups=defaultdict(list)
            for ex in examples:groups[(ex['verb']['kanji_choice'],ex['verb']['reading'],ex.get('definition',''))].append(ex)
            for (word,reading,definition),xs in groups.items():
                body=[node('summary',f'{word}（{reading}） — {len(xs)} 例'),fragment(xs[0].get('definition_with_ruby') or definition)]
                for ex in xs:
                    en=fragment(ex.get('example_with_ruby') or ex['example'])
                    bare=html.fragment_fromstring(ex.get('example_with_ruby') or ex['example'],create_parent='div')
                    for rt in bare.xpath('.//rt|.//rp'):rt.drop_tree()
                    plain_source=html.fragment_fromstring(ex['example'],create_parent='div').text_content()
                    if compact(bare.text_content())!=compact(plain_source):
                        mismatches.append(dict(particle=particle,role=label,type='source_ruby_plain_mismatch',example=ex['example']))
                        en=node('div',[en,node('div',["原文（ルビなし）：",fragment(ex['example'])])])
                    en['data']={'ninjal':'example'}
                    annotations=[f"{a.get('text','')}：{a.get('type','')}／{a.get('thematicRole','')}"+('（典型的）' if a.get('argument') else '（周辺的）') for a in ex.get('annotation',[]) if a.get('thematicRole')]
                    en['content'].append(node('div','典型的' if ex.get('role_type')=='argument' else '周辺的' if ex.get('role_type')=='adjunct' else ex.get('role_type',''),'note'))
                    en['content'].append(node('details',[node('summary','格と意味役割'),*[node('div',v) for v in annotations]]))
                    if ex.get('annotation_comments'):en['content'].append(node('div',ex['annotation_comments'],'note'))
                    body.append(en)
                content.append(node('details',body))
            url=BASE+'caseparticlebank/particle_search/result/?case-particle='+quote(particle)+'&thematic-role='+quote(label)
            content.append(node('a','出典：格助詞バンク',href=url))
            n=node('div',content,'root');seq+=1
            for a in sorted({term,particle+'〈'+label+'〉'}):entries.append([a,'','','',0,[{'type':'structured-content','content':n}],seq,''])
            item=[link(label+' — '+str(len(examples))+' 例',term)]
            if examples:item.append(fragment(examples[0].get('example_with_ruby') or examples[0]['example']))
            overview.append(node('div',item,'example'))
        if total!=summary['total_examples']:mismatches.append(dict(particle=particle,summary_total=summary['total_examples'],actual_total=total))
        overview.insert(1,node('div',f'{len(summary["roles"])} 意味役割／{total} 用例。各見出しをクリックして全用例を表示。','note'))
        n=node('div',overview,'root');seq+=1
        for a in {surface,'〜'+surface,particle}:entries.append([a,surface,'','',0,[{'type':'structured-content','content':n}],seq,''])
        if surface in {'に','で'}:preview.append(n)
    stats=dict(stats,particles=9,all_indexed_role_files_preserved=True,all_example_instances_preserved=True,source_discrepancies=len(mismatches),
        description='官网公开 JSON 快照。9 个格助词的概览及 95 个语义角色组，保留分组文件的全部例句、振假名、释义、典型／周边类型与格标注。概览链接到完整用例；动词分组可折叠。不是仓库原始数据全集；网站 WLSP 自动分类等内部字段仅保存在源 JSON。')
    save(ROOT/'reports/ninjal-cases-source-issues.json',mismatches)
    finish('ninjal-cases','日本語格助詞バンク〔NINJAL・用例版〕','日本語格助詞バンク-NINJAL-Yomitan.zip',BASE+'caseparticlebank/',entries,stats,manifest,preview)

if __name__=='__main__':
    import sys
    for name in sys.argv[1:] or ['verbs','cases']:{'verbs':verbs,'cases':cases}[name]()
