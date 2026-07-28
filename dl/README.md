# Dictionary downloads

This directory is the download center, analogous to the `dl/` area in
MarvNC/yomitan-dictionaries. Large ZIP files are hosted as GitHub Release assets
instead of being committed to Git history.

## Published dictionaries

No commercial dictionary archive is public yet. The converters are ready, while the
content licenses and redistribution evidence still require confirmation.

Once an edition is authorized, its row will provide:

- a direct ZIP link to a versioned GitHub Release;
- a stable Yomitan update-index URL;
- revision, size, checksum, source, and license;
- a link to the dictionary page and changelog.

The authoritative state is stored in
[`catalog/dictionaries.json`](../catalog/dictionaries.json). CI rejects download links
that are marked public without license evidence and a real update manifest.
