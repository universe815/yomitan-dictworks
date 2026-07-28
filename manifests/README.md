# Update indexes

Each published dictionary gets one directory containing an `index.json` served over a
stable raw URL. Start from `index.template.json`.

Templates are not live update endpoints. Do not add a real manifest until the
corresponding archive has a lawful, stable public download URL.

Each manifest points to a versioned per-dictionary GitHub Release tag. Avoid
`releases/latest` because the newest repository release can belong to another
dictionary.
