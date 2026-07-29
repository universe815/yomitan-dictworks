# Adding a dictionary

The repository is a source-and-tooling hub. Add a converter here only when another
person can understand how to reproduce the build without receiving your private
source files.

## 1. Establish provenance

Record the source name, version/date, URL, license, required attribution, and whether
definitions, examples, images, audio, and fonts may be redistributed. If the answer
is unclear, publish converter code only.

## 2. Choose the pipeline

- Simple JSON entries: add an item to `config/dictionaries.json` and use `src/build.ts`.
- Large or richly formatted MDX: write a streaming converter that emits NDJSON, then
  use or extend one of the structured builders.
- Images and fonts: extract them to `generated/<dictionary>-resources/` and refer to
  archive-relative paths from structured content.

Committed configuration must contain relative paths only. Source MDX/MDD paths belong
on the command line and must never be saved in reports that are committed.

## 3. Preserve Yomitan semantics

- Give related spellings and redirects the same sequence number where appropriate.
- Use structured content instead of raw source HTML.
- Keep links as `?query=<encoded term>` links.
- Add a scoped attribute in structured content and target it from `styles/<id>.css`.
- Treat subentries as searchable terms when users reasonably expect direct lookup.
- Set `sourceLanguage` and `targetLanguage`.

## 4. Add repeatable checks

At minimum, test representative headwords, redirects, empty definitions, entry count,
and the official term-bank schema. For rich dictionaries, also check missing media,
unsafe file names, broken query links, Ruby order, and the final ZIP member list.

The repository-wide checks are:

```powershell
pnpm check
python -m compileall -q scripts
python scripts/check_repository.py
```

## 5. Document and version

Add a page under `<source language>/<category>/<pair>/<id>/`, an entry in
`catalog/dictionaries.json`, a row in the root catalog, and an entry in
`dict-changelog.md`. Increment `revision` whenever the generated dictionary changes,
even if the source data version did not change.

All active dictionaries use public mode. Enable update fields only after the stable
Google Drive file ID, public ZIP download, and GitHub Raw update manifest are
configured as described in [publishing.md](publishing.md).

Record `driveFileId`, `driveFileUrl`, `driveFolderUrl`, and the anonymous
`downloadUrl`. Put one directly importable ZIP per edition in the flat `Downloads/`
folder, with a language/type prefix in its filename. Record `rightsStatus` and a
truthful `rightsStatement`; never infer or invent a content license.
