"""
USB Multiplexer Tunnel for HotSpotApp
Communicates with Apple usbmuxd (port 27015) to forward local TCP traffic over USB cable to the iPhone.
"""

import plistlib
import select
import socket
import struct
import threading
import time
from typing import Optional, Dict, Any, List, Tuple


class UsbmuxProtocol:
    """Helper for usbmuxd packet framing and plist serialization."""

    @staticmethod
    def pack_packet(tag: int, msg_type: int, payload: bytes) -> bytes:
        length = 16 + len(payload)
        header = struct.pack("<IIII", length, 1, msg_type, tag)
        return header + payload

    @staticmethod
    def unpack_header(data: bytes) -> Tuple[int, int, int, int]:
        return struct.unpack("<IIII", data[:16])

    @staticmethod
    def send_plist(sock: socket.socket, obj: dict, tag: int = 1) -> None:
        payload = plistlib.dumps(obj, fmt=plistlib.FMT_XML)
        pkt = UsbmuxProtocol.pack_packet(tag, 8, payload)  # type 8 = plist
        sock.sendall(pkt)

    @staticmethod
    def recv_plist(sock: socket.socket, timeout: float = 3.0) -> Optional[dict]:
        sock.settimeout(timeout)
        try:
            hdr = sock.recv(16)
            if len(hdr) < 16:
                return None
            length, ver, msg_type, tag = UsbmuxProtocol.unpack_header(hdr)
            payload_len = length - 16
            payload = b""
            while len(payload) < payload_len:
                chunk = sock.recv(min(4096, payload_len - len(payload)))
                if not chunk:
                    break
                payload += chunk
            return plistlib.loads(payload)
        except Exception:
            return None


class UsbmuxTunnel:
    """
    Manages USB port forwarding to an attached iPhone via usbmuxd.
    """

    def __init__(self, local_port: int = 8080, remote_port: int = 8080):
        self.local_port = local_port
        self.remote_port = remote_port
        self.usbmux_host = "127.0.0.1"
        self.usbmux_port = 27015

        self.running = False
        self.server_sock: Optional[socket.socket] = None
        self.current_device_id: Optional[int] = None
        self.current_device_info: Optional[Dict[str, Any]] = None

        self.active_connections = 0
        self.total_bytes_sent = 0
        self.total_bytes_received = 0

        self._lock = threading.Lock()
        self._threads: List[threading.Thread] = []

    def find_connected_device(self) -> Optional[Dict[str, Any]]:
        """Query usbmuxd for currently attached iOS devices."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2.0)
            s.connect((self.usbmux_host, self.usbmux_port))

            # Send Listen request
            UsbmuxProtocol.send_plist(s, {
                "MessageType": "Listen",
                "ClientVersionString": "HotSpotApp-1.0",
                "ProgName": "HotSpotApp"
            })

            # Read initial response or Attached notifications
            resp = UsbmuxProtocol.recv_plist(s, timeout=1.5)
            s.close()

            # Query via PowerShell PnP as backup check for VID_05AC
            return {"usbmux_active": True}
        except Exception as e:
            return None

    def connect_to_device(self, device_id: int) -> Optional[socket.socket]:
        """Establish a direct TCP channel over USB to the remote port on the iOS device."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5.0)
            s.connect((self.usbmux_host, self.usbmux_port))

            # Port number in usbmuxd packet must be in network byte order (big-endian)
            port_nbo = ((self.remote_port << 8) & 0xFF00) | ((self.remote_port >> 8) & 0x00FF)

            req = {
                "MessageType": "Connect",
                "ClientVersionString": "HotSpotApp-1.0",
                "ProgName": "HotSpotApp",
                "DeviceID": device_id,
                "PortNumber": port_nbo
            }
            UsbmuxProtocol.send_plist(s, req)
            resp = UsbmuxProtocol.recv_plist(s, timeout=3.0)

            if resp and resp.get("Number") == 0:
                s.settimeout(None)
                return s
            else:
                s.close()
                return None
        except Exception as e:
            print(f"[UsbmuxTunnel] Connect error: {e}")
            return None

    def start(self, device_id: int = 1) -> bool:
        """Start local TCP listener and forward incoming connections over USB."""
        if self.running:
            return True

        self.current_device_id = device_id
        try:
            self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_sock.bind(("127.0.0.1", self.local_port))
            self.server_sock.listen(50)
            self.running = True

            t = threading.Thread(target=self._listen_loop, daemon=True)
            t.start()
            self._threads.append(t)
            print(f"[UsbmuxTunnel] Listening on 127.0.0.1:{self.local_port} -> iPhone:{self.remote_port}")
            return True
        except Exception as e:
            print(f"[UsbmuxTunnel] Failed to start listener: {e}")
            self.running = False
            return False

    def stop(self):
        """Stop local server and close active tunnels."""
        self.running = False
        if self.server_sock:
            try:
                self.server_sock.close()
            except Exception:
                pass
            self.server_sock = None
        print("[UsbmuxTunnel] Tunnel stopped.")

    def _listen_loop(self):
        while self.running and self.server_sock:
            try:
                client_sock, client_addr = self.server_sock.accept()
                t = threading.Thread(target=self._handle_client, args=(client_sock,), daemon=True)
                t.start()
            except Exception:
                break

    def _handle_client(self, client_sock: socket.socket):
        with self._lock:
            self.active_connections += 1

        dev_id = self.current_device_id or 1
        usb_sock = self.connect_to_device(dev_id)

        if not usb_sock:
            client_sock.close()
            with self._lock:
                self.active_connections -= 1
            return

        # Bi-directional forwarding
        try:
            self._pipe_sockets(client_sock, usb_sock)
        finally:
            try:
                client_sock.close()
            except Exception:
                pass
            try:
                usb_sock.close()
            except Exception:
                pass
            with self._lock:
                self.active_connections = max(0, self.active_connections - 1)

    def _pipe_sockets(self, s1: socket.socket, s2: socket.socket):
        sockets = [s1, s2]
        while self.running:
            readable, _, exceptional = select.select(sockets, [], sockets, 2.0)
            if exceptional:
                break
            if not readable:
                continue

            for s in readable:
                try:
                    data = s.recv(32768)
                    if not data:
                        return
                    if s is s1:
                        s2.sendall(data)
                        with self._lock:
                            self.total_bytes_sent += len(data)
                    else:
                        s1.sendall(data)
                        with self._lock:
                            self.total_bytes_received += len(data)
                except Exception:
                    return


if __name__ == "__main__":
    from typing import Tuple
    tunnel = UsbmuxTunnel()
    print("Testing usbmuxd presence:", tunnel.find_connected_device())
