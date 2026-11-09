"""Build two local Yomitan dictionaries, preserving source text and alias multiplicity."""
from __future__ import annotations
import argparse, base64, hashlib, html as html_std, json, re, zipfile
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import quote, unquote
import fastjsonschema
from lxml import html
from mdict_utils.base.readmdict import MDX, MDD
from build_modern_adjective import compact, plain, walk, kana_reading

ROOT = Path(__file__).resolve().parents[1]
for output_dir in ('dictionary-output', 'reports'):
    (ROOT / output_dir).mkdir(parents=True, exist_ok=True)
CONFIG = {
 'ruigigo': dict(title='研究社 類義語使い分け辞典', file='研究社-類義語使い分け辞典-Yomitan.zip', language='ja', url='https://forum.freemdict.com/t/topic/43916', tag='辨析', description='585 组辨析正文和 5 篇前言等资料；保留源 MDX 全部词头、多义跳转、正文和 5 张图表。EPWING 转换源；上游曾用 AI 重排版，未对原书逐页校订。'),
 'nichibei': dict(title='最新日米口語辞典［決定版］（文字预览版）', file='最新日米口語辞典-決定版-文字预览-Yomitan.zip', language='en', url='https://forum.freemdict.com/t/topic/44009/6', tag='口语', description='源 MDX 的 3328 篇词条正文及 9 篇附录资料。文字预览：源文件有指向缺失正文的索引，详见配套报告；保留全部现有正文，不补造缺词。原音频仅保存为独立源文件，本 ZIP 不支持播放音频。'),
}
CSS = '''
[data-sc-extra="entry"]{line-height:1.75;color:inherit;overflow-wrap:anywhere}
[data-sc-extra="header"],[data-sc-extra="head"]{border-bottom:2px solid #728e9c;padding-bottom:.4em;margin-bottom:.7em}
[data-sc-extra="main-words"]{font-size:1.2em;font-weight:bold}
[data-sc-extra="word"]{display:inline-block;margin-right:.2em}
[data-sc-extra="kana"]{font-size:.8em;opacity:.75;margin-left:.25em}
[data-sc-extra="assoc-words"]{margin-top:.4em;font-size:.92em;opacity:.9}
[data-sc-extra="exp-item"]{border-left:3px solid #648c9c;padding-left:.65em;margin:.5em 0}
[data-sc-extra="exp-word"]{font-weight:bold;margin-right:.6em}
[data-sc-extra="content-section"]{margin:.9em 0;padding:.5em .8em;background:rgba(120,145,170,.10);border-left:2px solid #8996a5}
[data-sc-extra="section-label"]{font-weight:bold;margin-bottom:.3em;border-bottom:1px dotted #8996a5}
[data-sc-extra="paragraph"],[data-sc-extra="paragraph-default"]{margin:.4em 0}
[data-sc-extra="underline"]{text-decoration:underline;font-weight:bold}
[data-sc-extra="heading"]{font-size:1.25em;font-weight:bold;margin-bottom:.6em}
[data-sc-extra="headword_kana"]{font-size:1.15em;font-weight:bold}
[data-sc-extra="headword_kanji"]{margin-left:.3em}
[data-sc-extra="headword_eng"]{display:block;margin-top:.3em;color:var(--extra-accent,#225f8c);font-weight:600}
[data-sc-extra="example"]{border-left:3px solid #829d9d;padding-left:.75em;margin:.8em 0}
[data-sc-extra="example_jp"]{font-weight:600}
[data-sc-extra="example_en"]{display:block;color:var(--extra-accent,#225f8c);margin:.3em 0}
[data-sc-extra="unresolved"]{text-decoration:underline dotted;opacity:.8}
[data-sc-extra="entry"] a{color:var(--extra-accent,#225f8c);text-decoration:underline}
[data-sc-extra="entry"] table{border-collapse:collapse;max-width:100%}
[data-sc-extra="entry"] td{padding:.1em .5em;vertical-align:top}
[data-sc-extra="entry"] img{max-width:100%;height:auto;background:white}
@media(prefers-color-scheme:dark){[data-sc-extra="entry"]{--extra-accent:#90c9f1}}
[data-theme="dark"] [data-sc-extra="entry"]{--extra-accent:#90c9f1}
'''

def save(path, value):
 path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')

