# Project instructions

- Keep this a single, local-only Home Assistant integration (`offline_devices`).
- Never commit household inventories, device IDs, URLs, credentials, or real screenshots.
- Use synthetic fixtures. Keep availability classification and incident transitions in `engine.py`, independent of Home Assistant.
- Update the English and Czech guides when changing installation or user-visible behavior.
- Run `python -m unittest discover -s tests -v` before delivery. Do not claim an actual Home Assistant startup or Marketplace approval from unit tests.
- Preserve exclusions and notification state across reloads. Do not send notifications during tests.
