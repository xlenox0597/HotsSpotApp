"""
Windows System Proxy Manager
Enables and disables system-wide HTTP/HTTPS proxy configuration via Windows Registry and WinINet API.
"""

import ctypes
import winreg
from typing import Tuple, Optional

INTERNET_SETTINGS_KEY = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"

# WinINet API Constants
INTERNET_OPTION_SETTINGS_CHANGED = 39
INTERNET_OPTION_REFRESH = 37


def notify_wininet():
    """Notify Windows system and active applications that proxy settings have changed."""
    try:
        internet_set_option = ctypes.windll.wininet.InternetSetOptionW
        internet_set_option(0, INTERNET_OPTION_SETTINGS_CHANGED, 0, 0)
        internet_set_option(0, INTERNET_OPTION_REFRESH, 0, 0)
    except Exception as e:
        print(f"[ProxyManager] Warning: failed to refresh WinINet: {e}")


class WindowsProxyManager:
    _original_enabled: Optional[int] = None
    _original_server: Optional[str] = None
    _original_override: Optional[str] = None

    @classmethod
    def get_proxy_status(cls) -> Tuple[bool, Optional[str]]:
        """Returns (is_enabled, proxy_server)."""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, INTERNET_SETTINGS_KEY, 0, winreg.KEY_READ) as key:
                enabled, _ = winreg.QueryValueEx(key, "ProxyEnable")
                server = None
                if enabled:
                    try:
                        server, _ = winreg.QueryValueEx(key, "ProxyServer")
                    except FileNotFoundError:
                        pass
                return bool(enabled), server
        except Exception as e:
            print(f"[ProxyManager] Error reading proxy status: {e}")
            return False, None

    @classmethod
    def enable_proxy(cls, host: str = "127.0.0.1", port: int = 8080) -> bool:
        """
        Enable Windows system proxy pointing to the local USB tunnel.
        Saves previous settings to allow seamless restoration later.
        """
        proxy_address = f"{host}:{port}"
        override = "<local>;localhost;127.0.0.1"

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, INTERNET_SETTINGS_KEY, 0, winreg.KEY_READ) as key:
                if cls._original_enabled is None:
                    try:
                        cls._original_enabled, _ = winreg.QueryValueEx(key, "ProxyEnable")
                    except FileNotFoundError:
                        cls._original_enabled = 0
                if cls._original_server is None:
                    try:
                        cls._original_server, _ = winreg.QueryValueEx(key, "ProxyServer")
                    except FileNotFoundError:
                        cls._original_server = ""
                if cls._original_override is None:
                    try:
                        cls._original_override, _ = winreg.QueryValueEx(key, "ProxyOverride")
                    except FileNotFoundError:
                        cls._original_override = ""

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, INTERNET_SETTINGS_KEY, 0, winreg.KEY_WRITE) as key:
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, proxy_address)
                winreg.SetValueEx(key, "ProxyOverride", 0, winreg.REG_SZ, override)

            notify_wininet()
            print(f"[ProxyManager] Enabled Windows system proxy: {proxy_address}")
            return True
        except Exception as e:
            print(f"[ProxyManager] Failed to set proxy: {e}")
            return False

    @classmethod
    def disable_proxy(cls) -> bool:
        """
        Disable Windows system proxy and restore previous user settings.
        """
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, INTERNET_SETTINGS_KEY, 0, winreg.KEY_WRITE) as key:
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)

                # Restore previous server address if known
                if cls._original_server is not None:
                    winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, cls._original_server)

            notify_wininet()
            print("[ProxyManager] Disabled Windows system proxy.")
            return True
        except Exception as e:
            print(f"[ProxyManager] Failed to disable proxy: {e}")
            return False


if __name__ == "__main__":
    status, srv = WindowsProxyManager.get_proxy_status()
    print("Initial Proxy Status:", status, "Server:", srv)
