# Dictionary changelog

This file records converter and dictionary-output changes. A converter change does
not make proprietary source data redistributable.

## 2026-07-29

- Enabled Yomitan update metadata in all four build configurations.
- Assigned stable per-edition `indexUrl` values and versioned GitHub Release
  `downloadUrl` values.
- Standardized four-part numeric revisions at `2026.07.29.1`.
- Renamed the XSJRH release asset to a stable filename independent of its revision.
- Clarified that the first update-enabled release must be installed from its ZIP or
  ZIP URL, not from the JSON update index.

## 2026-07-28 — catalog update

- Reorganized dictionaries as source language → type → language pair → dictionary,
  following the catalog style of MarvNC/yomitan-dictionaries.
- Added Japanese and English category pages, a download center, and a machine-readable
  catalog with separate build and distribution states.
- Added catalog validation and a per-dictionary versioned Release/update-index
  workflow suitable for multiple independently updated dictionaries.

## 2026-07-28

- Initialized the public source repository and multi-dictionary catalog.
- Added converters and Yomitan builders for OALD, 《新世纪日汉双解大辞典》,
  and 《新日汉拟声拟态词词典》.
- Added schema validation, dictionary-specific QA, CI, strict ignore rules, and
  optional Yomitan remote-update metadata.
- Kept all commercial source files, extracted resources, and generated ZIP archives
  out of the repository and releases.
