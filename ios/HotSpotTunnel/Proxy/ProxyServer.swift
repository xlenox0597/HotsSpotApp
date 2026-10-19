import Foundation
import Network

/// Lightweight asynchronous HTTP CONNECT proxy server built with Apple's Network.framework
public class ProxyServer {
    public static let shared = ProxyServer()

    private var listener: NWListener?
    private let queue = DispatchQueue(label: "com.hotspot.proxyserver", qos: .userInitiated)
    private var activeConnections: [UUID: ProxyConnection] = [:]

    public let port: UInt16 = 8080

    private init() {}

    public func start() throws {
        stop()

        let parameters = NWParameters.tcp
        parameters.allowLocalEndpointReuse = true

        guard let nwPort = NWEndpoint.Port(rawValue: port) else {
            throw NSError(domain: "ProxyServer", code: -1, userInfo: [NSLocalizedDescriptionKey: "Invalid port"])
        }

        listener = try NWListener(using: parameters, on: nwPort)
        listener?.stateUpdateHandler = { [weak self] state in
            guard let self = self else { return }
            switch state {
            case .ready:
                print("[ProxyServer] Listening on 127.0.0.1:\(self.port)")
                DispatchQueue.main.async {
                    TunnelState.shared.isRunning = true
                    TunnelState.shared.statusMessage = "Proxy active on port \(self.port)"
                }
            case .failed(let error):
                print("[ProxyServer] Listener failed: \(error)")
                self.stop()
            case .cancelled:
                print("[ProxyServer] Listener cancelled.")
            default:
                break
            }
        }

        listener?.newConnectionHandler = { [weak self] newConn in
            self?.handleIncomingConnection(newConn)
        }

        listener?.start(queue: queue)
        BackgroundKeepAlive.shared.start()
    }

    public func stop() {
        listener?.cancel()
        listener = nil

        queue.async {
            for (_, conn) in self.activeConnections {
                conn.close()
            }
            self.activeConnections.removeAll()
        }

        BackgroundKeepAlive.shared.stop()

        DispatchQueue.main.async {
            TunnelState.shared.isRunning = false
            TunnelState.shared.activeConnections = 0
            TunnelState.shared.statusMessage = "Stopped"
        }
    }

    private func handleIncomingConnection(_ clientConn: NWConnection) {
        let id = UUID()
        let proxyConn = ProxyConnection(id: id, clientConnection: clientConn) { [weak self] in
            self?.queue.async {
                self?.activeConnections.removeValue(forKey: id)
                DispatchQueue.main.async {
                    TunnelState.shared.activeConnections = self?.activeConnections.count ?? 0
                }
            }
        }

        queue.async {
            self.activeConnections[id] = proxyConn
            DispatchQueue.main.async {
                TunnelState.shared.activeConnections = self.activeConnections.count
            }
        }

        proxyConn.start()
    }
}

/// Manages a single proxied client-to-target tunnel
class ProxyConnection {
    let id: UUID
    let clientConn: NWConnection
    var targetConn: NWConnection?
    let onClose: () -> Void

    private let queue = DispatchQueue(label: "com.hotspot.connection", qos: .userInitiated)
    private var isClosed = false

    init(id: UUID, clientConnection: NWConnection, onClose: @escaping () -> Void) {
        self.id = id
        self.clientConn = clientConnection
        self.onClose = onClose
    }

    func start() {
        clientConn.stateUpdateHandler = { [weak self] state in
            if case .failed = state { self?.close() }
            if case .cancelled = state { self?.close() }
        }
        clientConn.start(queue: queue)
        readInitialRequest()
    }

    private func readInitialRequest() {
        clientConn.receive(minimumIncompleteLength: 1, maximumLength: 8192) { [weak self] data, _, isComplete, error in
            guard let self = self else { return }
            if let error = error {
                print("[ProxyConnection] Initial read error: \(error)")
                self.close()
                return
            }

            guard let data = data, !data.isEmpty,
                  let requestStr = String(data: data, encoding: .utf8) else {
                self.close()
                return
            }

            self.parseAndTunnel(requestStr: requestStr, rawData: data)
        }
    }

