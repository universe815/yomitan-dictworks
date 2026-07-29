# Dictionary catalog

`dictionaries.json` is the machine-readable source of truth for the dictionary
catalog. It records language direction, type, build command, revision, archive name,
and update location for every edition.

Distribution states:

- `personal`: the converter and update metadata are ready, while the ZIP is served
  from the owner's computer rather than published by this repository;
- `published`: a stable public archive, update index, license, and evidence are all
  present;
- `retired`: no longer offered to new users, while historical information remains.

Both update-enabled states require a matching `manifests/<id>/index.json`. Changing
an entry to `published` additionally requires a redistribution license and evidence.
CI validates these invariants.
