#!/usr/bin/env node
/**
 * Convert the public NINJAL V-V Compound Verb Lexicon data embedded in
 * headwords.js into the structured NDJSON consumed by build-xsjrh.ts.
 *
 * The source file is deliberately supplied by the caller instead of being
 * committed here: the NINJAL repository states that the original Excel data
 * is downloadable upon agreement.  The official website currently exposes
 * the same records to its search UI as a JavaScript array, which is suitable
 * for a personal/local conversion but is not a blanket redistribution grant.
 */

import fs from 'node:fs';
import path from 'node:path';

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 1) {
    const value = argv[i];
    if (!value.startsWith('--')) continue;
    const key = value.slice(2);
    const next = argv[i + 1];
    if (!next || next.startsWith('--')) throw new Error(`缺少参数值: --${key}`);
    args[key] = next;
    i += 1;
  }
  for (const key of ['source', 'output', 'report']) {
    if (!args[key]) throw new Error(`必须指定 --${key}`);
  }
  return args;
}

function readHeadwords(sourcePath) {
  let source = fs.readFileSync(sourcePath, 'utf8').replace(/^\uFEFF/, '');
  source = source.replace(/^var\s+headwords\s*=\s*/, '').replace(/;\s*$/, '');
  const records = JSON.parse(source);
  if (!Array.isArray(records)) throw new Error('headwords.js 未包含数组');
  return records;
}

function text(value) {
  return typeof value === 'string' ? value.trim() : '';
}

function node(tag, content, data = {}, extra = {}) {
  return { tag, content, data, ...extra };
}

function span(value, className, lang) {
  if (!text(value)) return null;
  return node('span', value, { vv: className }, lang ? { lang } : {});
}

function line(label, value, lang = undefined, className = 'field') {
  const valueNode = span(value, className, lang);
  if (!valueNode) return null;
  return node('div', [span(label, 'label'), valueNode], { vv: 'line' });
}

function patternText(patterns) {
  if (!Array.isArray(patterns)) return '';
  return patterns
    .flatMap((entry) => Array.isArray(entry?.pattern) ? entry.pattern : [])
    .map((item) => text(item?.item))
    .filter(Boolean)
    .join('　');
}

function exampleNode(example) {
  const japanese = text(example?.example);
  if (!japanese) return null;
  const translations = [
    ['zh', text(example?.example_sc)],
    ['en', text(example?.example_en)],
    ['ko', text(example?.example_kr)],
    ['zh-TW', text(example?.example_tc)],
  ].filter(([, value]) => value);
  const content = [
    node('div', japanese, { vv: 'example-ja' }, { lang: 'ja' }),
    ...translations.map(([lang, value]) => node('div', value, { vv: 'example-translation' }, { lang })),
  ];
  if (example?.romaji) content.push(node('div', text(example.romaji), { vv: 'romaji' }, { lang: 'en' }));
  return node('div', content, { vv: 'example' });
}

function senseNode(sense, index) {
  const definition = text(sense?.definition);
  const definitionSc = text(sense?.definition_sc);
  const definitionEn = text(sense?.definition_en);
  const definitionTc = text(sense?.definition_tc);
  const definitionKr = text(sense?.definition_kr);
  const content = [
    node('div', [span(`${index + 1}.`, 'sense-number'), span(definition, 'definition-ja', 'ja')].filter(Boolean), { vv: 'definition' }),
    span(definitionSc, 'definition-sc', 'zh'),
    span(definitionEn, 'definition-en', 'en'),
    span(definitionTc, 'definition-tc', 'zh-TW'),
    span(definitionKr, 'definition-kr', 'ko'),
  ].filter(Boolean);

  const pattern = patternText(sense?.patterns);
  if (pattern) content.push(node('div', [span('句型', 'label'), span(pattern, 'pattern')], { vv: 'line' }));

  const examples = Array.isArray(sense?.examples) ? sense.examples.map(exampleNode).filter(Boolean) : [];
  if (examples.length) {
    content.push(node('details', [
      node('summary', `例句（${examples.length}）`, { vv: 'examples-title' }),
      node('div', examples, { vv: 'examples' }),
    ], { vv: 'examples-details' }, { open: true }));
  }
  return node('div', content, { vv: 'sense' });
}

