# Home Assistant Online / Offline Devices

Find offline devices across your Home Assistant home, keep a dashboard up to date automatically, and receive optional notifications when availability changes.

[Český návod](README.cs.md) · [Notification blueprint](blueprints/availability_notifications.yaml) · [Dashboard](dashboards/device-availability.yaml)

**0.1.0 beta · targets Home Assistant 2026.11+ · custom integration · local processing**

This integration reads the availability your existing integrations report. It covers Wi-Fi, Zigbee, Bluetooth and other devices registered in Home Assistant, without maintaining a list of entity IDs. Device names, areas, additions and removals update automatically within about a minute.

## What you get

- One row per monitored device registry entry, even when the device has many entities.
- A native dashboard showing confirmed outages, uncertain states, all devices and exceptions.
- Exclusions managed through a Home Assistant label, including intentionally switched-off devices.
- One persistent switch controlling availability notifications for all monitored integrations.
- One notification event for changes in the same scan, without repeating an ongoing incident every minute.
- A configurable confirmation delay (five minutes by default) and five minutes of settling time after startup or reload.
- Separate handling for each Zigbee2MQTT bridge, so a failed bridge does not report every child as an independent failure.

The supplied dashboard uses standard cards. No custom frontend cards, cloud account, API token, network scan or runtime Python dependencies are required.

## Installation

### Marketplace / HACS custom repository

