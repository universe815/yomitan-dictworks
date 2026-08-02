import { createReadStream } from 'node:fs';
import { readFile, readdir } from 'node:fs/promises';
import path from 'node:path';
import readline from 'node:readline';
import {
  Dictionary,
  DictionaryIndex,
  TermEntry,
} from 'yomichan-dict-builder';
import type {
  DetailedDefinition,
  StructuredContent,
} from 'yomichan-dict-builder/dist/types/yomitan/termbank';
import {
  applyUpdateMetadata,
  type UpdateMetadata,
} from './update-metadata';

interface OaldConfig extends UpdateMetadata {
  title: string;
  revision: string;
  author: string;
  description: string;
  attribution: string;
  url: string;
  inputNdjson: string;
  outputFile: `${string}.zip`;
  stylesFile: string;
  imagesDir?: string;
  imagesManifest?: string;
  termBankMaxSize?: number;
  mediaCompression?: 'STORE' | 'DEFLATE';
}

interface ConvertedRecord {
  term: string;
  sequence: number;
  definition?: DetailedDefinition;
  redirect?: string;
}

const projectRoot = process.cwd();

async function readConfig(): Promise<OaldConfig> {
  const argument = process.argv.slice(2).find((value) => value !== '--');
  const configPath = argument ?? 'config/oald.json';
  const text = await readFile(path.resolve(projectRoot, configPath), 'utf8');
  return JSON.parse(text) as OaldConfig;
}

function assertRecord(value: unknown, lineNumber: number): asserts value is ConvertedRecord {
  if (typeof value !== 'object' || value === null) {
    throw new Error(`NDJSON 第 ${lineNumber} 行不是对象`);
  }
  const record = value as Partial<ConvertedRecord>;
  if (!record.term?.trim() || !Number.isInteger(record.sequence) || record.sequence! < 1) {
    throw new Error(`NDJSON 第 ${lineNumber} 行缺少有效的 term/sequence`);
  }
  if (record.definition === undefined && !record.redirect) {
    throw new Error(`NDJSON 第 ${lineNumber} 行既没有 definition 也没有 redirect`);
  }
}

function redirectDefinition(target: string): DetailedDefinition {
  const content: StructuredContent = {
    tag: 'div',
    data: { oald: 'redirect' },
    content: [
      '参见 ',
      {
        tag: 'a',
        href: `?query=${encodeURIComponent(target)}`,
        content: target,
        lang: 'en',
      },
    ],
  };
  return { type: 'structured-content', content };
}

async function main(): Promise<void> {
  const config = await readConfig();
  if (
    config.termBankMaxSize !== undefined
    && (!Number.isInteger(config.termBankMaxSize) || config.termBankMaxSize < 1)
  ) {
    throw new Error('termBankMaxSize 必须是正整数');
  }
  const dictionary = new Dictionary({
    fileName: config.outputFile,
    ...(config.termBankMaxSize === undefined
      ? {}
      : { termBankMaxSize: config.termBankMaxSize }),
  });
  let index = new DictionaryIndex()
    .setTitle(config.title)
    .setRevision(config.revision)
    .setAuthor(config.author)
    .setDescription(config.description)
    .setAttribution(config.attribution)
    .setUrl(config.url)
    .setSequenced(true)
    .setSourceLanguage('en')
    .setTargetLanguage('zh');

  index = applyUpdateMetadata(index, config);
  await dictionary.setIndex(index.build());
  await dictionary.addFile(
    path.resolve(projectRoot, config.stylesFile),
    'styles.css',
  );
  if (config.imagesDir) {
    const imageDirectory = path.resolve(projectRoot, config.imagesDir);
    let imageNames: string[];
    if (config.imagesManifest) {
      const manifest = JSON.parse(
        await readFile(path.resolve(projectRoot, config.imagesManifest), 'utf8'),
      ) as { images_referenced?: unknown };
      if (
        !Array.isArray(manifest.images_referenced)
        || manifest.images_referenced.some((name) => typeof name !== 'string')
      ) {
        throw new Error('图片 manifest 缺少有效的 images_referenced 数组');
      }
      imageNames = (manifest.images_referenced as string[]).sort();
    } else {
      imageNames = (await readdir(imageDirectory))
        .filter((name) => /\.(?:png|jpe?g|svg)$/i.test(name))
        .sort();
    }
    for (const [index, imageName] of imageNames.entries()) {
      const imagePath = path.join(imageDirectory, imageName);
      if (config.mediaCompression === undefined) {
        await dictionary.addFile(imagePath, `img/oald/${imageName}`);
      } else {
        dictionary.zip.file(
          `img/oald/${imageName}`,
          await readFile(imagePath),
          { compression: config.mediaCompression },
        );
      }
      if ((index + 1) % 250 === 0) {
        console.log(`已加入 ${index + 1}/${imageNames.length} 张图片…`);
      }
    }
    console.log(`已加入 ${imageNames.length.toLocaleString()} 张图片。`);
  }

  const inputPath = path.resolve(projectRoot, config.inputNdjson);
  const lines = readline.createInterface({
    input: createReadStream(inputPath, { encoding: 'utf8' }),
    crlfDelay: Infinity,
  });

  let lineNumber = 0;
  let directCount = 0;
  let redirectCount = 0;
  for await (const line of lines) {
    lineNumber += 1;
    if (!line.trim()) continue;
    const parsed: unknown = JSON.parse(line);
    assertRecord(parsed, lineNumber);

    const entry = new TermEntry(parsed.term)
      .setReading('')
      .setSequenceNumber(parsed.sequence);
    if (parsed.definition !== undefined) {
      entry.addDetailedDefinition(parsed.definition);
      directCount += 1;
    } else if (parsed.redirect) {
      entry.addDetailedDefinition(redirectDefinition(parsed.redirect));
      redirectCount += 1;
    }
    await dictionary.addTerm(entry.build());

    if (lineNumber % 50_000 === 0) {
      console.log(`已读取 ${lineNumber.toLocaleString()} 条记录…`);
    }
  }

  const outputDir = path.resolve(projectRoot, 'dictionary-output');
  const stats = await dictionary.export(outputDir);
  console.log(`\n✓ ${config.title} -> dictionary-output/${config.outputFile}`);
  console.log(`正文 ${directCount.toLocaleString()}，别名 ${redirectCount.toLocaleString()}`);
  console.table(stats);
}

main().catch((error: unknown) => {
  console.error(error instanceof Error ? error.stack ?? error.message : error);
  process.exitCode = 1;
});
