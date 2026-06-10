# custody-benchmarks

Versioned benchmark content for the GEOINT custody evaluation harness
(DIU LOE-1). Consumed by `checkmaite-plugin-custody`:

- `scenarios/*.yaml` — one `ScenarioConfig` per file (schema:
  `checkmaite_plugin_custody.custody_schemas`, normative source: the shared
  contracts doc §3). Passed to the plugin via `--scenarios-dir`.
- `rubrics/{citation,explanation,uncertainty}.md` — judge system prompts,
  loaded by filename via the plugin's `--rubrics-dir`.
- `datasets/manifest.yaml` — provenance + license per dataset.

Validate content:

```bash
/Users/khan/openteams/checkmaite-plugin-custody/.venv/bin/pytest tests/ -v
```
