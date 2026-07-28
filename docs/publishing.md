# Publishing and automatic updates

GitHub source code and dictionary data have different licensing risk. Publishing a
converter does not authorize publishing the archive it creates.

## Release gate

Before making a dictionary downloadable, verify:

1. the data and every bundled media type may be redistributed;
2. attribution and license text are present;
3. source files, local paths, reports, credentials, and unrelated resources are absent;
4. dictionary-specific QA and official schema validation pass;
5. the ZIP imports into a clean Yomitan profile;
6. its revision is greater than the previous public revision.

## Recommended GitHub layout

Use Git for source code and small update indexes. Put ZIP files in GitHub Releases,
not in repository history.

For each public edition:

- Release asset:
  `https://github.com/universe815/yomitan-dictworks/releases/download/<id>-<revision>/<name>.zip`
- Update index:
  `https://raw.githubusercontent.com/universe815/yomitan-dictworks/main/manifests/<id>/index.json`

Copy `manifests/index.template.json` to `manifests/<id>/index.json`, replace every
placeholder, and commit it. The remote index is ordinary Yomitan `index.json`
metadata; Yomitan compares its `revision` with the installed dictionary and then
downloads `downloadUrl`.

Do not use `releases/latest/download/...` in a multi-dictionary repository: the
latest repository release may belong to another dictionary and omit this asset.

The dictionary's own config must contain the same stable URLs:

```json
{
  "isUpdatable": true,
  "indexUrl": "https://raw.githubusercontent.com/universe815/yomitan-dictworks/main/manifests/<id>/index.json",
  "downloadUrl": "https://github.com/universe815/yomitan-dictworks/releases/download/<id>-<revision>/<name>.zip"
}
```

Do not enable these fields before the URLs work. `src/update-metadata.ts` deliberately
fails the build when only part of the update configuration is present.

## Release sequence

1. Record the content license and redistribution evidence in
   `catalog/dictionaries.json`.
2. Choose a versioned tag such as `<id>-2026.07.28.1` and put that URL in the
   dictionary config.
3. Build and validate locally.
4. Create the GitHub Release and upload the fixed-name ZIP asset:

   ```powershell
   gh release create "<id>-<revision>" `
     "dictionary-output/<name>.zip" `
     --repo universe815/yomitan-dictworks `
     --title "<title> <revision>" `
     --notes "See the dictionary page and dict-changelog.md."
   ```

5. Confirm the versioned download URL returns that ZIP.
6. Extract its embedded index as the remote update index:

   ```powershell
   python scripts/extract_update_index.py `
     "dictionary-output/<name>.zip" `
     "manifests/<id>/index.json"
   ```

7. Change the catalog distribution state to `published`, fill every URL/license
   field, and commit the manifest and catalog.
8. Import once from the update-index URL and test an update from the previous revision.

If a dictionary may not legally be redistributed, stop after local validation. Keep
its manifest absent and its release status listed as “converter only”.
