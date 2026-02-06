//
//  SymptomInputView.swift
//  MedBotWatch
//
//  Voice and text input for symptom analysis
//

import SwiftUI

struct SymptomInputView: View {
    @StateObject private var viewModel = SymptomViewModel()
    @StateObject private var voiceService = VoiceService.shared
    @EnvironmentObject var settingsManager: SettingsManager
    @State private var showResult = false

    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                // Voice input button
                VoiceInputButton(
                    voiceService: voiceService,
                    transcribedText: $viewModel.query
                )

                // Transcribed/typed text
                if !viewModel.query.isEmpty {
                    Text(viewModel.query)
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .lineLimit(3)
                        .padding(.horizontal)
                }

                // Or type input
                Text(LocalizedStringKey("symptom_tap_or_speak"))
                    .font(.caption2)
                    .foregroundColor(.secondary)

                // Quick symptom buttons
                VStack(spacing: 8) {
                    QuickSymptomButton(
                        text: NSLocalizedString("quick_headache", comment: "Headache"),
                        query: $viewModel.query
                    )
                    QuickSymptomButton(
                        text: NSLocalizedString("quick_fever", comment: "Fever"),
                        query: $viewModel.query
                    )
                    QuickSymptomButton(
                        text: NSLocalizedString("quick_cough", comment: "Cough"),
                        query: $viewModel.query
                    )
                }

                // Analyze button
                if !viewModel.query.isEmpty {
                    Button(action: {
                        Task {
                            await viewModel.analyzeSymptoms(
                                language: settingsManager.language.rawValue
                            )
                            if viewModel.hasResponse {
                                showResult = true
                            }
                        }
                    }) {
                        if viewModel.isLoading {
                            ProgressView()
                        } else {
                            Text(LocalizedStringKey("button_analyze"))
                        }
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(viewModel.isLoading)
                }

                // Error message
                if let error = viewModel.errorMessage {
                    Text(error)
                        .font(.caption2)
                        .foregroundColor(.red)
                        .multilineTextAlignment(.center)
                }
            }
            .padding()
        }
        .localizedNavTitle("feature_symptoms")
        .navigationDestination(isPresented: $showResult) {
            if let response = viewModel.response {
                SymptomResultView(response: response)
            }
        }
    }
}

struct QuickSymptomButton: View {
    let text: String
    @Binding var query: String

    var body: some View {
        Button(action: {
            if query.isEmpty {
                query = text
            } else {
                query += ", \(text.lowercased())"
            }
        }) {
            Text(text)
                .font(.caption2)
                .frame(maxWidth: .infinity)
        }
        .buttonStyle(.bordered)
    }
}
