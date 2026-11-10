# Cleanplex for Home Assistant

Shows [Cleanplex](https://github.com/nazmolla/Cleanplex) status in Home Assistant and lets you pause or resume its library scanning. It polls Cleanplex's own web API every 30 seconds; nothing needs to be changed on the Cleanplex server.

## Entities

| Entity | Type | What it shows |
|---|---|---|
| Scanner | switch | On while scanning may run; turn it off to pause (for example while someone is watching) |
| Scanning | binary sensor | A title is being scanned now |
| Plex connection | binary sensor | Cleanplex can reach Plex |
| Front door | binary sensor | Stream filtering for every client is on |
| Scan queue, Scan progress, Scanning title, Active scan workers | sensors | The scanner's current work |
| Titles scanned / waiting / failed | sensors | Library scan counts |
| Active streams, Filtered streams | sensors | Plex streams now playing, and how many currently have a filter that applies |

## Install

1. In HACS, open the three-dot menu, choose **Custom repositories**, add `https://github.com/nazmolla/ha-cleanplex` as category **Integration**, then install **Cleanplex** and restart Home Assistant.
2. **Settings → Devices & services → Add integration → Cleanplex**, and enter the address of the Cleanplex web UI, for example `http://192.168.0.80:7979`.

Manual install: copy `custom_components/cleanplex` into your Home Assistant `custom_components` folder.

## Example automation

Pause scanning while a stream is playing, so scans do not compete with playback:

```yaml
automation:
  - alias: Pause Cleanplex scans while streaming
    triggers:
      - trigger: numeric_state
        entity_id: sensor.cleanplex_active_streams
        above: 0
    actions:
      - action: switch.turn_off
        target: { entity_id: switch.cleanplex_scanner }
```

## Development

```bash
pip install pytest-homeassistant-custom-component
pytest
```
