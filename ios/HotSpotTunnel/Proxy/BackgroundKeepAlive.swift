import Foundation
import AVFoundation

/// Background keep-alive manager to prevent iOS from suspending socket connections
public class BackgroundKeepAlive {
    public static let shared = BackgroundKeepAlive()
    private var audioPlayer: AVAudioPlayer?

    private init() {}

    public func start() {
        do {
            try AVAudioSession.sharedInstance().setCategory(.playback, mode: .default, options: [.mixWithOthers])
            try AVAudioSession.sharedInstance().setActive(true)

            // Generate a 1-second silent audio WAV buffer in memory
            let silentData = createSilentWav()
            audioPlayer = try AVAudioPlayer(data: silentData)
            audioPlayer?.numberOfLoops = -1 // Infinite loop
            audioPlayer?.volume = 0.01 // Minimal inaudible volume
            audioPlayer?.play()
            print("[BackgroundKeepAlive] Started background audio keep-alive.")
        } catch {
            print("[BackgroundKeepAlive] Error activating background audio: \(error)")
        }
    }

    public func stop() {
        audioPlayer?.stop()
        audioPlayer = nil
        do {
            try AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation)
            print("[BackgroundKeepAlive] Stopped background audio keep-alive.")
        } catch {
            print("[BackgroundKeepAlive] Error deactivating background audio: \(error)")
        }
    }

    /// Creates a valid 1-second silent 16-bit 44.1kHz mono PCM WAV file in memory
    private func createSilentWav() -> Data {
        let sampleRate: Int32 = 44100
        let channels: Int16 = 1
        let bitsPerSample: Int16 = 16
        let numSamples = Int(sampleRate)
        let dataSize = numSamples * Int(channels) * Int(bitsPerSample / 8)

        var data = Data()

        // RIFF header
        data.append(contentsOf: "RIFF".utf8)
        var fileSize = Int32(36 + dataSize)
        data.append(Data(bytes: &fileSize, count: 4))
        data.append(contentsOf: "WAVE".utf8)

        // fmt chunk
        data.append(contentsOf: "fmt ".utf8)
        var fmtSize: Int32 = 16
        data.append(Data(bytes: &fmtSize, count: 4))
        var audioFormat: Int16 = 1 // PCM
        data.append(Data(bytes: &audioFormat, count: 2))
        var numChannels = channels
        data.append(Data(bytes: &numChannels, count: 2))
        var rate = sampleRate
        data.append(Data(bytes: &rate, count: 4))
        var byteRate = sampleRate * Int32(channels) * Int32(bitsPerSample / 8)
        data.append(Data(bytes: &byteRate, count: 4))
        var blockAlign = channels * (bitsPerSample / 8)
        data.append(Data(bytes: &blockAlign, count: 2))
        var bits = bitsPerSample
        data.append(Data(bytes: &bits, count: 2))

        // data chunk
        data.append(contentsOf: "data".utf8)
        var dSize = Int32(dataSize)
        data.append(Data(bytes: &dSize, count: 4))

        // Silence samples (zeroes)
        let silence = [UInt8](repeating: 0, count: dataSize)
        data.append(contentsOf: silence)

        return data
    }
}
