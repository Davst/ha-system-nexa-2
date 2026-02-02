# System Nexa 2 (Early Alpha)

> [!CAUTION]
> **EXPERIMENTAL / DO NOT USE**
> This integration is currently in early alpha and under active development. It is **not ready for public use**. Breaking changes may occur at any time.

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


## Prerequisites & Device Setup
Before configuring this integration in Home Assistant, your Nexa device must be connected to your local network.

1.  **Power on** your System Nexa 2 device.
2.  **Connect to WiFi**: Follow the manufacturer instructions to connect the device to your WiFi network.
3.  **Find IP Address**: Check your router's client list to find the IP address of the device (this will be the **Host**).
4.  **Get Token**: Locate the API Token for your device. This is often found on a sticker on the device, in the official mobile app, or in the device's web interface (http://<device-ip>:3000).

## Configuration
1. Go to **Settings** > **Devices & Services**.
2. If your device is discovered, click **Configure**.
3. Otherwise, click **Add Integration** and search for "System Nexa 2".
4. Enter your **API Token**.

## Supported Devices
- Nexa WPD-01 (Dimmer)
- Other System Nexa 2 receivers (Generic support)
