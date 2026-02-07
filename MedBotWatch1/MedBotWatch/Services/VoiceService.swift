//
//  VoiceService.swift
//  MedBotWatch
//
//  Voice input service for watchOS
//  Uses watchOS native dictation (Speech framework is NOT available on watchOS)
//

import Foundation

/// Manages voice input state for watchOS
/// On watchOS, voice input is handled via system dictation (TextField's built-in mic button)
class VoiceService: NSObject, ObservableObject {
    static let shared = VoiceService()

    @Published var isRecording = false
    @Published var transcribedText = ""
    @Published var errorMessage: String?
    @Published var audioLevel: Float = 0.0

    override init() {
        super.init()
    }

    /// Set the language for speech recognition (no-op on watchOS, system handles it)
    func setLanguage(_ language: AppLanguage) {
        // watchOS uses system language settings for dictation
    }

    @MainActor
    func startRecording() async {
        // On watchOS, dictation is handled by the system via TextField
        // This is kept for API compatibility with VoiceInputButton
        isRecording = true
    }

    @MainActor
    func stopRecording() {
        isRecording = false
        audioLevel = 0
    }
}
