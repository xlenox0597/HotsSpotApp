# Apple USB HotSpot & Tunnel Manager

An all-in-one cross-platform solution to share internet from an Apple device (iPhone / iPad) to a Windows PC or laptop via a USB cable.

Supports **two distinct operating modes**:
1. 📱 **USB Tunnel Mode (iPhone App)**: Connects to our custom iOS app over Apple's USB multiplexer protocol (`usbmuxd`). **Requires NO network drivers on Windows** and **bypasses carrier-enforced Personal Hotspot restrictions**.
2. ⚡ **Native Hotspot Mode (WHQL Drivers)**: For traditional Apple Personal Hotspot tethering, with official Microsoft WHQL-signed Apple Ethernet drivers (`netaapl64.inf` and `AppleUsb.inf`) bundled out-of-the-box.

---

## 🌟 Architecture Overview

```
+-------------------------------------------------------------------------------+
|                                  iPHONE                                       |
|                                                                               |
|  +-------------------------------------------------------------------------+  |
|  |                    HotSpotTunnel (SwiftUI App)                          |  |
|  |  - One-tap "Start Tethering" switch                                     |  |
|  |  - Inaudible background audio loop to keep socket alive when locked     |  |
|  |  - Asynchronous HTTP CONNECT / SOCKS proxy on 127.0.0.1:8080            |  |
|  |  - Real-time telemetry: upload/download speeds & byte meters            |  |
|  +------------------------------------+------------------------------------+  |
+---------------------------------------|---------------------------------------+
                                        | (Lightning / USB-C Cable)
                                        | Apple usbmuxd multiplexer protocol
+---------------------------------------|---------------------------------------+
|                                       v                                       |
|  +------------------------------------+------------------------------------+  |
|  |                           WINDOWS PC                                    |  |
|  |                                                                         |  |
|  |  [USB Multiplexer Tunnel] (src/usbmux_tunnel.py)                        |  |
|  |    - Communicates with Apple usbmuxd (port 27015)                       |  |
|  |    - Forwards local PC port 127.0.0.1:8080 to iPhone:8080 over USB cable|  |
|  |                                                                         |  |
|  |  [Windows Proxy Manager] (src/proxy_manager.py)                         |  |
|  |    - Automatically configures Windows System Proxy to 127.0.0.1:8080    |  |
|  |    - All browsers, games, Discord, and system apps route to USB         |  |
|  |    - Automatically reverts previous proxy settings when stopped         |  |
|  +-------------------------------------------------------------------------+  |
+-------------------------------------------------------------------------------+
```

---

## 🚀 Quick Start

### Option B: USB Tunnel Mode (Recommended)

1. **Install the iOS App on your iPhone**:
   - The complete Swift source is located in [`ios/HotSpotTunnel`](ios/HotSpotTunnel).
   - Open in Xcode or sign with AltStore / Sideloadly (see [`ios/README.md`](ios/README.md)).
   - Tap **"Start Tethering"** in the iPhone app.
2. **Connect your iPhone to Windows via USB cable**.
   - If prompted on your iPhone, tap **"Trust This Computer"** and enter your passcode.
3. **Launch the Windows App**:
   - Run `python main.py` or launch `dist\HotSpotManager\HotSpotManager.exe`.
   - On the **"📱 USB Tunnel (iPhone App)"** tab, click **"Start USB Internet Tunnel"**.
   - **Done!** Windows will route all internet traffic through the cable.

---

### Option A: Native Hotspot Mode (Traditional Driver Tethering)

If you prefer using Apple's built-in **Settings → Personal Hotspot**:
1. The app includes official Microsoft WHQL-signed drivers in [`drivers/`](drivers/):
   - `appleusb/`: Apple USB composite driver
   - `netaapl64/`: Apple Mobile Device Ethernet driver
2. Open the **"⚡ Native Hotspot (Drivers)"** tab and click **"Install Drivers Now"** (elevates UAC automatically).
3. Connect your cable and turn ON **Personal Hotspot → Allow Others to Join** on your iPhone.
4. The virtual adapter will activate and acquire an IP address (`172.20.10.x`).

---

## 🛠️ Building the Standalone Executable (.exe)

```powershell
python build.py
```
Executable output: `dist\HotSpotManager\HotSpotManager.exe`

---

## 📦 Building the Windows Installer

Compile [`installer/inno_setup.iss`](installer/inno_setup.iss) with Inno Setup to generate `HotSpotApp_Setup.exe`.

---

## 📁 Repository Structure

```
HotsSpotApp/
├── ios/
│   ├── HotSpotTunnel/
│   │   ├── HotSpotTunnelApp.swift     # SwiftUI app lifecycle
│   │   ├── Models/TunnelState.swift   # Live speed & data transfer telemetry
│   │   ├── Views/ContentView.swift    # Modern SwiftUI interface
│   │   ├── Proxy/ProxyServer.swift    # Network.framework HTTP CONNECT proxy engine
│   │   ├── Proxy/BackgroundKeepAlive.swift # Background keep-alive engine
│   │   └── Info.plist                 # Background modes & network permissions
│   └── README.md                      # Detailed iOS install & sideloading guide
├── drivers/                           # Official Microsoft WHQL-signed Apple drivers
│   ├── appleusb/                      # Apple USB composite driver
│   └── netaapl64/                     # Apple Mobile Device Ethernet driver
├── src/
│   ├── usbmux_tunnel.py               # Pure-Python usbmuxd port forwarder
│   ├── proxy_manager.py               # Windows system proxy manager (WinINet API)
│   ├── driver_manager.py              # DriverStore checker & elevated pnputil installer
│   ├── device_detector.py             # PnP device detector (Vendor ID 05AC)
│   ├── network_manager.py             # NDIS adapter monitor & diagnostics
│   └── ui.py                          # Dual-mode CustomTkinter user interface
├── installer/
│   ├── install_drivers.bat            # Standalone elevated driver installer
│   └── inno_setup.iss                 # Inno Setup wizard compiler script
├── main.py                            # Application entry point
├── build.py                           # Standalone executable compiler
├── requirements.txt                   # Python dependencies
└── README.md
```