This project is **not yet included in the default catalog**. Searching for it will not find it until a catalog submission has been accepted. Home Assistant 2026.11 includes the former HACS experience in **Settings → Marketplace**. See the [official Marketplace guide](https://www.home-assistant.io/integrations/marketplace).

1. Add `https://github.com/PetrMlejnek/home-assistant-offline-devices` as a custom repository, type **Integration**. In older HACS installations the custom repository menu is under the three-dot menu.
2. Download the integration. For a beta release, enable prerelease versions if your client requires it.
3. Restart Home Assistant.
4. Go to **Settings → Devices & services → Add integration**, then search for **Online / Offline Devices**.
5. Choose an existing exclusion label, or leave it blank to create **Do not monitor availability**. Set the outage confirmation time in seconds.

The first version has unit tests for the availability rules and artifact checks. Compatibility with every integration or hardware combination has not been established. Validate the inventory in your home before turning notifications on.

### Manual installation

Copy `custom_components/offline_devices` into your Home Assistant `config/custom_components` directory, restart, and follow steps 4–5 above. Do not copy private configuration files into this repository.

## Add the dashboard

1. Create a new empty dashboard under **Settings → Dashboards**. Use URL path `device-availability`.
2. Open it, enter edit mode, and open the **Raw configuration editor**. Replace its configuration with [dashboards/device-availability.yaml](dashboards/device-availability.yaml).
3. Confirm that `sensor.offline_devices` and `switch.offline_devices_notifications` exist. If Home Assistant appended a suffix due to a name collision, or you rename these two entities, update their references in the dashboard.

The dashboard and optional blueprint are installed separately from the integration. Updating the integration through Marketplace does not overwrite your dashboard or automation. Names of your household devices can be changed freely; their registry IDs are used internally.

## Manage exceptions

Apply the selected label to a **device** under Settings → Devices & services. It moves to the Exclusions view on the next scan. Remove the label to resume monitoring. Renaming the label is safe because the integration stores its ID.

You can select your existing label, such as **Nehlídat dostupnost**, during setup. Existing device assignments remain in place. A label on an **entity** excludes only that entity from the evidence used for its device. Labels on areas are not inherited.

Disabled devices, disabled/hidden entities and service devices are skipped by default. Recognized Zigbee2MQTT bridges remain monitored infrastructure. A device with no enabled, visible operational entities is omitted unless explicitly labeled as an exception.

If you delete the selected label, the dashboard displays a warning and notification events pause. Select a valid label in the integration's options to resume. Review phones, televisions, seasonal equipment, virtual devices and other things that are intentionally unavailable before enabling alerts.

## Optional mobile notifications

Notifications start **off** and the switch restores its previous setting after restart. The integration sends local Home Assistant events; it never picks a recipient automatically.

1. Copy [availability_notifications.yaml](blueprints/availability_notifications.yaml) to `config/blueprints/automation/offline_devices/availability_notifications.yaml`, or import its GitHub URL using the blueprint import UI after the repository is published.
2. Create **one** automation from the blueprint.
3. In **Notification actions**, choose your mobile notification action. Set the title to `{{ notification_title }}` and the message to `{{ notification_message }}`. You can customize the language or use the device lists in your own template.
4. Check the selected notifications switch and set the dashboard path if you used a different URL.
5. Turn on **Mobile notifications** on the dashboard.

Example notification action (replace the placeholder service with your actual mobile app action):

```yaml
action: notify.mobile_app_your_phone
data:
  title: "{{ notification_title }}"
  message: "{{ notification_message }}"
  data:
    url: "{{ dashboard_path }}"
    clickAction: "{{ dashboard_path }}"
```

Available variables: `notification_title`, `notification_message`, `offline_devices`, `recovered_devices`, and `dashboard_path`. Each device row contains `id`, `name`, `area`, `integrations`, `status`, `since`, and `incident`.

Changes in the same scan produce one summary. Confirmed offline incidents and later recoveries are reported once per observed transition. Unknown and bridge-blocked periods do not split an incident. Renaming, removing or excluding a device does not generate a message. First discovery is silent; startup-pending devices can produce a new outage after the settling period.

Monitoring continues while notifications are off. Turning them on does not replay existing outages. A later recovery can still be reported for an outage observed while notifications were off. Recovery during startup is silent. Disable earlier availability automations if they overlap; two automations or two chosen notification actions can intentionally send two messages. There is no delivery acknowledgement or retry queue for a failed notification service.

## How availability is decided

| Status | Meaning |
| --- | --- |
| `online` | At least one connectivity sensor is on, or an operational entity has a known state. A switch/light being `off` is online. |
| `pending` | All relevant states indicate an outage, but confirmation or startup settling is still in progress. |
| `offline` | Explicit connectivity is off/unavailable, or all operational entities are unavailable, for the configured delay. |
| `unknown` | The integration does not have enough information to confirm availability. |
| `blocked` | The device's own Zigbee2MQTT parent bridge is unavailable or has unknown connectivity. |
| `excluded` | The device has the selected exclusion label. |

Explicit `binary_sensor` connectivity states take precedence over other values. Otherwise operational domains include sensors, lights, switches, covers, climate, cameras, media players, locks, fans, vacuums and related actuators. Buttons, updates, configuration numbers and trackers are not availability evidence. A partially unavailable device is not marked wholly offline while another operational entity is still available.

## Limits

- This is an availability view of Home Assistant data, not an independent ping or radio monitor. If an integration retains a stale value and never reports `unavailable`, the device can still look online. Enable device availability in the upstream integration where supported. Sleeping battery devices are not declared offline merely because they have not changed recently.
- Zigbee2MQTT parent suppression requires its normal device registry parent link and bridge connectivity entity. ZHA and other hubs currently use the ordinary availability rules; parent suppression is not inferred from names.
- One physical product can have multiple device registry entries. These remain separate; unrelated devices behind a gateway are not merged.
- A minute polling interval adds up to about one minute to the configured confirmation delay. A complete Home Assistant/server/network failure cannot be reported by this integration running inside that same server.
- Incident state is stored locally in Home Assistant's `.storage` directory, with a short delayed save and normal shutdown persistence. An abrupt crash before persistence, removal/reinstallation or lost storage can lose incident history. Notification delivery is not an exactly-once transport guarantee.
- The sensor has a device-list attribute. Very large installations should assess recorder/database growth and template rendering performance. No device inventory is sent by the integration to GitHub or a third party. Your chosen notification action determines where alert contents go.

## Update or remove

Update the custom integration in Marketplace/HACS and restart. Existing labels, device label assignments and the notification switch are preserved. To change options, use the integration's configuration menu; this reloads the monitor with a settling period.

To remove it, delete the integration entry, remove its dashboard/notification automation if no longer wanted, and uninstall its files through Marketplace/HACS. The shared label and assignments are intentionally left intact. Local incident storage is also retained; see [maintenance notes](docs/MAINTENANCE.md) if you need to remove it.

## Development and distribution

```sh
python -m pip install -r requirements-test.txt
python -m unittest discover -s tests -v
```

Tests use synthetic devices and read the actual shipped templates. They cover classification, incident transitions, multiple bridges and artifact parsing. They do not replace an actual Home Assistant setup/unload test. CI also runs Home Assistant's hassfest manifest/config checks.

Marketplace catalog inclusion requires a public repository, validation and review; see [publisher requirements](https://www.hacs.dev/docs/publish/include/). Installation as a custom repository and acceptance into the searchable catalog are separate steps. See the [release checklist](docs/MAINTENANCE.md).

Licensed under [MIT](LICENSE). This is an independent community project, not an official Home Assistant integration.
