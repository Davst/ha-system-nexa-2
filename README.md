# System Nexa 2 for Home Assistant

Custom component for System Nexa 2 support in Home Assistant.

## Features
- **Local Control**: Control your devices via the local network (no cloud required).
- **Websocket Support**: Real-time state updates (critical for devices like WPD-01 with physical buttons).
- **Discovery**: Automatically discovers devices on your network.
- **Dimmers**: Full support for dimming capabilities.

## Installation

### HACS (Recommended)
1. Add this repository as a **Custom Repository** in HACS.
2. Search for "System Nexa 2" and click Download.
3. Restart Home Assistant.

### Manual
1. Copy the `custom_components/system_nexa_2` folder to your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.

## Configuration
1. Go to **Settings** > **Devices & Services**.
2. If your device is discovered, click **Configure**.
3. Otherwise, click **Add Integration** and search for "System Nexa 2".
4. Enter your **API Token**.

## Supported Devices
- Nexa WPD-01 (Dimmer)
- Other System Nexa 2 receivers (Generic support)
