# Maintenance and release notes

## Validation boundaries

The availability rules originated in a working household YAML setup. This repository is a separate Python integration. Do not describe the new integration as production-tested merely because its predecessor worked.

Local unit tests exercise synthetic availability transitions and shipped artifacts. Registry adapters use Home Assistant APIs; changes to those APIs require runtime validation. hassfest checks metadata, not real hardware behavior.

Before a stable release, verify on a disposable Home Assistant 2026.11+ instance:

- UI setup, duplicate setup prevention, options reload and unload.
- Exclusion label creation, reuse, rename, removal and entity-level exclusions.
- Sensor/switch IDs, restore after restart, monitor freshness and dashboard rendering.
- An observed outage/recovery with a test notification action; switch off suppresses events.
- Two Zigbee2MQTT bridges with independent parent links.
- Existing automations do not overlap with the new blueprint.

Do not install an untested custom integration into a live household merely to obtain a screenshot. Use synthetic data for public examples and issue reports.

## Local storage

One Home Assistant storage key, `offline_devices.<config-entry-id>`, holds the last inventory and switch state. Removing the integration intentionally leaves it available for recovery, along with the user-managed exclusion label. To erase that storage after uninstalling, stop Home Assistant and remove only its exact matching file from `.storage`; keep a backup and never delete the directory. Reinstalling normally creates a new config entry and does not recover a removed entry's history.

## Publishing

1. Run tests and review the exact tracked files for household data and secrets.
2. Run the hassfest workflow and review results.
3. Keep the first release marked **prerelease**; record untested runtime steps.
4. Verify installation as a Marketplace/HACS custom repository on a test instance.
5. Provide branding through the supported Home Assistant brands process and run the full HACS repository validation.
6. When the requirements are met, propose the repository to `hacs/default` using its contribution rules. Catalog acceptance is up to its maintainers.

Do not claim default Marketplace discoverability while this submission is pending or absent. A successful custom repository download does not mean catalog approval.

References: [Marketplace](https://contributors.home-assistant.io/marketplace/), [integration repository requirements](https://www.hacs.dev/docs/publish/integration/), [catalog inclusion](https://www.hacs.dev/docs/publish/include/).