    private func parseAndTunnel(requestStr: String, rawData: Data) {
        let lines = requestStr.components(separatedBy: "\r\n")
        guard let firstLine = lines.first else {
            close()
            return
        }

        let parts = firstLine.components(separatedBy: " ")
        guard parts.count >= 2 else {
            close()
            return
        }

        let method = parts[0].uppercased()
        let target = parts[1]

        if method == "CONNECT" {
            // HTTPS CONNECT Tunnel
            let hostParts = target.components(separatedBy: ":")
            let hostStr = hostParts[0]
            let portNum: UInt16 = hostParts.count > 1 ? UInt16(hostParts[1]) ?? 443 : 443

            connectToTarget(host: hostStr, port: portNum) { [weak self] success in
                guard let self = self else { return }
                if success {
                    let response = "HTTP/1.1 200 Connection Established\r\n\r\n"
                    if let respData = response.data(using: .utf8) {
                        self.clientConn.send(content: respData, completion: .contentProcessed({ [weak self] _ in
                            self?.startBiDirectionalPiping()
                        }))
                    }
                } else {
                    let errResp = "HTTP/1.1 502 Bad Gateway\r\n\r\n"
                    self.clientConn.send(content: errResp.data(using: .utf8), completion: .contentProcessed({ [weak self] _ in
                        self?.close()
                    }))
                }
            }
        } else {
            // Plain HTTP Proxy
            var hostStr = ""
            var portNum: UInt16 = 80

            for line in lines {
                if line.lowercased().starts(with: "host:") {
                    let h = line.dropFirst(5).trimmingCharacters(in: .whitespaces)
                    let hParts = h.components(separatedBy: ":")
                    hostStr = hParts[0]
                    if hParts.count > 1 {
                        portNum = UInt16(hParts[1]) ?? 80
                    }
                    break
                }
            }

            if hostStr.isEmpty {
                close()
                return
            }

            connectToTarget(host: hostStr, port: portNum) { [weak self] success in
                guard let self = self else { return }
                if success {
                    self.targetConn?.send(content: rawData, completion: .contentProcessed({ [weak self] _ in
                        self?.startBiDirectionalPiping()
                    }))
                } else {
                    self.close()
                }
            }
        }
    }

    private func connectToTarget(host: String, port: UInt16, completion: @escaping (Bool) -> Void) {
        guard let nwPort = NWEndpoint.Port(rawValue: port) else {
            completion(false)
            return
        }

        let endpoint = NWEndpoint.hostPort(host: NWEndpoint.Host(host), port: nwPort)
        let target = NWConnection(to: endpoint, using: .tcp)

        target.stateUpdateHandler = { [weak self] state in
            switch state {
            case .ready:
                completion(true)
            case .failed(let err):
                print("[ProxyConnection] Failed outbound to \(host):\(port): \(err)")
                completion(false)
                self?.close()
            case .cancelled:
                self?.close()
            default:
                break
            }
        }

        self.targetConn = target
        target.start(queue: queue)
    }

    private func startBiDirectionalPiping() {
        pipe(from: clientConn, to: targetConn, isUpload: true)
        pipe(from: targetConn, to: clientConn, isUpload: false)
    }

    private func pipe(from source: NWConnection?, to dest: NWConnection?, isUpload: Bool) {
        guard let source = source, let dest = dest else { return }

        source.receive(minimumIncompleteLength: 1, maximumLength: 32768) { [weak self] data, _, isComplete, error in
            guard let self = self, !self.isClosed else { return }

            if let data = data, !data.isEmpty {
                if isUpload {
                    TunnelState.shared.addBytes(sent: UInt64(data.count), received: 0)
                } else {
                    TunnelState.shared.addBytes(sent: 0, received: UInt64(data.count))
                }

                dest.send(content: data, completion: .contentProcessed({ [weak self] sendErr in
                    if sendErr == nil {
                        self?.pipe(from: source, to: dest, isUpload: isUpload)
                    } else {
                        self?.close()
                    }
                }))
            } else if isComplete || error != nil {
                self.close()
            }
        }
    }

    func close() {
        guard !isClosed else { return }
        isClosed = true
        clientConn.cancel()
        targetConn?.cancel()
        onClose()
    }
}
