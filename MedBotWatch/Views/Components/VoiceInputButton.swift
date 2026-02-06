//
//  VoiceInputButton.swift
//  MedBotWatch
//
//  Microphone button with audio waveform visualization
//

import SwiftUI

struct VoiceInputButton: View {
    @ObservedObject var voiceService: VoiceService
    @Binding var transcribedText: String

    var body: some View {
        Button(action: {
            Task {
                if voiceService.isRecording {
                    await voiceService.stopRecording()
                    transcribedText = voiceService.transcribedText
                } else {
                    await voiceService.startRecording()
                }
            }
        }) {
            ZStack {
                // Background circle
                Circle()
                    .fill(voiceService.isRecording ? Color.red : Color.blue)
                    .frame(width: 60, height: 60)

                // Waveform visualization when recording
                if voiceService.isRecording {
                    WaveformView(level: voiceService.audioLevel)
                        .frame(width: 40, height: 20)
                } else {
                    Image(systemName: "mic.fill")
                        .font(.system(size: 24))
                        .foregroundColor(.white)
                }
            }
        }
        .buttonStyle(PlainButtonStyle())
        .accessibilityLabel(voiceService.isRecording ?
            NSLocalizedString("voice_stop", comment: "Stop recording") :
            NSLocalizedString("voice_start", comment: "Start recording"))
    }
}

struct WaveformView: View {
    let level: Float
    let barCount = 5

    var body: some View {
        HStack(spacing: 2) {
            ForEach(0..<barCount, id: \.self) { index in
                WaveformBar(level: level, index: index)
            }
        }
    }
}

struct WaveformBar: View {
    let level: Float
    let index: Int

    @State private var animatedHeight: CGFloat = 4

    var body: some View {
        RoundedRectangle(cornerRadius: 1)
            .fill(Color.white)
            .frame(width: 4, height: animatedHeight)
            .onChange(of: level) { _, newLevel in
                withAnimation(.easeInOut(duration: 0.1)) {
                    // Create slight variation based on index
                    let variation = Float(abs(index - 2)) * 0.1
                    let adjustedLevel = max(0.2, min(1.0, newLevel + variation))
                    animatedHeight = CGFloat(adjustedLevel) * 20
                }
            }
    }
}

// Compact voice input for inline use
struct CompactVoiceInput: View {
    @StateObject private var voiceService = VoiceService.shared
    @Binding var text: String
    let placeholder: String

    var body: some View {
        HStack {
            if voiceService.isRecording {
                Text(voiceService.transcribedText.isEmpty ?
                    NSLocalizedString("voice_listening", comment: "Listening...") :
                    voiceService.transcribedText)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .lineLimit(2)
            } else if text.isEmpty {
                Text(placeholder)
                    .font(.caption)
                    .foregroundColor(.secondary)
            } else {
                Text(text)
                    .font(.caption)
                    .lineLimit(2)
            }

            Spacer()

            Button(action: {
                Task {
                    if voiceService.isRecording {
                        await voiceService.stopRecording()
                        text = voiceService.transcribedText
                    } else {
                        await voiceService.startRecording()
                    }
                }
            }) {
                Image(systemName: voiceService.isRecording ? "stop.circle.fill" : "mic.circle.fill")
                    .font(.title2)
                    .foregroundColor(voiceService.isRecording ? .red : .blue)
            }
            .buttonStyle(PlainButtonStyle())
        }
        .padding(.vertical, 8)
    }
}
