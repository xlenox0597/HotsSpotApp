"""
Network Manager for HotSpotApp
Monitors Apple Mobile Device Ethernet adapter, IP leases, connectivity, and provides repair tools.
"""

import json
import os
import subprocess
import time
from typing import Dict, Any, Optional, Tuple
import urllib.request


def get_apple_network_adapter() -> Optional[Dict[str, Any]]:
    """
    Find the Apple Mobile Device Ethernet network adapter.
    """
    ps_cmd = (
        'Get-NetAdapter | '
        'Where-Object { $_.InterfaceDescription -like "*Apple*" -or $_.Name -like "*Apple*" } | '
        'Select-Object Name, InterfaceDescription, Status, LinkSpeed, MacAddress | '
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
            if isinstance(data, list) and len(data) > 0:
                return data[0]
            elif isinstance(data, dict):
                return data
    except Exception as e:
        print(f"Error querying network adapter: {e}")
        
    return None


def get_adapter_ip_config(adapter_name: str) -> Dict[str, Any]:
    """
    Get IPv4, Gateway, and DNS settings for the specified adapter.
    """
    config = {
        "ipv4": None,
        "gateway": None,
        "dns": []
    }
    
    if not adapter_name:
        return config

    ps_cmd = (
        f'$ip = Get-NetIPAddress -InterfaceAlias "{adapter_name}" -AddressFamily IPv4 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty IPAddress; '
        f'$gw = Get-NetRoute -InterfaceAlias "{adapter_name}" -DestinationPrefix "0.0.0.0/0" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty NextHop; '
        f'$dns = Get-DnsClientServerAddress -InterfaceAlias "{adapter_name}" -AddressFamily IPv4 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty ServerAddresses; '
        '@{"ipv4"=$ip; "gateway"=$gw; "dns"=$dns} | ConvertTo-Json -Compress'
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
            config["ipv4"] = data.get("ipv4")
            config["gateway"] = data.get("gateway")
            dns = data.get("dns")
            if isinstance(dns, list):
                config["dns"] = dns
            elif dns:
                config["dns"] = [dns]
    except Exception as e:
        print(f"Error getting IP configuration: {e}")

    return config


def test_internet_connectivity() -> Dict[str, Any]:
    """
    Test internet connection and latency.
    """
    start_time = time.time()
    try:
        req = urllib.request.Request(
            "http://connectivitycheck.gstatic.com/generate_204",
            headers={"User-Agent": "HotSpotApp-Connection-Check"}
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            latency_ms = int((time.time() - start_time) * 1000)
            if resp.status == 204 or resp.status == 200:
                return {
                    "online": True,
                    "latency_ms": latency_ms,
                    "message": f"Connected ({latency_ms} ms)"
                }
    except Exception:
        pass

    return {
        "online": False,
        "latency_ms": None,
        "message": "Offline / No Internet"
    }


def restart_apple_adapter(adapter_name: str = "Apple Mobile Device Ethernet") -> Tuple[bool, str]:
    """
    Restart the Apple Ethernet network adapter (requires admin).
    """
    ps_cmd = f'Restart-NetAdapter -Name "{adapter_name}" -ErrorAction Stop'
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            check=False,
            timeout=10
        )
        if res.returncode == 0:
            return True, f"Successfully restarted adapter '{adapter_name}'."
        return False, res.stderr.strip() or res.stdout.strip()
    except Exception as e:
        return False, str(e)


def flush_dns_and_renew_dhcp() -> Tuple[bool, str]:
    """
    Flush DNS cache and renew DHCP leases.
    """
    logs = []
    try:
        subprocess.run(["ipconfig", "/flushdns"], capture_output=True, check=False)
        logs.append("Flushed DNS Resolver Cache.")
        subprocess.run(["ipconfig", "/renew"], capture_output=True, check=False)
        logs.append("Renewed DHCP IP configuration.")
        return True, "\n".join(logs)
    except Exception as e:
        return False, str(e)


def get_network_overview() -> Dict[str, Any]:
    """
    Consolidated network status report.
    """
    adapter = get_apple_network_adapter()
    if not adapter:
        return {
            "adapter_present": False,
            "status": "Adapter Not Found",
            "name": None,
            "ip": None,
            "gateway": None,
            "dns": [],
            "internet": test_internet_connectivity()
        }

    adapter_name = adapter.get("Name", "Apple Mobile Device Ethernet")
    ip_info = get_adapter_ip_config(adapter_name)
    internet = test_internet_connectivity()

    return {
        "adapter_present": True,
        "status": adapter.get("Status", "Unknown"),
        "name": adapter_name,
        "description": adapter.get("InterfaceDescription", ""),
        "link_speed": adapter.get("LinkSpeed", "N/A"),
        "ip": ip_info.get("ipv4"),
        "gateway": ip_info.get("gateway"),
        "dns": ip_info.get("dns", []),
        "internet": internet
    }


if __name__ == "__main__":
    overview = get_network_overview()
    print("Network Overview:", overview)
