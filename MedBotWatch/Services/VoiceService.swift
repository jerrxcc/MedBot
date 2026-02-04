//
//  VoiceService.swift
//  MedBotWatch
//
//  Speech recognition service supporting English and Chinese
//

import Foundation
import Speech
import AVFoundation

/// Manages speech recognition for voice input
class VoiceService: NSObject, ObservableObject {
    static let shared = VoiceService()

    @Published var isRecording = false
    @Published var transcribedText = ""
    @Published var errorMessage: String?
    @Published var audioLevel: Float = 0.0

    private var audioEngine: AVAudioEngine?
    private var speechRecognizer: SFSpeechRecognizer?
    private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    private var recognitionTask: SFSpeechRecognitionTask?

    private var currentLocale: Locale = Locale(identifier: "en-US")

    override init() {
        super.init()
        setupDefaultRecognizer()
    }

    // MARK: - Setup

    private func setupDefaultRecognizer() {
        // Default to English
        speechRecognizer = SFSpeechRecognizer(locale: Locale(identifier: "en-US"))
    }

    /// Set the language for speech recognition
    func setLanguage(_ language: AppLanguage) {
        let localeIdentifier: String
        switch language {
        case .english, .auto:
            localeIdentifier = "en-US"
        case .chinese:
            localeIdentifier = "zh-Hans"
        }

        currentLocale = Locale(identifier: localeIdentifier)
        speechRecognizer = SFSpeechRecognizer(locale: currentLocale)
    }

    // MARK: - Permissions

    func requestPermissions() async -> Bool {
        // Request speech recognition permission
        let speechStatus = await withCheckedContinuation { continuation in
            SFSpeechRecognizer.requestAuthorization { status in
                continuation.resume(returning: status)
            }
        }

        guard speechStatus == .authorized else {
            await MainActor.run {
                errorMessage = NSLocalizedString("error_speech_permission", comment: "Speech permission denied")
            }
            return false
        }

        // Request microphone permission
        let audioStatus = await AVAudioApplication.requestRecordPermission()
        guard audioStatus else {
            await MainActor.run {
                errorMessage = NSLocalizedString("error_mic_permission", comment: "Microphone permission denied")
            }
            return false
        }

        return true
    }

    // MARK: - Recording

    @MainActor
    func startRecording() async {
        // Check permissions first
        guard await requestPermissions() else { return }

        guard let recognizer = speechRecognizer, recognizer.isAvailable else {
            errorMessage = NSLocalizedString("error_speech_unavailable", comment: "Speech recognition unavailable")
            return
        }

        // Reset state
        transcribedText = ""
        errorMessage = nil

        // Setup audio engine
        audioEngine = AVAudioEngine()

        guard let audioEngine = audioEngine else { return }

        // Create recognition request
        recognitionRequest = SFSpeechAudioBufferRecognitionRequest()

        guard let recognitionRequest = recognitionRequest else { return }

        recognitionRequest.shouldReportPartialResults = true
        recognitionRequest.taskHint = .dictation

        // Configure audio session for watchOS
        let audioSession = AVAudioSession.sharedInstance()
        do {
            try audioSession.setCategory(.record, mode: .measurement, options: .duckOthers)
            try audioSession.setActive(true, options: .notifyOthersOnDeactivation)
        } catch {
            errorMessage = "Audio session error: \(error.localizedDescription)"
            return
        }

        // Get input node
        let inputNode = audioEngine.inputNode
        let recordingFormat = inputNode.outputFormat(forBus: 0)

        // Install tap for audio
        inputNode.installTap(onBus: 0, bufferSize: 1024, format: recordingFormat) { [weak self] buffer, _ in
            self?.recognitionRequest?.append(buffer)

            // Calculate audio level for visualization
            let level = self?.calculateAudioLevel(buffer: buffer) ?? 0
            DispatchQueue.main.async {
                self?.audioLevel = level
            }
        }

        // Start recognition task
        recognitionTask = recognizer.recognitionTask(with: recognitionRequest) { [weak self] result, error in
            guard let self = self else { return }

            if let result = result {
                DispatchQueue.main.async {
                    self.transcribedText = result.bestTranscription.formattedString
                }
            }

            if error != nil || (result?.isFinal ?? false) {
                self.stopRecordingInternal()
            }
        }

        // Start audio engine
        do {
            audioEngine.prepare()
            try audioEngine.start()
            isRecording = true
        } catch {
            errorMessage = "Could not start recording: \(error.localizedDescription)"
            stopRecordingInternal()
        }
    }

    @MainActor
    func stopRecording() {
        stopRecordingInternal()
    }

    private func stopRecordingInternal() {
        audioEngine?.stop()
        audioEngine?.inputNode.removeTap(onBus: 0)
        recognitionRequest?.endAudio()

        recognitionTask?.cancel()
        recognitionTask = nil
        recognitionRequest = nil
        audioEngine = nil

        DispatchQueue.main.async {
            self.isRecording = false
            self.audioLevel = 0
        }
    }

    // MARK: - Audio Level

    private func calculateAudioLevel(buffer: AVAudioPCMBuffer) -> Float {
        guard let channelData = buffer.floatChannelData else { return 0 }

        let channelDataValue = channelData.pointee
        let channelDataValueArray = stride(
            from: 0,
            to: Int(buffer.frameLength),
            by: buffer.stride
        ).map { channelDataValue[$0] }

        let rms = sqrt(channelDataValueArray.map { $0 * $0 }.reduce(0, +) / Float(buffer.frameLength))
        let avgPower = 20 * log10(rms)

        // Normalize to 0-1 range
        let minDb: Float = -60
        let maxDb: Float = 0
        let normalized = max(0, min(1, (avgPower - minDb) / (maxDb - minDb)))

        return normalized
    }
}
