# Yomitan Dictworks

A categorized collection of multilingual dictionaries and reproducible conversion
tools for [Yomitan](https://github.com/yomidevs/yomitan).

The catalog layout follows
[MarvNC/yomitan-dictionaries](https://github.com/MarvNC/yomitan-dictionaries):
dictionaries are grouped by source language, dictionary type, and translation
direction. This project additionally keeps a machine-readable catalog, per-dictionary
update indexes, reproducible QA, and versioned GitHub Releases.

## Dictionary collection

### What should I install?

- For Japanese reading with Chinese explanations:
  [新世纪日汉双解大辞典](japanese/term/ja-zh/xsjrh/) is the broad general dictionary;
  [新日汉拟声拟态词词典](japanese/term/ja-zh/onomatopoeia/) is the specialized
  companion for mimetic and onomatopoeic expressions.
- For English reading with Chinese explanations:
  [OALD](english/term/en-zh/oald/) provides text and illustrated editions.

“Build ready” and “public download available” are separate states. Commercial
dictionary content remains unavailable until redistribution rights are documented.

### Downloads and updates

[Open the download center](dl/) for public ZIP files, checksums, revisions, licenses,
and Yomitan automatic-update indexes.

| Source language | Type | Direction | Dictionary | Build | Download |
| --- | --- | --- | --- | --- | --- |
| Japanese | Term | JA → ZH | [新世纪日汉双解大辞典](japanese/term/ja-zh/xsjrh/) | Ready | Rights review |
| Japanese | Term | JA → ZH | [新日汉拟声拟态词词典](japanese/term/ja-zh/onomatopoeia/) | Ready | Rights review |
| English | Term | EN → ZH | [OALD text edition](english/term/en-zh/oald/) | Ready | Rights review |
| English | Term | EN → ZH | [OALD illustrated edition](english/term/en-zh/oald/) | Ready | Rights review |

## Japanese

### Terms

#### Japanese → Chinese

- [新世纪日汉双解大辞典（完整图文版）](japanese/term/ja-zh/xsjrh/)
- [新日汉拟声拟态词词典 第2版](japanese/term/ja-zh/onomatopoeia/)

The Japanese section is prepared for the same top-level categories used by larger
Yomitan collections: `term`, `frequency`, `grammar`, and `kanji`.

[Browse all Japanese dictionaries](japanese/).

## English

### Terms

#### English → Chinese

- [OALD text and illustrated editions](english/term/en-zh/oald/)

[Browse all English dictionaries](english/).

## Repository layout

```text
catalog/                         machine-readable dictionary catalog
dl/                              public download center
english/term/en-zh/<dictionary>/ English term dictionaries
japanese/term/ja-zh/<dictionary>/ Japanese term dictionaries
config/                          build metadata
src/                             Yomitan archive builders
scripts/                         converters, QA, schema and catalog checks
styles/                          dictionary-scoped CSS
manifests/<id>/index.json        public automatic-update indexes
dictionary-output/               ignored local build output
```

## Build a local dictionary

Requirements: Node.js 20+, pnpm, and Python 3.11+.

```powershell
pnpm install --frozen-lockfile
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Build and validate the redistributable sample:

```powershell
pnpm dict -- sample-ja-zh
python scripts/validate_yomitan_schema.py dictionary-output/sample-ja-zh.zip
```

Commercial dictionaries require a legally obtained local MDX/MDD. See each
dictionary page for its converter, build, and QA commands.

## Add or publish a dictionary

- [Adding a dictionary](docs/adding-a-dictionary.md)
- [Publishing and automatic updates](docs/publishing.md)
- [Catalog conventions](catalog/README.md)
- [Dictionary changelog](dict-changelog.md)
- [Contributing](CONTRIBUTING.md)

Public editions use a stable raw `indexUrl` and a versioned GitHub Release
`downloadUrl`. The repository does not use a single `releases/latest` link because
the newest release may belong to a different dictionary.

## License and content rights

Original code and documentation are MIT licensed. Dictionary entries, examples,
images, audio, fonts, branding, and other third-party content retain their own
licenses. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
