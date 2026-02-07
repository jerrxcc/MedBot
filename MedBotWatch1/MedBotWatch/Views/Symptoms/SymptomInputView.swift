//
//  SymptomInputView.swift
//  MedBotWatch
//
//  Voice and text input for symptom analysis
//

import SwiftUI

struct SymptomInputView: View {
    @StateObject private var viewModel = SymptomViewModel()
    @EnvironmentObject var settingsManager: SettingsManager
    @State private var showResult = false

    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                // Text input with dictation (tap to get watchOS keyboard + mic)
                TextField(
                    L("symptom_tap_or_speak"),
                    text: $viewModel.query
                )
                .font(.caption)
                .textFieldStyle(.plain)
                .padding(8)
                .background(Color.gray.opacity(0.15))
                .cornerRadius(8)

                // Quick symptom buttons
                VStack(spacing: 8) {
                    QuickSymptomButton(
                        text: L("quick_headache"),
                        query: $viewModel.query
                    )
                    QuickSymptomButton(
                        text: L("quick_fever"),
                        query: $viewModel.query
                    )
                    QuickSymptomButton(
                        text: L("quick_cough"),
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
