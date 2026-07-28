# Dictionary catalog

`dictionaries.json` is the machine-readable source of truth for the public catalog.
It records language direction, type, build command, revision, release asset, and
distribution status for every edition.

Distribution states:

- `rights-review`: conversion is ready, but public redistribution has not been
  authorized or documented;
- `published`: a release asset, update index, license, and evidence are all present;
- `retired`: no longer offered to new users, while historical information remains.

Changing an entry to `published` requires all distribution fields and a matching
`manifests/<id>/index.json`. CI validates these invariants.