function definition(record) {
  const headword = text(record.headword1);
  const reading = text(record.reading);
  const header = node('div', [
    span(headword, 'headword', 'ja'),
    span(reading ? `【${reading}】` : '', 'reading', 'ja'),
    span(record.jita, 'jita'),
    span(record.word_structure, 'structure'),
    span(record.headword2 && record.headword2 !== headword ? record.headword2 : '', 'components', 'ja'),
  ].filter(Boolean), { vv: 'header' });

  const senses = Array.isArray(record.senses) ? record.senses.map(senseNode).filter(Boolean) : [];
  const content = [header, ...senses];
  const fields = [
    ['関連する形', record.other_forms, 'ja', 'related'],
    ['類義語', record.synonym, 'ja', 'related'],
    ['反義語', record.antonym, 'ja', 'related'],
    ['名詞形', record.noun_form, 'ja', 'related'],
    ['発音メモ', record.pronunciation_note, 'ja', 'note'],
    ['注記', record.note, 'ja', 'note'],
  ];
  for (const [label, value, lang, className] of fields) {
    const field = line(label, value, lang, className);
    if (field) content.push(field);
  }
  if (record.NLB_link) {
    content.push(node('div', [
      span('NLB', 'label'),
      { tag: 'a', href: `https://www2.ninjal.ac.jp/vvlexicon/`, content: text(record.NLB_link), lang: 'en' },
    ], { vv: 'line' }));
  }
  return { type: 'structured-content', content: node('div', content, { vv: 'entry' }) };
}

function normalizeAlias(value) {
  return text(value).replace(/[、，,／,\/]/g, ' ').split(/[\s　]+/).filter(Boolean);
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const records = readHeadwords(args.source);
  const directTerms = new Set(records.map((record) => text(record.headword1)).filter(Boolean));
  const seenAliases = new Set();
  const output = [];
  const stats = {
    sourceRecords: records.length,
    directRecords: 0,
    aliasRecords: 0,
    senses: 0,
    examples: 0,
    skippedRecords: 0,
    duplicateSourceRecords: 0,
    invalidSourceRecords: 0,
    duplicateAliasesSkipped: 0,
  };

  for (const record of records) {
    const term = text(record.headword1);
    if (!term) {
      stats.skippedRecords += 1;
      stats.invalidSourceRecords += 1;
      continue;
    }
    const sequence = Number(record.headword_id);
    if (!Number.isInteger(sequence)) throw new Error(`无效 headword_id: ${term}`);
    output.push({ term, reading: text(record.reading), sequence, definition: definition(record), sourceKey: term });
    stats.directRecords += 1;
    for (const sense of Array.isArray(record.senses) ? record.senses : []) {
      stats.senses += 1;
      stats.examples += Array.isArray(sense.examples) ? sense.examples.length : 0;
    }

    for (const alias of normalizeAlias(record.other_forms)) {
      if (!alias || directTerms.has(alias) || seenAliases.has(alias)) {
        stats.duplicateAliasesSkipped += 1;
        continue;
      }
      seenAliases.add(alias);
      output.push({ term: alias, reading: text(record.reading), sequence, redirect: term, sourceKey: term });
      stats.aliasRecords += 1;
    }
  }

  output.sort((a, b) => (a.sequence - b.sequence) || a.term.localeCompare(b.term, 'ja'));
  fs.mkdirSync(path.dirname(args.output), { recursive: true });
  fs.writeFileSync(args.output, `${output.map((entry) => JSON.stringify(entry)).join('\n')}\n`, 'utf8');
  const report = {
    source: path.resolve(args.source),
    output: path.resolve(args.output),
    generatedAt: new Date().toISOString(),
    stats,
    outputRecords: output.length,
    note: 'Source records are embedded in the public NINJAL website. This local conversion does not grant redistribution rights.',
  };
  fs.mkdirSync(path.dirname(args.report), { recursive: true });
  fs.writeFileSync(args.report, `${JSON.stringify(report, null, 2)}\n`, 'utf8');
  console.log(JSON.stringify(report, null, 2));
}

main();
