//
//  TTSService.swift
//  MedBotWatch
//
//  MiniMax T2A v2 TTS client for voice output on Apple Watch
//

import Foundation
import AVFoundation

/// Text-to-speech service using MiniMax T2A v2 API
class TTSService: NSObject, ObservableObject, AVAudioPlayerDelegate {
    static let shared = TTSService()

    @Published var isSpeaking = false
    @Published var isLoading = false
    @Published var errorMessage: String?

    private var audioPlayer: AVAudioPlayer?
    private let session: URLSession
    private let maxTextLength = 200

    override init() {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 15
        config.timeoutIntervalForResource = 30
        self.session = URLSession(configuration: config)
        super.init()
    }

    // MARK: - Public API

    /// Speak the given text using MiniMax TTS
    /// - Parameters:
    ///   - text: Text to speak (truncated to 200 chars)
    ///   - voiceId: MiniMax voice ID (default: "male-qn-qingse")
    @MainActor
    func speak(text: String, voiceId: String = "male-qn-qingse") async {
        // Stop any active voice recording to avoid audio session conflict
        VoiceService.shared.stopRecording()

        guard !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }

        let apiKey = UserDefaults.standard.string(forKey: "minimax_api_key") ?? ""
        let groupId = UserDefaults.standard.string(forKey: "minimax_group_id") ?? ""

        guard !apiKey.isEmpty, !groupId.isEmpty else {
            errorMessage = "MiniMax API key or Group ID not configured"
            return
        }

        // Truncate text for bandwidth
        let truncatedText = String(text.prefix(maxTextLength))

        isLoading = true
        errorMessage = nil

        do {
            let audioData = try await requestTTS(
                text: truncatedText,
                voiceId: voiceId,
                apiKey: apiKey,
                groupId: groupId
            )

            try playAudio(data: audioData)
        } catch {
            errorMessage = error.localizedDescription
            isLoading = false
        }
    }

    /// Stop current playback
    @MainActor
    func stop() {
        audioPlayer?.stop()
        audioPlayer = nil
        isSpeaking = false
        isLoading = false
    }

    // MARK: - Private

    private func requestTTS(
        text: String,
        voiceId: String,
        apiKey: String,
        groupId: String
    ) async throws -> Data {
        guard let url = URL(string: "https://api.minimax.chat/v1/t2a_v2?GroupId=\(groupId)") else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(apiKey)", forHTTPHeaderField: "Authorization")

        let body: [String: Any] = [
            "model": "speech-01-turbo",
            "text": text,
            "stream": false,
            "voice_setting": [
                "voice_id": voiceId,
                "speed": 1.0,
                "vol": 1.0,
                "pitch": 0
            ],
            "audio_setting": [
                "sample_rate": 16000,
                "format": "mp3"
            ]
        ]

        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            let statusCode = (response as? HTTPURLResponse)?.statusCode ?? 0
            throw APIError.serverError("TTS API returned status \(statusCode)")
        }

        // Parse response - MiniMax returns JSON with base64 audio data
        guard let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
              let audioDict = json["data"] as? [String: Any],
              let audioBase64 = audioDict["audio"] as? String,
              let audioData = Data(base64Encoded: audioBase64) else {
            throw APIError.decodingError(
                NSError(domain: "TTSService", code: -1,
                        userInfo: [NSLocalizedDescriptionKey: "Failed to decode TTS audio"])
            )
        }

        return audioData
    }

    private func playAudio(data: Data) throws {
        let audioSession = AVAudioSession.sharedInstance()
        try audioSession.setCategory(.playback, mode: .default)
        try audioSession.setActive(true)

        audioPlayer = try AVAudioPlayer(data: data)
        audioPlayer?.delegate = self
        audioPlayer?.play()

        DispatchQueue.main.async {
            self.isLoading = false
            self.isSpeaking = true
        }
    }

    // MARK: - AVAudioPlayerDelegate

    func audioPlayerDidFinishPlaying(_ player: AVAudioPlayer, successfully flag: Bool) {
        DispatchQueue.main.async {
            self.isSpeaking = false
        }
    }

    func audioPlayerDecodeErrorDidOccur(_ player: AVAudioPlayer, error: Error?) {
        DispatchQueue.main.async {
            self.isSpeaking = false
            self.errorMessage = error?.localizedDescription ?? "Audio playback error"
        }
    }
}
