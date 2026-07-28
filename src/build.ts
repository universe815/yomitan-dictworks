import { readFile } from 'node:fs/promises';
import path from 'node:path';
import {
  Dictionary,
  DictionaryIndex,
  TermEntry,
} from 'yomichan-dict-builder';
import {
  applyUpdateMetadata,
  type UpdateMetadata,
} from './update-metadata';

interface DictionaryConfig extends UpdateMetadata {
  id: string;
  title: string;
  revision: string;
  author?: string;
  description?: string;
  attribution?: string;
  url?: string;
  input: string;
  outputFile: `${string}.zip`;
}

interface SourceEntry {
  term: string;
  reading?: string;
  definitions: string[];
  frequency?: number;
}

const projectRoot = process.cwd();

async function readJson<T>(relativePath: string): Promise<T> {
  const filePath = path.resolve(projectRoot, relativePath);
  const text = await readFile(filePath, 'utf8');
  return JSON.parse(text) as T;
}

function validateSource(entries: SourceEntry[], input: string): void {
  if (!Array.isArray(entries)) {
    throw new Error(`${input}: 顶层必须是 JSON 数组`);
  }

  entries.forEach((entry, index) => {
    if (!entry.term?.trim()) {
      throw new Error(`${input}: 第 ${index + 1} 项缺少 term`);
    }
    if (!Array.isArray(entry.definitions) || entry.definitions.length === 0) {
      throw new Error(`${input}: 第 ${index + 1} 项至少需要一条 definition`);
    }
    if (entry.definitions.some((definition) => !definition?.trim())) {
      throw new Error(`${input}: 第 ${index + 1} 项含有空 definition`);
    }
    if (
      entry.frequency !== undefined &&
      (!Number.isFinite(entry.frequency) || entry.frequency < 0)
    ) {
      throw new Error(`${input}: 第 ${index + 1} 项的 frequency 必须是非负数`);
    }
  });
}

async function buildDictionary(config: DictionaryConfig): Promise<void> {
  const source = await readJson<SourceEntry[]>(config.input);
  validateSource(source, config.input);

  const dictionary = new Dictionary({ fileName: config.outputFile });
  let index = new DictionaryIndex()
    .setTitle(config.title)
    .setRevision(config.revision);

  if (config.author) index = index.setAuthor(config.author);
  if (config.description) index = index.setDescription(config.description);
  if (config.attribution) index = index.setAttribution(config.attribution);
  if (config.url) index = index.setUrl(config.url);
  index = applyUpdateMetadata(index, config);

  await dictionary.setIndex(index.build());

  for (const sourceEntry of source) {
    let term = new TermEntry(sourceEntry.term);
    if (sourceEntry.reading) term = term.setReading(sourceEntry.reading);
    for (const definition of sourceEntry.definitions) {
      term = term.addDetailedDefinition(definition);
    }
    await dictionary.addTerm(term.build());

    if (sourceEntry.frequency !== undefined) {
      dictionary.addTermMeta([
        sourceEntry.term,
        'freq',
        sourceEntry.frequency,
      ]);
    }
  }

  const outputDir = path.resolve(projectRoot, 'dictionary-output');
  const stats = await dictionary.export(outputDir);
  console.log(`\n✓ ${config.title} -> dictionary-output/${config.outputFile}`);
  console.table(stats);
}

async function main(): Promise<void> {
  const configs = await readJson<DictionaryConfig[]>('config/dictionaries.json');
  const argument = process.argv.slice(2).find((value) => value !== '--');

  if (!Array.isArray(configs) || configs.length === 0) {
    throw new Error('config/dictionaries.json 至少需要一个词典配置');
  }

  const selected = argument === '--all'
    ? configs
    : configs.filter((config) => config.id === argument);

  if (selected.length === 0) {
    const ids = configs.map((config) => config.id).join(', ');
    throw new Error(`请指定词典 id（可选：${ids}），或使用 --all`);
  }

  for (const config of selected) {
    await buildDictionary(config);
  }
}

main().catch((error: unknown) => {
  console.error(error instanceof Error ? error.message : error);
  process.exitCode = 1;
});
