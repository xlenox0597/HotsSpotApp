"""
Driver Manager for HotSpotApp
Handles detection and installation of Apple USB and Apple Mobile Device Ethernet drivers.
"""

import ctypes
import os
import subprocess
import sys
from typing import Dict, Tuple


def is_admin() -> bool:
    """Check if the current process has administrative privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def run_as_admin(command_args: list) -> bool:
    """Relaunch the script or command with elevated UAC permissions."""
    if is_admin():
        return True
    
    executable = sys.executable
    params = " ".join([f'"{arg}"' for arg in command_args])
    
    try:
        ret = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            executable,
            params,
            None,
            1  # SW_SHOWNORMAL
        )
        return ret > 32
    except Exception as e:
        print(f"Failed to elevate permissions: {e}")
        return False


def get_drivers_dir() -> str:
    """Locate the drivers folder relative to current executable or script."""
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    drivers_dir = os.path.join(base_dir, "drivers")
    return drivers_dir


def check_driver_store() -> Dict[str, bool]:
    """
    Check if Apple USB and Apple Mobile Device Ethernet drivers are present in the Windows DriverStore.
    """
    results = {
        "appleusb": False,
        "netaapl64": False
    }
    
    try:
        output = subprocess.check_output(["pnputil", "/enum-drivers"], text=True, stderr=subprocess.STDOUT)
        lower_output = output.lower()
        if "appleusb.inf" in lower_output or "apple, inc." in lower_output:
            results["appleusb"] = True
        if "netaapl64.inf" in lower_output:
            results["netaapl64"] = True
    except Exception as e:
        print(f"Error checking driver store: {e}")
        
    return results


def check_installed_pnp_devices() -> Dict[str, bool]:
    """Check if the Apple Ethernet network adapter is registered in Windows PnP."""
    results = {
        "ethernet_adapter_found": False,
        "usb_device_found": False
    }
    
    ps_cmd = 'Get-PnpDevice -FriendlyName "*Apple*" -ErrorAction SilentlyContinue | Select-Object -Property FriendlyName, Status | ConvertTo-Json'
    try:
        output = subprocess.check_output(["powershell", "-NoProfile", "-Command", ps_cmd], text=True, stderr=subprocess.DEVNULL).strip()
        if "Apple Mobile Device Ethernet" in output:
            results["ethernet_adapter_found"] = True
        if "Apple Mobile Device" in output or "Apple iPhone" in output:
            results["usb_device_found"] = True
    except Exception as e:
        print(f"Error checking PnP devices: {e}")

    return results


def install_drivers() -> Tuple[bool, str]:
    """
    Install both Apple USB and Apple Mobile Device Ethernet drivers using pnputil.
    Requires administrative privileges.
    """
    if not is_admin():
        return False, "Administrator privileges are required to install device drivers."

    drivers_dir = get_drivers_dir()
    usb_inf = os.path.join(drivers_dir, "appleusb", "AppleUsb.inf")
    net_inf = os.path.join(drivers_dir, "netaapl64", "netaapl64.Inf")

    if not os.path.exists(usb_inf):
        return False, f"Driver file not found: {usb_inf}"
    if not os.path.exists(net_inf):
        return False, f"Driver file not found: {net_inf}"

    log = []
    success = True

    for inf_path in [usb_inf, net_inf]:
        cmd = ["pnputil", "/add-driver", inf_path, "/install"]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if res.returncode == 0 or "successfully added" in res.stdout.lower() or "already exists" in res.stdout.lower():
                log.append(f"Successfully staged and installed: {os.path.basename(inf_path)}")
            else:
                log.append(f"Warning for {os.path.basename(inf_path)}: {res.stdout.strip()}")
        except Exception as e:
            success = False
            log.append(f"Failed to install {os.path.basename(inf_path)}: {e}")

    return success, "\n".join(log)


if __name__ == "__main__":
    if "--install" in sys.argv:
        if not is_admin():
            print("Requesting administrator privileges...")
            run_as_admin(sys.argv)
            sys.exit(0)
        ok, msg = install_drivers()
        print(msg)
        sys.exit(0 if ok else 1)
    else:
        print("Driver Store Status:", check_driver_store())
        print("PnP Devices Status:", check_installed_pnp_devices())
