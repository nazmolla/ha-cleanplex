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
| Active streams, Filtered streams | sensors | Plex streams now playing, and how many currently have a filter that applies. The `streams` attribute lists user, title, client and filter state |
| Skips total, Skips (24 h), False positives | sensors | How many filter actions Cleanplex has performed, and how many detections were marked as false positives |
| Last skip | timestamp sensor | When the latest skip or mute happened; attributes hold title, user, client and category |
| Filter action | event | Fires once for every new skip or mute (`skip` or `mute`), with title, user, client and category, for automations |

## Install

1. Home Assistant 2026.11 or newer: **Settings → Marketplace → Add from link**, enter `https://github.com/nazmolla/ha-cleanplex`, and install **Cleanplex**. (This needs the Marketplace's one-time GitHub device sign-in; it only reads public data.) Older versions: HACS, three-dot menu, **Custom repositories**, category **Integration**.
2. Enter the address of the Cleanplex web UI when the setup opens, for example `http://192.168.0.80:7979`. If it does not open, use **Settings → Devices & services → Add integration → Cleanplex**.

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

Tell me when a filter acts:

```yaml
automation:
  - alias: Notify when Cleanplex skips something
    triggers:
      - trigger: state
        entity_id: event.cleanplex_filter_action
    conditions:
      - condition: template
        value_template: "{{ trigger.to_state.state not in ['unknown', 'unavailable'] }}"
    actions:
      - action: notify.notify
        data:
          message: >
            {{ trigger.to_state.attributes.event_type | capitalize }}:
            {{ trigger.to_state.attributes.title }} for {{ trigger.to_state.attributes.user }}
            ({{ trigger.to_state.attributes.category }})
```

The integration needs a Cleanplex that has the skip history endpoints (any recent version); with an older one the skip sensors stay at zero and the rest keeps working.

## Development

```bash
pip install pytest-homeassistant-custom-component
pytest
```
