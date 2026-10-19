"""
Device Detector for HotSpotApp
Detects connected Apple iOS devices (iPhone, iPad) over USB.
"""

import json
import subprocess
from typing import Dict, Any, List


def get_connected_apple_devices() -> List[Dict[str, Any]]:
    """
    Query Windows PnP devices for connected Apple hardware (Vendor ID 05AC).
    """
    devices = []
    
    ps_cmd = (
        'Get-PnpDevice | '
        'Where-Object { $_.InstanceId -like "*VID_05AC*" -and $_.Present -eq $true } | '
        'Select-Object FriendlyName, Status, Class, InstanceId | '
        'ConvertTo-Json -Compress'
    )
    
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            check=False,
            timeout=5
        )
        output = proc.stdout.strip()
        if output:
            data = json.loads(output)
            if isinstance(data, dict):
                devices.append(data)
            elif isinstance(data, list):
                devices.extend(data)
    except Exception as e:
        print(f"Error querying Apple devices: {e}")

    return devices


def is_apple_device_connected() -> Dict[str, Any]:
    """
    Returns a summary of Apple device connection status.
    """
    devices = get_connected_apple_devices()
    
    if not devices:
        return {
            "connected": False,
            "name": "No Apple device detected",
            "status": "Disconnected",
            "devices": []
        }
    
    # Check for friendly name
    device_name = "Apple iOS Device"
    has_ok_status = False
    
    for dev in devices:
        fname = dev.get("FriendlyName") or ""
        if "iPhone" in fname or "iPad" in fname:
            device_name = fname
        if dev.get("Status") == "OK":
            has_ok_status = True
            
    return {
        "connected": True,
        "name": device_name,
        "status": "OK" if has_ok_status else "Attention Required",
        "devices": devices
    }


if __name__ == "__main__":
    status = is_apple_device_connected()
    print("Apple Device Status:", status)
