import SwiftUI

struct ContentView: View {
    @ObservedObject var state = TunnelState.shared
    @State private var showingInstructions = false

    var body: some View {
        NavigationView {
            ZStack {
                Color(UIColor.systemGroupedBackground)
                    .ignoresSafeArea()

                ScrollView {
                    VStack(spacing: 24) {
                        // Header
                        VStack(spacing: 6) {
                            Text("USB Internet Tunnel")
                                .font(.system(size: 26, weight: .bold))
                            Text("Share iPhone cellular data over cable without Personal Hotspot carrier restrictions")
                                .font(.system(size: 13))
                                .foregroundColor(.secondary)
                                .multilineTextAlignment(.center)
                                .padding(.horizontal, 20)
                        }
                        .padding(.top, 10)

                        // Main Big Status Circle / Toggle
                        VStack(spacing: 16) {
                            ZStack {
                                Circle()
                                    .fill(state.isRunning ? Color.green.opacity(0.15) : Color.gray.opacity(0.15))
                                    .frame(width: 170, height: 170)

                                if state.isRunning {
                                    Circle()
                                        .stroke(Color.green, lineWidth: 3)
                                        .frame(width: 170, height: 170)
                                }

                                Image(systemName: state.isRunning ? "cable.connector.horizontal" : "cable.connector")
                                    .font(.system(size: 64, weight: .medium))
                                    .foregroundColor(state.isRunning ? .green : .gray)
                            }

                            Text(state.isRunning ? "Tunnel Active" : "Ready to Connect")
                                .font(.system(size: 20, weight: .semibold))

                            Text(state.statusMessage)
                                .font(.system(size: 13))
                                .foregroundColor(.secondary)

                            Button(action: toggleTunnel) {
                                Text(state.isRunning ? "Stop Tethering" : "Start Tethering")
                                    .font(.system(size: 16, weight: .bold))
                                    .foregroundColor(.white)
                                    .frame(maxWidth: .infinity)
                                    .frame(height: 50)
                                    .background(state.isRunning ? Color.red : Color.blue)
                                    .cornerRadius(12)
                            }
                            .padding(.horizontal, 40)
                        }
                        .padding(.vertical, 24)
                        .frame(maxWidth: .infinity)
                        .background(Color(UIColor.secondarySystemGroupedBackground))
                        .cornerRadius(16)
                        .padding(.horizontal, 16)

                        // Live Telemetry Card
                        if state.isRunning {
                            VStack(spacing: 16) {
                                HStack {
                                    Text("Live Telemetry")
                                        .font(.system(size: 15, weight: .bold))
                                    Spacer()
                                    Label("\(state.activeConnections) Active", systemImage: "network")
                                        .font(.system(size: 12, weight: .medium))
                                        .foregroundColor(.green)
                                }

                                Divider()

                                HStack(spacing: 20) {
                                    VStack(alignment: .leading, spacing: 4) {
                                        Text("Download Speed")
                                            .font(.caption)
                                            .foregroundColor(.secondary)
                                        Text(state.downloadSpeedFormatted)
                                            .font(.system(size: 18, weight: .bold))
                                    }
                                    Spacer()
                                    VStack(alignment: .trailing, spacing: 4) {
                                        Text("Upload Speed")
                                            .font(.caption)
                                            .foregroundColor(.secondary)
                                        Text(state.uploadSpeedFormatted)
                                            .font(.system(size: 18, weight: .bold))
                                    }
                                }

                                Divider()

                                HStack(spacing: 20) {
                                    VStack(alignment: .leading, spacing: 4) {
                                        Text("Received Data")
                                            .font(.caption)
                                            .foregroundColor(.secondary)
                                        Text(TunnelState.formatBytes(bytes: state.totalBytesReceived))
                                            .font(.system(size: 15, weight: .medium))
                                    }
                                    Spacer()
                                    VStack(alignment: .trailing, spacing: 4) {
                                        Text("Sent Data")
                                            .font(.caption)
                                            .foregroundColor(.secondary)
                                        Text(TunnelState.formatBytes(bytes: state.totalBytesSent))
                                            .font(.system(size: 15, weight: .medium))
                                    }
                                }
                            }
                            .padding(20)
                            .frame(maxWidth: .infinity)
                            .background(Color(UIColor.secondarySystemGroupedBackground))
                            .cornerRadius(16)
                            .padding(.horizontal, 16)
                            .transition(.opacity.combined(with: .move(edge: .top)))
                        }

                        // Instructions Card
                        VStack(alignment: .leading, spacing: 12) {
                            Text("How to Connect with Windows PC")
                                .font(.system(size: 15, weight: .bold))

                            StepRow(num: "1", text: "Plug your iPhone into the Windows PC via Lightning or USB-C cable.")
                            StepRow(num: "2", text: "If prompted, tap 'Trust This Computer' and enter your passcode.")
                            StepRow(num: "3", text: "Tap 'Start Tethering' above.")
                            StepRow(num: "4", text: "Open HotSpotApp on Windows and click 'Enable USB Tunnel'.")
                        }
                        .padding(20)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(Color(UIColor.secondarySystemGroupedBackground))
                        .cornerRadius(16)
                        .padding(.horizontal, 16)
                        .padding(.bottom, 30)
                    }
                }
            }
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .principal) {
                    Text("HotSpot Tunnel")
                        .font(.headline)
                }
            }
        }
    }

    private func toggleTunnel() {
        withAnimation {
            if state.isRunning {
                ProxyServer.shared.stop()
            } else {
                do {
                    try ProxyServer.shared.start()
                } catch {
                    state.statusMessage = "Error: \(error.localizedDescription)"
                }
            }
        }
    }
}

struct StepRow: View {
    let num: String
    let text: String

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            ZStack {
                Circle()
                    .fill(Color.blue.opacity(0.15))
                    .frame(width: 24, height: 24)
                Text(num)
                    .font(.system(size: 12, weight: .bold))
                    .foregroundColor(.blue)
            }
            Text(text)
                .font(.system(size: 13))
                .foregroundColor(.primary)
                .fixedSize(horizontal: false, vertical: true)
        }
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
    }
}
