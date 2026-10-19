import Foundation
import Combine

/// Observable state model representing live tethering telemetry
public class TunnelState: ObservableObject {
    public static let shared = TunnelState()

    @Published public var isRunning: Bool = false
    @Published public var activeConnections: Int = 0
    @Published public var totalBytesSent: UInt64 = 0
    @Published public var totalBytesReceived: UInt64 = 0
    @Published public var uploadSpeedFormatted: String = "0 KB/s"
    @Published public var downloadSpeedFormatted: String = "0 KB/s"
    @Published public var statusMessage: String = "Ready to connect"

    private var previousSent: UInt64 = 0
    private var previousReceived: UInt64 = 0
    private var speedTimer: AnyCancellable?

    private init() {
        startSpeedMonitoring()
    }

    private func startSpeedMonitoring() {
        speedTimer = Timer.publish(every: 1.0, on: .main, in: .common)
            .autoconnect()
            .sink { [weak self] _ in
                guard let self = self else { return }
                guard self.isRunning else {
                    self.uploadSpeedFormatted = "0 KB/s"
                    self.downloadSpeedFormatted = "0 KB/s"
                    return
                }

                let sentDiff = self.totalBytesSent > self.previousSent ? self.totalBytesSent - self.previousSent : 0
                let recvDiff = self.totalBytesReceived > self.previousReceived ? self.totalBytesReceived - self.previousReceived : 0

                self.previousSent = self.totalBytesSent
                self.previousReceived = self.totalBytesReceived

                self.uploadSpeedFormatted = Self.formatSpeed(bytes: sentDiff)
                self.downloadSpeedFormatted = Self.formatSpeed(bytes: recvDiff)
            }
    }

    public func addBytes(sent: UInt64, received: UInt64) {
        DispatchQueue.main.async {
            self.totalBytesSent += sent
            self.totalBytesReceived += received
        }
    }

    public static func formatBytes(bytes: UInt64) -> String {
        let formatter = ByteCountFormatter()
        formatter.allowedUnits = [.useBytes, .useKB, .useMB, .useGB]
        formatter.countStyle = .file
        return formatter.string(fromByteCount: Int64(bytes))
    }

    public static func formatSpeed(bytes: UInt64) -> String {
        if bytes < 1024 {
            return "\(bytes) B/s"
        } else if bytes < 1024 * 1024 {
            return String(format: "%.1f KB/s", Double(bytes) / 1024.0)
        } else {
            return String(format: "%.2f MB/s", Double(bytes) / (1024.0 * 1024.0))
        }
    }
}
