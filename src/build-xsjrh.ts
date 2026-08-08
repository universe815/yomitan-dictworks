import { createReadStream } from 'node:fs';
import { readFile, readdir } from 'node:fs/promises';
import path from 'node:path';
import readline from 'node:readline';
import { Dictionary, DictionaryIndex, TermEntry } from 'yomichan-dict-builder';
import type { DetailedDefinition, StructuredContent } from 'yomichan-dict-builder/dist/types/yomitan/termbank';
import type { IsoLanguageCode } from 'yomichan-dict-builder/dist/types/IsoLanguageCode';
import { applyUpdateMetadata, type UpdateMetadata } from './update-metadata';

interface Config extends UpdateMetadata {
  title: string;
  revision: string;
  author: string;
  description: string;
  attribution: string;
  url: string;
  inputNdjson: string;
  outputFile: `${string}.zip`;
  stylesFile: string;
  resourcesDir: string;
  sourceLanguage?: IsoLanguageCode;
  targetLanguage?: IsoLanguageCode;
  resourcePathPrefix?: string;
  redirectDataKey?: string;
}

interface RecordValue {
  term: string;
  reading: string;
  sequence: number;
  definition?: DetailedDefinition;
  redirect?: string;
}

const root = process.cwd();

async function walk(directory: string, prefix = ''): Promise<string[]> {
  const values: string[] = [];
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const relative = prefix ? `${prefix}/${entry.name}` : entry.name;
    const absolute = path.join(directory, entry.name);
    if (entry.isDirectory()) values.push(...await walk(absolute, relative));
    else values.push(relative);
  }
  return values;
}

function redirectDefinition(target: string, dataKey: string, language: string): DetailedDefinition {
  const content: StructuredContent = {
    tag: 'div',
    data: { [dataKey]: 'redirect' },
    content: ['参见 ', { tag: 'a', href: `?query=${encodeURIComponent(target)}`, content: target, lang: language }],
  };
  return { type: 'structured-content', content };
}

async function main(): Promise<void> {
  const configPath = process.argv.slice(2).find((value) => value !== '--') ?? 'config/xsjrh.json';
  const config = JSON.parse(await readFile(path.resolve(root, configPath), 'utf8')) as Config;
  const dictionary = new Dictionary({ fileName: config.outputFile });
  const sourceLanguage = config.sourceLanguage ?? 'ja';
  const targetLanguage = config.targetLanguage ?? 'zh';
  const resourcePathPrefix = (config.resourcePathPrefix ?? 'img/xsjrh').replace(/\/$/, '');
  const redirectDataKey = config.redirectDataKey ?? 'xsjrh';
  let index = new DictionaryIndex()
    .setTitle(config.title)
    .setRevision(config.revision)
    .setAuthor(config.author)
    .setDescription(config.description)
    .setAttribution(config.attribution)
    .setUrl(config.url)
    .setSequenced(true)
    .setSourceLanguage(sourceLanguage)
    .setTargetLanguage(targetLanguage);
  index = applyUpdateMetadata(index, config);
  await dictionary.setIndex(index.build());
  await dictionary.addFile(path.resolve(root, config.stylesFile), 'styles.css');

  const resourcesRoot = path.resolve(root, config.resourcesDir);
  const resources = (await walk(resourcesRoot)).sort();
  let packed = 0;
  for (const relative of resources) {
    const extension = path.extname(relative).toLowerCase();
    let archivePath: string | undefined;
    if (['.png', '.jpg', '.jpeg', '.svg'].includes(extension)) archivePath = `${resourcePathPrefix}/${relative}`;
    else if (['.otf', '.ttf', '.woff', '.woff2'].includes(extension)) archivePath = `fonts/${path.basename(relative)}`;
    if (!archivePath) continue;
    await dictionary.addFile(path.join(resourcesRoot, ...relative.split('/')), archivePath);
    packed += 1;
  }
  console.log(`已加入 ${packed.toLocaleString()} 个图片/字体资源。`);

  const lines = readline.createInterface({
    input: createReadStream(path.resolve(root, config.inputNdjson), { encoding: 'utf8' }),
    crlfDelay: Infinity,
  });
  let count = 0;
  let direct = 0;
  let redirects = 0;
  for await (const line of lines) {
    if (!line.trim()) continue;
    const record = JSON.parse(line) as RecordValue;
    if (!record.term || !Number.isInteger(record.sequence)) throw new Error(`NDJSON 第 ${count + 1} 行无效`);
    const entry = new TermEntry(record.term).setReading(record.reading ?? '').setSequenceNumber(record.sequence);
    if (record.definition !== undefined) {
      entry.addDetailedDefinition(record.definition);
      direct += 1;
    } else if (record.redirect) {
      entry.addDetailedDefinition(redirectDefinition(record.redirect, redirectDataKey, sourceLanguage));
      redirects += 1;
    } else throw new Error(`NDJSON 第 ${count + 1} 行没有释义或跳转`);
    await dictionary.addTerm(entry.build());
    count += 1;
    if (count % 50000 === 0) console.log(`已读取 ${count.toLocaleString()} 条记录…`);
  }

  const stats = await dictionary.export(path.resolve(root, 'dictionary-output'));
  console.log(`\n✓ ${config.title} -> dictionary-output/${config.outputFile}`);
  console.log(`正文 ${direct.toLocaleString()}，检索跳转 ${redirects.toLocaleString()}`);
  console.table(stats);
}

main().catch((error: unknown) => {
  console.error(error instanceof Error ? error.stack ?? error.message : error);
  process.exitCode = 1;
});
