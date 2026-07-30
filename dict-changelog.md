# Dictionary changelog

This file records converter and dictionary-output changes. A converter change does
not make proprietary source data redistributable.

## 2026-07-30

- Fixed both OALD editions as `2026.07.30.4`: changed all dictionary-style
  selectors to Yomitan's rendered `data-sc-oald` attributes, aligned the
  standalone preview with the real renderer, and added archive QA that rejects
  the non-rendering `data-oald` form.
- Refined both OALD editions as `2026.07.30.3`: restored 40+ additional
  high-value source classes and custom tags; distinguished OALD, AI, and Leon
  Chinese sources; color-coded all 18 supplemental module kinds; added native
  folding for Idioms and Phrasal Verbs; and recreated richer layouts for
  British/American usage, verb forms, word families, collocations, grammar,
  Wordfinder, and related-entry metadata.
- Rebuilt both OALD editions as `2026.07.30.2`: restored whitespace lost
  around inline MDX nodes; preserved substantially more semantic structure;
  separated English examples and Chinese translations; added distinct
  headword, pronunciation, sense, topic, idiom, and CEFR styling; and changed
  long supplemental sections into native Yomitan `details` panels.
- Added representative OALD spacing/structure QA, standalone visual previews,
  and fast archive-wide checks for term rows, collapsible sections, CRCs, and
  the complete 622-image reference set.
- Migrated all four active editions to versioned GitHub Release automatic
  downloads in `2026.07.30.1`, while retaining the same public Google Drive
  files for manual downloads and archival copies.
- Changed the two Japanese dictionary build filenames and Release display labels
  to Chinese user-facing names; GitHub-safe Release filenames, stable internal
  catalog IDs, and update-manifest paths remain ASCII.
- Added metadata-only ZIP repacking for already validated formal archives.
- Strengthened scheduled public-link checks with bounded ZIP end-of-directory
  validation and required catalog byte-size/SHA-256 metadata.

## 2026-07-29

- Migrated 《新世纪日汉双解大辞典》 automatic downloads to a GitHub
  Release asset in `2026.07.29.5`; Google Drive remains the manual download
  and archive location.
- Refreshed 《新世纪日汉双解大辞典》 typography in `2026.07.29.4`:
  removed the gray Chinese-gloss background, changed Japanese and Chinese text
  to system sans-serif stacks, and reduced the visual weight of headwords and
  Chinese translations.
- Switched all four editions from localhost-only updates to public Google Drive
  downloads and bumped them to `2026.07.29.3`.
- Added one stable public file page and one anonymous direct update URL per edition.
- Reworked the root catalog in the table-led style of W1ght/yomitan-guide, with
  separate descriptions, downloads, and update manifests.
- Added scheduled public-link verification and explicit Drive file-ID validation.
- Replaced contradictory "do not distribute" metadata with neutral third-party
  ownership and non-affiliation notices without asserting a content license.
- Enabled Yomitan update metadata in all four build configurations.
- Assigned stable per-edition GitHub Raw `indexUrl` values and localhost
  `downloadUrl` values for personal updates without GitHub Releases.
- Added a localhost update server for catalog archives stored in the Google Drive
  sync folder.
- Standardized personal ZIP storage under a catalog-driven Google Drive tree and
  added SHA-256-verified synchronization from `dictionary-output`.
- Reworked the root README as a language/type/direction dictionary catalog.
- Bumped all four editions to `2026.07.29.2`, allowing installations of
  `2026.07.29.1` to receive the corrected non-Release update metadata.
- Renamed the XSJRH archive to a stable filename independent of its revision.
- Clarified that the first update-enabled build must be installed from its ZIP or
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
