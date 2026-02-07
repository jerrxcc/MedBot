//
//  TTSService.swift
//  MedBotWatch
//
//  Text-to-speech service using Apple AVSpeechSynthesizer (works offline on watchOS)
//

import Foundation
import AVFoundation

/// Text-to-speech service using Apple's built-in AVSpeechSynthesizer
class TTSService: NSObject, ObservableObject, AVSpeechSynthesizerDelegate {
    static let shared = TTSService()

    @Published var isSpeaking = false
    @Published var isLoading = false
    @Published var errorMessage: String?

    private let synthesizer = AVSpeechSynthesizer()

    override init() {
        super.init()
        synthesizer.delegate = self
    }

    // MARK: - Public API

    /// Speak the given text using Apple TTS
    @MainActor
    func speak(text: String, voiceId: String = "") async {
        // Stop any active voice recording to avoid audio session conflict
        VoiceService.shared.stopRecording()

        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }

        // Stop current speech if any
        if synthesizer.isSpeaking {
            synthesizer.stopSpeaking(at: .immediate)
        }

        isLoading = true
        errorMessage = nil

        do {
            let audioSession = AVAudioSession.sharedInstance()
            try audioSession.setCategory(.playback, mode: .default)
            try audioSession.setActive(true)
        } catch {
            errorMessage = "Audio session error: \(error.localizedDescription)"
            isLoading = false
            return
        }

        let utterance = AVSpeechUtterance(string: trimmed)
        utterance.rate = AVSpeechUtteranceDefaultSpeechRate
        utterance.volume = 1.0

        // Auto-detect language and pick a voice
        if let voice = pickVoice(for: trimmed) {
            utterance.voice = voice
        }

        synthesizer.speak(utterance)
    }

    /// Stop current playback
    @MainActor
    func stop() {
        synthesizer.stopSpeaking(at: .immediate)
        isSpeaking = false
        isLoading = false
    }

    // MARK: - Voice Selection

    private func pickVoice(for text: String) -> AVSpeechSynthesisVoice? {
        // Check if text contains Chinese characters
        let hasChinese = text.unicodeScalars.contains { scalar in
            (0x4E00...0x9FFF).contains(scalar.value) ||
            (0x3400...0x4DBF).contains(scalar.value)
        }

        let langCode = hasChinese ? "zh-CN" : "en-US"

        // Prefer enhanced/premium voices if available
        let voices = AVSpeechSynthesisVoice.speechVoices().filter { $0.language == langCode }
        if let enhanced = voices.first(where: { $0.quality == .enhanced }) {
            return enhanced
        }
        return AVSpeechSynthesisVoice(language: langCode)
    }

    // MARK: - AVSpeechSynthesizerDelegate

    func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didStart utterance: AVSpeechUtterance) {
        DispatchQueue.main.async {
            self.isLoading = false
            self.isSpeaking = true
        }
    }

    func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didFinish utterance: AVSpeechUtterance) {
        DispatchQueue.main.async {
            self.isSpeaking = false
        }
    }

    func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didCancel utterance: AVSpeechUtterance) {
        DispatchQueue.main.async {
            self.isSpeaking = false
        }
    }
}
