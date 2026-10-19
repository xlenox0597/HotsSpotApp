"""
HotSpotApp User Interface
Features Dual-Mode Operation:
1. USB Tunnel Mode (Uses iPhone App + usbmuxd, NO drivers required, bypasses carrier hotspot blocks)
2. Native Hotspot Mode (Uses official Apple WHQL drivers + Personal Hotspot)
"""

import sys
import threading
import time
import customtkinter as ctk
from tkinter import messagebox

from src.driver_manager import (
    check_driver_store,
    is_admin,
    install_drivers,
    run_as_admin
)
from src.device_detector import is_apple_device_connected
from src.network_manager import (
    get_network_overview,
    restart_apple_adapter,
    flush_dns_and_renew_dhcp
)
from src.proxy_manager import WindowsProxyManager
from src.usbmux_tunnel import UsbmuxTunnel


class HotSpotAppUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Apple USB HotSpot & Tunnel Manager")
        self.geometry("740x740")
        self.minsize(680, 650)

        # Theme settings
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.running = True
        self.tunnel = UsbmuxTunnel(local_port=8080, remote_port=8080)
        self.tunnel_active = False

        self._build_ui()

        # Start live background polling
        self.monitor_thread = threading.Thread(target=self._poll_status, daemon=True)
        self.monitor_thread.start()

    def _build_ui(self):
        # Header
        self.header_frame = ctk.CTkFrame(self, corner_radius=12, fg_color=("gray85", "#1c1c1e"))
        self.header_frame.pack(fill="x", padx=20, pady=(15, 10))

        title_lbl = ctk.CTkLabel(
            self.header_frame,
            text="Apple USB Internet Manager",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        title_lbl.pack(anchor="w", padx=20, pady=(15, 2))

        sub_lbl = ctk.CTkLabel(
            self.header_frame,
            text="Share iPhone Internet to Windows over USB cable via iPhone App Tunnel or Native Hotspot",
            font=ctk.CTkFont(size=13),
            text_color="gray"
        )
        sub_lbl.pack(anchor="w", padx=20, pady=(0, 15))

        # Tabview for Modes
        self.tabview = ctk.CTkTabview(self, corner_radius=12)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=5)

        self.tab_tunnel = self.tabview.add("📱 USB Tunnel (iPhone App)")
        self.tab_native = self.tabview.add("⚡ Native Hotspot (Drivers)")

        self._build_tunnel_tab()
        self._build_native_tab()

    # =========================================================================
    # TAB 1: USB Tunnel Mode (Option B - iPhone App + usbmuxd)
    # =========================================================================
    def _build_tunnel_tab(self):
        scroll = ctk.CTkScrollableFrame(self.tab_tunnel, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=5, pady=5)

        # Big Action Card
        card_main = self._create_card(
            scroll,
            title="USB Tunnel Control",
            desc="Connects to the HotSpotTunnel app on your iPhone over standard USB cable."
        )

        self.lbl_tunnel_status = ctk.CTkLabel(
            card_main,
            text="Tunnel: Inactive (Proxy Disabled)",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#FF9500"
        )
        self.lbl_tunnel_status.pack(anchor="w", padx=20, pady=(2, 8))

        self.btn_toggle_tunnel = ctk.CTkButton(
            card_main,
            text="Start USB Internet Tunnel",
            command=self._on_toggle_tunnel,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color="#007AFF",
            hover_color="#0051A8",
            height=44,
            width=260
        )
        self.btn_toggle_tunnel.pack(anchor="w", padx=20, pady=(0, 15))

        # Live Metrics Card
        card_metrics = self._create_card(
            scroll,
            title="Live Connection Telemetry",
            desc="Real-time traffic routed through the USB cable."
        )

        self.lbl_metrics_data = ctk.CTkLabel(
            card_metrics,
            text="Sent: 0 KB | Received: 0 KB | Active Connections: 0",
            font=ctk.CTkFont(size=14, weight="medium")
        )
        self.lbl_metrics_data.pack(anchor="w", padx=20, pady=(2, 6))

        self.lbl_proxy_info = ctk.CTkLabel(
            card_metrics,
            text="Windows System Proxy: Inactive",
            font=ctk.CTkFont(size=13),
            text_color="gray"
        )
        self.lbl_proxy_info.pack(anchor="w", padx=20, pady=(0, 15))

        # Setup Instructions Card
        card_guide = self._create_card(
            scroll,
            title="iPhone App Setup Steps",
            desc="Simple 3-step setup on your Apple device."
        )

        steps = [
            "1. Connect your iPhone to this PC using an original or MFi USB cable.",
            "2. Unlock your iPhone, tap 'Trust This Computer', and enter your passcode.",
            "3. Open the 'HotSpot Tunnel' app on your iPhone and tap 'Start Tethering'.",
            "4. Click 'Start USB Internet Tunnel' above."
        ]
        for step in steps:
            lbl = ctk.CTkLabel(card_guide, text=step, font=ctk.CTkFont(size=13), anchor="w")
            lbl.pack(anchor="w", padx=20, pady=2)

        lbl_spacing = ctk.CTkLabel(card_guide, text="", height=8)
        lbl_spacing.pack()

    def _on_toggle_tunnel(self):
        if not self.tunnel_active:
            # Start tunnel
            ok = self.tunnel.start()
            if ok:
                WindowsProxyManager.enable_proxy(host="127.0.0.1", port=8080)
                self.tunnel_active = True
                self.btn_toggle_tunnel.configure(text="Stop USB Internet Tunnel", fg_color="#FF3B30", hover_color="#C0261D")
                self.lbl_tunnel_status.configure(text="✔ Tunnel Active (Proxy Enabled: 127.0.0.1:8080)", text_color="#34C759")
                self.lbl_proxy_info.configure(text="Windows System Proxy: Active (All apps routed to USB)", text_color="#34C759")
            else:
                messagebox.showerror("Error", "Could not connect to USB multiplexer (usbmuxd). Ensure Apple USB cable is plugged in.")
        else:
            # Stop tunnel
            self.tunnel.stop()
            WindowsProxyManager.disable_proxy()
            self.tunnel_active = False
            self.btn_toggle_tunnel.configure(text="Start USB Internet Tunnel", fg_color="#007AFF", hover_color="#0051A8")
            self.lbl_tunnel_status.configure(text="Tunnel: Inactive (Proxy Disabled)", text_color="#FF9500")
            self.lbl_proxy_info.configure(text="Windows System Proxy: Inactive", text_color="gray")

    # =========================================================================
    # TAB 2: Native Hotspot Mode (Option A - Driver + Personal Hotspot)
    # =========================================================================
    def _build_native_tab(self):
        scroll = ctk.CTkScrollableFrame(self.tab_native, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=5, pady=5)

        # Drivers Card
        card_drivers = self._create_card(
            scroll,
            title="1. Apple Driver Status",
            desc="Required by Windows for virtual Ethernet tethering."
        )
        self.lbl_drivers_status = ctk.CTkLabel(
            card_drivers,
            text="Checking drivers...",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.lbl_drivers_status.pack(anchor="w", padx=20, pady=(2, 5))

        self.btn_install_drivers = ctk.CTkButton(
            card_drivers,
            text="Install / Repair Drivers",
            command=self._on_install_drivers,
            fg_color="#007AFF",
            hover_color="#0051A8",
            width=180
        )
        self.btn_install_drivers.pack(anchor="w", padx=20, pady=(0, 15))

        # Device Card
        card_device = self._create_card(
            scroll,
            title="2. Apple Device Connection",
            desc="Plug your iPhone or iPad using an original USB cable."
        )
        self.lbl_device_status = ctk.CTkLabel(
            card_device,
            text="Searching for connected Apple devices...",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.lbl_device_status.pack(anchor="w", padx=20, pady=(2, 5))

        # Network Card
        card_network = self._create_card(
            scroll,
            title="3. USB Tethering & Network Adapter",
            desc="Monitors Apple Mobile Device Ethernet adapter and DHCP leases."
        )
        self.lbl_network_status = ctk.CTkLabel(
            card_network,
            text="Waiting for Apple network adapter...",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.lbl_network_status.pack(anchor="w", padx=20, pady=(2, 5))

        self.lbl_network_details = ctk.CTkLabel(
            card_network,
            text="IP: -- | Gateway: --",
            font=ctk.CTkFont(size=13)
        )
        self.lbl_network_details.pack(anchor="w", padx=20, pady=(0, 5))

        # Diagnostics Row
        card_diag = self._create_card(
            scroll,
            title="Diagnostics & Network Tools",
            desc="Quick fixes if connection stalls."
        )
        btn_row = ctk.CTkFrame(card_diag, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(2, 15))

        btn_restart = ctk.CTkButton(
            btn_row,
            text="Restart Adapter",
            command=self._on_restart_adapter,
            width=140
        )
        btn_restart.pack(side="left", padx=(0, 10))

        btn_renew = ctk.CTkButton(
            btn_row,
            text="Renew IP / Flush DNS",
            command=self._on_renew_ip,
            width=160
        )
        btn_renew.pack(side="left")

    def _create_card(self, parent, title: str, desc: str):
        card = ctk.CTkFrame(parent, corner_radius=10, fg_color=("gray90", "#2c2c2e"))
        card.pack(fill="x", pady=6)

        t_lbl = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=15, weight="bold"))
        t_lbl.pack(anchor="w", padx=20, pady=(12, 2))

        d_lbl = ctk.CTkLabel(card, text=desc, font=ctk.CTkFont(size=12), text_color="gray")
        d_lbl.pack(anchor="w", padx=20, pady=(0, 8))

        return card

    # =========================================================================
    # Polling & Updates
    # =========================================================================
    def _poll_status(self):
        while self.running:
            try:
                self._update_all_status()
            except Exception as e:
                print(f"Error in status poll: {e}")
            time.sleep(2)

    def _update_all_status(self):
        # Telemetry for USB Tunnel
        if self.tunnel_active:
            sent_mb = self.tunnel.total_bytes_sent / (1024 * 1024)
            recv_mb = self.tunnel.total_bytes_received / (1024 * 1024)
            self.lbl_metrics_data.configure(
                text=f"Sent: {sent_mb:.2f} MB | Received: {recv_mb:.2f} MB | Active Connections: {self.tunnel.active_connections}"
            )

        # Drivers Check
        drivers = check_driver_store()
        all_drivers = drivers.get("appleusb") and drivers.get("netaapl64")
        if all_drivers:
            self.lbl_drivers_status.configure(text="✔ Drivers Installed", text_color="#34C759")
            self.btn_install_drivers.configure(text="Re-install Drivers", fg_color="gray40")
        else:
            self.lbl_drivers_status.configure(text="⚠ Missing Drivers", text_color="#FF9500")
            self.btn_install_drivers.configure(text="Install Drivers Now", fg_color="#007AFF")

        # Apple Device Check
        device_info = is_apple_device_connected()
        if device_info["connected"]:
            self.lbl_device_status.configure(text=f"✔ Connected: {device_info['name']}", text_color="#34C759")
        else:
            self.lbl_device_status.configure(text="❌ No Apple device detected via USB", text_color="#FF3B30")

        # Network Overview
        net = get_network_overview()
        if net["adapter_present"]:
            self.lbl_network_status.configure(text=f"✔ Adapter Active ({net['status']})", text_color="#34C759")
            self.lbl_network_details.configure(
                text=f"IP: {net['ip'] or 'Acquiring IP...'} | Gateway: {net['gateway'] or '172.20.10.1'}"
            )
        else:
            self.lbl_network_status.configure(text="❌ Apple Ethernet Adapter not detected", text_color="#FF3B30")

    def _on_install_drivers(self):
        if not is_admin():
            confirmed = messagebox.askyesno(
                "Administrator Required",
                "Installing device drivers requires Administrator privileges.\n\nGrant permission now?"
            )
            if confirmed:
                run_as_admin([sys.argv[0], "--install-drivers"])
            return

        success, msg = install_drivers()
        messagebox.showinfo("Result", msg)
        self._update_all_status()

    def _on_restart_adapter(self):
        def worker():
            ok, msg = restart_apple_adapter()
            messagebox.showinfo("Status", msg if ok else f"Notice: {msg}")
            self._update_all_status()
        threading.Thread(target=worker, daemon=True).start()

    def _on_renew_ip(self):
        def worker():
            ok, msg = flush_dns_and_renew_dhcp()
            messagebox.showinfo("Status", msg)
            self._update_all_status()
        threading.Thread(target=worker, daemon=True).start()

    def destroy(self):
        self.running = False
        if self.tunnel_active:
            self.tunnel.stop()
            WindowsProxyManager.disable_proxy()
        super().destroy()


def run_app():
    app = HotSpotAppUI()
    app.mainloop()


if __name__ == "__main__":
    run_app()