def build(name):
 cfg=CONFIG[name]; source=ROOT/'sources'/f'{name}.mdx'
 rows=[(k.decode('utf-8'),v.decode('utf-8')) for k,v in MDX(str(source)).items()]
 bodies={}; redirects=defaultdict(set); aliases=defaultdict(set); reading_map=defaultdict(set)
 issues={'unresolved_redirects':[], 'unresolved_links':[], 'notes':[]}; stats=Counter()
 for k,v in rows:
  if v.strip().startswith('@@@LINK='): redirects[k].add(v.strip()[8:])
  else:
   assert k not in bodies
   bodies[k]=html.fragment_fromstring(v,create_parent='div')
 # Numeric source IDs are usable only when an actual body contains that ID.
 ids=defaultdict(set)
 for k,d in bodies.items():
  for e in d.xpath('.//*[@id]'): ids[e.get('id')].add(k)
 def resolve(k, seen=frozenset()):
  k=unquote(k).rstrip('#')
  if k in seen:return set()
  result=set(ids.get(k,()))
  if k in bodies: result.add(k)
  for target in redirects.get(k,()): result.update(resolve(target,seen|{k}))
  return result
 for a,targets in redirects.items():
  for target in targets:
   found=resolve(target)
   if not found:issues['unresolved_redirects'].append({'alias':a,'target':target})
   for k in found:aliases[k].add(a)
 for k,d in bodies.items():
  aliases[k].add(k)
  for ident, destinations in ids.items():
   if k in destinations:aliases[k].add(ident)
  if name=='ruigigo':
   for e in d.xpath('.//span[@class="word"]'):
    words=e.xpath('./span[@class="kanji"]/text()'); kana=e.xpath('./span[@class="kana"]/text()')
    for word in words:
     aliases[k].add(word.strip())
     if len(kana)==1:
      r=kana_reading(kana[0]); aliases[k].add(kana[0].strip())
      if r:reading_map[(k,word.strip())].add(r)
  else:
   kana=''.join(d.xpath('.//span[@class="headword_kana"]/text()')).strip()
   kanji=''.join(d.xpath('.//span[@class="headword_kanji"]/text()')).strip('［］')
   if kana:aliases[k].add(kana)
   if kanji:
    aliases[k].add(kanji)
    # Parenthesized optional suffixes get both literal and expanded lookups.
    if re.search('（[^（）]+）',kanji):
     aliases[k].add(re.sub('（[^（）]+）','',kanji))
     aliases[k].add(kanji.replace('（','').replace('）',''))
   if kana_reading(kana):
    for a in aliases[k]:reading_map[(k,a)].add(kana_reading(kana))
   for title in d.xpath('.//div[@class="midashi_info_appendix"]/text()'):aliases[k].add(title.strip())
 known={a for al in aliases.values() for a in al if a}; media={}
 if name=='ruigigo':
  media={k.decode().lstrip('\\/'):v for k,v in MDD(str(ROOT/'sources/ruigigo.mdd')).items()}
 def convert(e, key):
  tag=e.tag
  if not isinstance(tag,str):return None
  if tag in {'link','script','style'}:return None
  if tag=='img':
   src=e.get('src','').lstrip('\\/')
   if name=='nichibei' and src=='sound.png':return None
   assert src in media,src
   stats['image_references']+=1
   return {'tag':'img','path':'media/'+src,'width':450,'sizeUnits':'px','background':True,'collapsed':False,'collapsible':True}
  children=[]
  if e.text:children.append(e.text)
  for child in e:
   c=convert(child,key)
   if c is not None:children.append(c)
   if child.tail:children.append(child.tail)
  if tag=='br':return {'tag':'br'}
  if tag=='a':
   href=e.get('href','')
   if href.startswith('sound://'):
    stats['audio_links_not_embedded']+=1
    return children
   assert href.startswith('entry://'),href
   target=unquote(href[8:]).rstrip('#'); destinations=resolve(target)
   if destinations:
    if target not in known:target=sorted(destinations)[0]
    stats['resolved_links']+=1
    return {'tag':'a','href':'?query='+quote(target,safe=''),'content':children}
   issues['unresolved_links'].append({'entry':key,'target':target,'label':plain(children)})
   return {'tag':'span','data':{'extra':'unresolved'},'title':'原始 MDX 中缺少对应正文，保留参照文字。','content':children}
  allowed={'div','span','p','u','h1','i','sub','table','tr','td','ruby','rt','rp','hr'}
  assert tag in allowed,tag
  out={'p':'div','u':'span','h1':'div','i':'span','sub':'span','hr':'div'}.get(tag,tag)
  cls=e.get('class','').split(); marker=cls[0] if cls else {'p':'paragraph-default','h1':'heading','u':'underline'}.get(tag,'')
  node={'tag':out,'content':children}
  if marker:node['data']={'extra':marker}
  if tag=='u':node['style']={'textDecorationLine':'underline','fontWeight':'bold'}
  if tag=='i':node['style']={'fontStyle':'italic'}
  if tag=='sub':node['style']={'fontSize':'0.8em','verticalAlign':'sub'}
  if marker in {'headword_eng','example_en'}:node['lang']='en'
  return node
 sequences={k:i for i,k in enumerate(bodies,1)}; contents={}; entries=[]
 for k,d in bodies.items():
  content=convert(d,k);content['data']={'extra':'entry'}
  assert compact(d.text_content())==compact(plain(content)),f'Text mismatch: {k}'
  contents[k]=content
  for a in sorted(aliases[k]):
   if not a:continue
   rd=kana_reading(a); candidates=reading_map[(k,a)]
   if not rd and len(candidates)==1:rd=next(iter(candidates))
   entries.append([a,rd,cfg['tag'],'',0,[{'type':'structured-content','content':content}],sequences[k],''])
 index={'title':cfg['title'],'revision':'2026.11.09.1','format':3,'sequenced':True,'sourceLanguage':'ja','targetLanguage':cfg['language'],'url':cfg['url'],'author':'原书作者；MDX：wynick27；日米修复源：epistularum；Yomitan 本地转换','description':cfg['description'],'attribution':'原书权利归原权利人；保留来源正文，仅本地转换，未配置公开更新。'}
 if name=='ruigigo':index['author']='原书作者：田忠魁、泉原省二、金相順；MDX：wynick27；Yomitan 本地转换'
 tags=[[cfg['tag'],'dictionary',0,cfg['description'],0]]
 validators={key:fastjsonschema.compile(json.loads((ROOT/'schemas'/fn).read_text(encoding='utf-8'))) for key,fn in {'index':'dictionary-index-schema.json','tag':'dictionary-tag-bank-v3-schema.json','term':'dictionary-term-bank-v3-schema.json'}.items()}
 validators['index'](index);validators['tag'](tags)
 out=ROOT/'dictionary-output'/cfg['file']
 def put(z,n,v):
  if not isinstance(v,(str,bytes)):v=json.dumps(v,ensure_ascii=False,separators=(',',':'))
  if isinstance(v,str):v=v.encode('utf-8')
  info=zipfile.ZipInfo(n,date_time=(2026,11,9,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,v)
 with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED) as z:
  put(z,'index.json',index);put(z,'tag_bank_1.json',tags);put(z,'styles.css',CSS)
  for offset in range(0,len(entries),250):
   batch=entries[offset:offset+250];validators['term'](batch);put(z,f'term_bank_{offset//250+1}.json',batch)
  for n,data in media.items():put(z,'media/'+n,data)
 with zipfile.ZipFile(out) as z:
  assert z.testzip() is None
  actual=[e for n in z.namelist() if n.startswith('term_bank_') for e in json.loads(z.read(n))]
  actual_terms={e[0] for e in actual}; actual_by_seq={e[6]:e[5][0]['content'] for e in actual}
  seqs_by_alias=defaultdict(set)
  for e in actual:seqs_by_alias[e[0]].add(e[6])
  assert len(actual)==len(entries)==len({(e[0],e[1],e[6]) for e in actual})
  for k,d in bodies.items():assert compact(d.text_content())==compact(plain(actual_by_seq[sequences[k]]))
  for a,targets in redirects.items():
   for t in targets:assert {sequences[k] for k in resolve(t)} <= seqs_by_alias[a]
  for c in actual_by_seq.values():
   for n in walk(c):
    if n.get('tag')=='a':assert unquote(n['href'][7:]) in actual_terms
    if n.get('tag')=='img':assert z.read(n['path'])==media[n['path'][6:]]
 missing_keys=sorted({k for k,v in rows}-actual_terms)
 if name=='ruigigo':
  assert not missing_keys and not issues['unresolved_redirects']
  assert len(seqs_by_alias['あう'])>=2
 else:
  # The original author file has the same missing bodies; record a comparison.
  original=[(k.decode(),v.decode()) for k,v in MDX(str(ROOT/'sources/nichibei-original.mdx')).items()]
  original_bodies={k:html.fragment_fromstring(v,create_parent='div') for k,v in original if not v.strip().startswith('@@@LINK=')}
  assert set(original_bodies)==set(bodies)
  assert all(compact(original_bodies[k].text_content())==compact(bodies[k].text_content()) for k in bodies)
  issues['original_and_repaired_body_text_identical']=True
  issues['notes'].append('原作者版与后续修复版正文逐字相同（忽略空白）；缺失目标在二者中均无正文。未将缺词索引伪造成释义。')
  issues['notes'].append('Yomitan 当前 structured-content schema 没有音频节点，且链接只支持 HTTP(S) 或内部查询。本包为文字预览版，不嵌入无效播放按钮；原 MDD 已留存。')
 issues['notes'].append('无可靠逐词词性，rules 留空；未推测改写原书内容。')
 issues['source_keys_without_body']=missing_keys
 report={'title':cfg['title'],'revision':index['revision'],'source_records':len(rows),'body_records':len(bodies),'search_records':len(actual),'unique_search_terms':len(actual_terms),'source_redirect_records':sum(v.strip().startswith('@@@LINK=') for k,v in rows),'unresolved_redirects':len(issues['unresolved_redirects']),'unresolved_target_ids':len({v['target'].rstrip('#') for v in issues['unresolved_redirects']}),'unresolved_links':len(issues['unresolved_links']),'source_keys_without_body':len(missing_keys),'all_available_body_text_preserved':True,'all_resolvable_redirect_destinations_preserved':True,'all_source_keys_preserved':not missing_keys,'official_schema_valid':True,'archive_crc_valid':True,'all_clickable_links_resolve':True,'media_files':len(media),'browser_import_tested':False,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'zip_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'zip_bytes':out.stat().st_size,**stats}
 save(ROOT/'reports'/f'{name}-qa.json',report);save(ROOT/'reports'/f'{name}-source-issues.json',issues)
 def render(v):
  if isinstance(v,str):return html_std.escape(v)
  if isinstance(v,list):return ''.join(map(render,v))
  tag=v['tag'];attrs=''
  if v.get('data'):attrs+=' data-sc-extra="'+html_std.escape(v['data']['extra'])+'"'
  if v.get('href'):attrs+=' href="'+html_std.escape(v['href'])+'"'
  if v.get('title'):attrs+=' title="'+html_std.escape(v['title'])+'"'
  if v.get('style'):attrs+=' style="'+';'.join(re.sub(r'[A-Z]',lambda m:'-'+m[0].lower(),k)+':'+str(t) for k,t in v['style'].items())+'"'
  if tag=='img':return '<img width="450" src="data:image/png;base64,'+base64.b64encode(media[v['path'][6:]]).decode()+'">'
  return '<'+tag+attrs+'>'+render(v.get('content',[]))+('' if tag=='br' else '</'+tag+'>')
 if name=='ruigigo':
  with_images=[k for k,d in bodies.items() if d.xpath('.//img')]; selected=[with_images[0],next(k for k in bodies if k.startswith('会う')),next(k for k in bodies if k.startswith('あいだ'))]
 else:selected=[next(k for k in bodies if k.startswith(s)) for s in ['ああでもない','きげんをとる','あいじん']]
 doc='<!doctype html><html lang="ja"><meta charset="utf-8"><title>'+cfg['title']+'</title><style>'+CSS+'body{font-family:Meiryo,Microsoft YaHei,sans-serif;margin:24px;background:#eee}main{display:grid;grid-template-columns:1fr 1fr;gap:20px}.pane{min-width:0;padding:20px;background:white}.dark{background:#202327;color:#e4e7eb}article{border-bottom:1px solid #888;padding-bottom:20px;margin-bottom:20px}</style><main>'
 for dark in (False,True):
  doc+='<section class="pane '+('dark' if dark else '')+'" data-theme="'+('dark' if dark else 'light')+'">'
  for k in selected:doc+='<article>'+render(contents[k])+'</article>'
  doc+='</section>'
 (ROOT/'reports'/f'{name}-preview.html').write_text(doc+'</main></html>',encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('name',choices=[*CONFIG,'all']);args=parser.parse_args()
 for name in CONFIG if args.name=='all' else [args.name]:build(name)
