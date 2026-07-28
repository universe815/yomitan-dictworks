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

For each public dictionary:

- Release asset:
  `https://github.com/universe815/yomitan-dictworks/releases/latest/download/<name>.zip`
- Update index:
  `https://raw.githubusercontent.com/universe815/yomitan-dictworks/main/manifests/<id>/index.json`

Copy `manifests/index.template.json` to `manifests/<id>/index.json`, replace every
placeholder, and commit it. The remote index is ordinary Yomitan `index.json`
metadata; Yomitan compares its `revision` with the installed dictionary and then
downloads `downloadUrl`.

The dictionary's own config must contain the same stable URLs:

```json
{
  "isUpdatable": true,
  "indexUrl": "https://raw.githubusercontent.com/universe815/yomitan-dictworks/main/manifests/<id>/index.json",
  "downloadUrl": "https://github.com/universe815/yomitan-dictworks/releases/latest/download/<name>.zip"
}
```

Do not enable these fields before the URLs work. `src/update-metadata.ts` deliberately
fails the build when only part of the update configuration is present.

## Release sequence

1. Build and validate locally.
2. Create a versioned tag such as `<id>-2026.07.28.1`.
3. Create the GitHub Release and upload the fixed-name ZIP asset.
4. Confirm the `releases/latest/download/...` URL returns that ZIP.
5. Update and commit `manifests/<id>/index.json`.
6. Import once from the update-index URL and test an update from the previous revision.

If a dictionary may not legally be redistributed, stop after local validation. Keep
its manifest absent and its release status listed as “converter only”.
