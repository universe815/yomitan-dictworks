# Contributing

Issues and pull requests are welcome for converter bugs, formatting improvements,
tests, documentation, and dictionaries based on redistributable data.

## Requirements for a dictionary contribution

- State the source URL, source version/date, and exact license.
- Explain whether definitions, examples, images, audio, and fonts may be redistributed.
- Do not attach or commit MDX/MDD files whose redistribution is not expressly allowed.
- Keep source-specific paths out of committed configuration.
- Include a repeatable build command and representative QA checks.
- Increment the dictionary `revision` whenever the resulting ZIP changes.

Run these checks before opening a pull request:

```powershell
pnpm install --frozen-lockfile
pnpm check
python -m compileall -q scripts
python scripts/check_repository.py
python scripts/check_catalog.py
```

For a generated ZIP, also run:

```powershell
python scripts/validate_yomitan_schema.py dictionary-output/<dictionary>.zip
```

Commercial dictionary compatibility fixes are acceptable as source code, but the
original content and generated archive must stay outside the repository.
