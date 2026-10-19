# HotSpotTunnel - iOS Companion App

A modern SwiftUI iOS application that shares your iPhone's cellular data connection with your Windows PC over a USB cable using **Apple's USB Multiplexing Protocol (`usbmuxd`)**.

---

## 🌟 Why This Approach is Superior

1. **No Ethernet Driver Required on Windows**: Communicates through Apple's standard USB multiplexer protocol (`usbmuxd`). You don't need `netaapl64.inf` installed on Windows.
2. **Works on ANY Mobile Carrier**: Bypasses carrier-enforced Personal Hotspot blocks (since traffic routes through the app's standard cellular socket).
3. **Low Latency & High Speed**: Direct hardware USB connection (up to 480 Mbps on Lightning, up to 10 Gbps on USB-C iPhone 15/16 Pro).
4. **Keeps Running in Background**: Uses an inaudible background audio loop to keep the proxy socket alive even when your iPhone screen is turned off or locked.

---

## 📱 How to Install on Your iPhone

You can install this app on your iPhone using either **Xcode** (free) or **Sideloading** (AltStore / SideStore / Sideloadly):

### Method 1: Via Xcode (Mac)
1. Open the `ios/` folder or import into Xcode as an iOS App project.
2. Select your iPhone as the build target in Xcode.
3. In **Signing & Capabilities**:
   - Check **Automatically manage signing**.
   - Select your personal Team (a free Apple ID works fine).
4. Click **Run** (Cmd + R) to install onto your iPhone.
5. On your iPhone: Go to **Settings → General → VPN & Device Management** and tap **Trust** for your Developer App certificate.

### Method 2: Sideloading (Windows or Mac via Sideloadly / AltStore)
1. If you don't have a Mac, you can build or export the `.ipa` using open-source tools or CI (GitHub Actions).
2. Install [Sideloadly](https://sideloadly.io/) or [AltStore](https://altstore.io/) on Windows.
3. Sign and install the app onto your iPhone with your Apple ID.

---

## 🚀 How to Use

1. Connect your iPhone to your Windows PC using an original or MFi USB cable.
2. If prompted on your iPhone, tap **"Trust This Computer"** and enter your passcode.
3. Open **HotSpot Tunnel** on your iPhone and tap **"Start Tethering"**.
4. Open **HotSpotApp** on Windows, switch to **"USB Tunnel Mode"**, and click **"Enable USB Internet Tunnel"**.
5. All Windows browsers, games, and applications will instantly route internet through the USB cable!
