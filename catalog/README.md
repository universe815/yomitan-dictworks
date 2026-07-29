# Dictionary catalog

`dictionaries.json` is the machine-readable source of truth for the dictionary
catalog. It records language direction, type, build command, revision, archive name,
and update location for every edition.

Distribution states:

- `personal`: the converter and update metadata are ready; the ZIP is stored in the
  owner's Google Drive and served from its local sync directory;
- `published`: a stable public archive, update index, license, and evidence are all
  present;
- `retired`: no longer offered to new users, while historical information remains.

Both update-enabled states require a matching `manifests/<id>/index.json`. Changing
an entry to `published` additionally requires a redistribution license and evidence.
For personal entries, `archivePath` is relative to the configured Google Drive
Yomitan root. CI validates these invariants.
