# STB-Proxy Home Assistant Integration

[![HACS Custom Repository](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A full-featured custom Home Assistant integration for [STB-Proxy](https://github.com/gregfroese/STB-Proxy).

STB-Proxy bridges Stalker portal streams to M3U players, Plex DVR, and Jellyfin. This integration connects directly to the native REST API provided by STB-Proxy, exposing full interactive control of channel blocks, live streaming activity, media server sync, and health status directly within Home Assistant.

---

## ✨ Features

- **Simple UI Setup (Config Flow)**: Connect in seconds by providing only your **STB-Proxy host address** and **API key**.
- **Channel Block Switches**: Control channel availability on the fly. Each channel block created in STB-Proxy is represented as a toggleable switch entity in Home Assistant, complete with channel count attributes.
- **Dynamic Block Discovery**: New channel blocks created in STB-Proxy are automatically discovered and added to Home Assistant without needing to restart.
- **Media Server Sync**:
  - **Button**: Trigger an immediate lineup synchronization with Plex and Jellyfin directly from your dashboards.
  - **Sensors & Health**: Monitor sync status, timestamp, and receive alerts if synchronization fails.
- **Live Stream & Lineup Monitoring**:
  - Track current active streams in real-time.
  - Monitor total channel lineup count.
  - Detect concurrent logins or physical STB box usage.
- **Dedicated Services**: Custom services (`stb_proxy.sync` and `stb_proxy.set_block`) for flexible automation design.

---

## 📦 Exposed Entities

### 🔌 Switches
| Entity | Description | Extra Attributes |
|---|---|---|
| `switch.block_<name>` | Toggles a specific Channel Block on/off | `block_name`, `channels`, `dead_channels` |

### 📊 Sensors
| Entity | Description | Units |
|---|---|---|
| `sensor.active_streams` | Number of streams currently active | `streams` |
| `sensor.available_channels` | Total channels available in the active lineup | `channels` |
| `sensor.other_logins` | Count of active external logins on portal accounts | `logins` |
| `sensor.plex_sync_time` | Timestamp of the last successful Plex sync *(if configured)* | — |
| `sensor.plex_sync_status` | Detailed status message from Plex sync *(if configured)* | — |
| `sensor.jellyfin_sync_time` | Timestamp of the last successful Jellyfin sync *(if configured)* | — |
| `sensor.jellyfin_sync_status` | Detailed status message from Jellyfin sync *(if configured)* | — |

### 🚨 Binary Sensors
| Entity | Device Class | Description |
|---|---|---|
| `binary_sensor.box_active` | `running` | Indicates if a physical STB box is currently active |
| `binary_sensor.plex_problem` | `problem` | Turns ON if the latest Plex synchronization reported an error |
| `binary_sensor.jellyfin_problem` | `problem` | Turns ON if the latest Jellyfin synchronization reported an error |

### 🔘 Buttons
| Entity | Description |
|---|---|
| `button.sync_media_servers` | Triggers immediate sync with Plex and Jellyfin |

---

## 🚀 Installation

### Option 1: HACS (Recommended)

1. Ensure [HACS](https://hacs.xyz) is installed.
2. In Home Assistant, open **HACS** > **Integrations** > Three dots menu (top right) > **Custom repositories**.
3. Add the repository URL:
   ```text
   ssh://git@gitea:222/stevewiebe/stb-proxy-ha.git
   ```
   *(or your HTTP/HTTPS Gitea repository URL)* with category **Integration**.
4. Click **Download** on the STB-Proxy integration card.
5. Restart Home Assistant.

### Option 2: Manual Installation

1. Copy the `custom_components/stb_proxy` directory into your Home Assistant `<config_dir>/custom_components/` directory:
   ```bash
   cp -r custom_components/stb_proxy /path/to/homeassistant/config/custom_components/
   ```
2. Restart Home Assistant.

---

## ⚙️ Configuration

1. In the STB-Proxy web UI, open **Settings** and locate the **API token**. If empty, one will be automatically generated, or you can click **New** to create one.
2. In Home Assistant, go to **Settings** > **Devices & Services** > **Add Integration**.
3. Search for **STB-Proxy**.
4. Enter your connection details:
   - **Host URL / Address**: e.g. `http://192.168.1.50:8001` or `192.168.1.50:8001`
   - **API Token / Key**: Paste the token from STB-Proxy Settings.
5. Click **Submit**.

---

## 🛠️ Services

### `stb_proxy.sync`
Triggers immediate synchronization with configured media servers (Plex and Jellyfin).

```yaml
service: stb_proxy.sync
```

### `stb_proxy.set_block`
Enables or disables a channel block by name.

```yaml
service: stb_proxy.set_block
data:
  block_name: "Sports"
  enabled: true
```

---

## 💡 Automation Examples

### 1. Enable Sports Channels Automatically During Game Time
```yaml
alias: "Enable Sports Channels on Weekends"
trigger:
  - platform: time
    at: "12:00:00"
condition:
  - condition: time
    weekday:
      - sat
      - sun
action:
  - service: switch.turn_on
    target:
      entity_id: switch.block_sports
```

### 2. Turn Off Non-Essential Channels When Leaving Home
```yaml
alias: "Disable Premium Channel Blocks Away"
trigger:
  - platform: state
    entity_id: zone.home
    to: "0"
action:
  - service: switch.turn_off
    target:
      entity_id:
        - switch.block_movies
        - switch.block_sports
```

### 3. Notify When a Physical STB Box Turns On
```yaml
alias: "STB Box Active Alert"
trigger:
  - platform: state
    entity_id: binary_sensor.box_active
    to: "on"
action:
  - service: notify.persistent_notification
    data:
      title: "STB Box Active"
      message: "A physical STB box has connected to the portal. Stream slots may be shared."
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
