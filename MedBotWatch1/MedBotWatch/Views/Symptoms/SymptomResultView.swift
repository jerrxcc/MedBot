//
//  SymptomResultView.swift
//  MedBotWatch
//
//  Display symptom analysis results with TTS playback
//

import SwiftUI

struct SymptomResultView: View {
    let response: SymptomResponse
    @StateObject private var ttsService = TTSService.shared

    var body: some View {
        ScrollView {
            VStack(spacing: 12) {
                // Severity and action badges
                LargeSeverityBadge(
                    severity: response.summary.severity,
                    action: response.summary.action
                )

                Divider()

                // Summary text
                Text(stripMarkdown(response.summary.short))
                    .font(.caption)
                    .fontWeight(.medium)
                    .multilineTextAlignment(.center)

                // TTS play/stop button
                Button(action: {
                    if ttsService.isSpeaking {
                        Task { await ttsService.stop() }
                    } else {
                        Task { await ttsService.speak(text: stripMarkdown(response.fullResponse)) }
                    }
                }) {
                    if ttsService.isLoading {
                        ProgressView()
                            .frame(height: 20)
                    } else {
                        Label(
                            ttsService.isSpeaking
                                ? L("tts_stop")
                                : L("tts_listen"),
                            systemImage: ttsService.isSpeaking ? "stop.fill" : "speaker.wave.2"
                        )
                        .font(.caption2)
                    }
                }
                .buttonStyle(.bordered)

                // TTS error message
                if let ttsError = ttsService.errorMessage {
                    Text(ttsError)
                        .font(.system(size: 10))
                        .foregroundColor(.orange)
                        .multilineTextAlignment(.center)
                }

                // Confidence indicator
                ConfidenceIndicator(
                    confidence: response.confidence,
                    level: response.confidenceLevel
                )
                .padding(.horizontal)

                Divider()

                // Full response
                Text(stripMarkdown(response.fullResponse))
                    .font(.caption2)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.leading)
                    .frame(maxWidth: .infinity, alignment: .leading)

                // Source count
                HStack {
                    Image(systemName: "doc.text")
                        .font(.caption2)
                    Text("\(response.sourcesCount) sources")
                        .font(.caption2)
                }
                .foregroundColor(.secondary)

                // Emergency action button
                if response.summary.action == .emergency {
                    Button(action: {
                        // Open phone app for emergency call
                    }) {
                        HStack {
                            Image(systemName: "phone.fill")
                            Text(LocalizedStringKey("button_emergency"))
                        }
                    }
                    .buttonStyle(.borderedProminent)
                    .tint(.red)
                }
            }
            .padding()
        }
        .localizedNavTitle("result_symptoms")
    }
}

/// Strip common markdown formatting for plain-text display
private func stripMarkdown(_ text: String) -> String {
    var s = text
    // Remove bold: **text** or __text__
    s = s.replacingOccurrences(of: "\\*\\*(.+?)\\*\\*", with: "$1", options: .regularExpression)
    s = s.replacingOccurrences(of: "__(.+?)__", with: "$1", options: .regularExpression)
    // Remove italic: *text* or _text_
    s = s.replacingOccurrences(of: "\\*(.+?)\\*", with: "$1", options: .regularExpression)
    // Remove headings: ### text
    s = s.replacingOccurrences(of: "(?m)^#{1,4}\\s*", with: "", options: .regularExpression)
    // Clean up stray asterisks
    s = s.replacingOccurrences(of: "\\*", with: "")
    return s.trimmingCharacters(in: .whitespacesAndNewlines)
}

#Preview {
    SymptomResultView(response: SymptomResponse(
        success: true,
        summary: WatchSummary(
            short: "May indicate tension headache",
            severity: .medium,
            action: .selfCare
        ),
        fullResponse: "Based on your symptoms of headache and fatigue, this may indicate a tension headache. Consider rest, hydration, and over-the-counter pain relievers if needed. If symptoms persist for more than 48 hours or worsen, please consult a doctor.",
        confidence: 0.78,
        confidenceLevel: "high",
        sourcesCount: 5,
        languageDetected: "en"
    ))
}
