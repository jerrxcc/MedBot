//
//  MedicationSearchView.swift
//  MedBotWatch
//
//  Search and lookup medication information
//

import SwiftUI

struct MedicationSearchView: View {
    @StateObject private var viewModel = MedicationViewModel()
    @StateObject private var voiceService = VoiceService.shared
    @EnvironmentObject var settingsManager: SettingsManager
    @State private var showResult = false

    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                // Voice input
                CompactVoiceInput(
                    text: $viewModel.query,
                    placeholder: NSLocalizedString("medication_placeholder", comment: "Enter drug name...")
                )

                // Common medications quick buttons
                Text(LocalizedStringKey("medication_common"))
                    .font(.caption2)
                    .foregroundColor(.secondary)

                LazyVGrid(columns: [
                    GridItem(.flexible()),
                    GridItem(.flexible())
                ], spacing: 8) {
                    QuickMedicationButton(name: "Paracetamol", query: $viewModel.query)
                    QuickMedicationButton(name: "Ibuprofen", query: $viewModel.query)
                    QuickMedicationButton(name: "Aspirin", query: $viewModel.query)
                    QuickMedicationButton(name: "Antibiotic", query: $viewModel.query)
                }

                // Search button
                if !viewModel.query.isEmpty {
                    Button(action: {
                        Task {
                            await viewModel.lookupMedication(
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
                            Text(LocalizedStringKey("button_search"))
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
        .localizedNavTitle("feature_medication")
        .navigationDestination(isPresented: $showResult) {
            if let response = viewModel.response {
                MedicationResultView(response: response)
            }
        }
    }
}

struct QuickMedicationButton: View {
    let name: String
    @Binding var query: String

    var body: some View {
        Button(action: {
            query = name
        }) {
            Text(name)
                .font(.caption2)
                .lineLimit(1)
        }
        .buttonStyle(.bordered)
    }
}

struct MedicationResultView: View {
    let response: MedicationResponse

    var body: some View {
        ScrollView {
            VStack(spacing: 12) {
                // Drug name if identified
                if let drugName = response.drugName {
                    Text(drugName)
                        .font(.headline)
                }

                // Summary
                Text(response.summary.short)
                    .font(.caption)
                    .multilineTextAlignment(.center)

                // Confidence
                ConfidenceIndicator(
                    confidence: response.confidence,
                    level: response.confidenceLevel
                )
                .padding(.horizontal)

                Divider()

                // Warnings section
                if let warnings = response.warnings, !warnings.isEmpty {
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Image(systemName: "exclamationmark.triangle.fill")
                                .foregroundColor(.orange)
                            Text(LocalizedStringKey("medication_warnings"))
                                .font(.caption)
                                .fontWeight(.semibold)
                        }

                        ForEach(warnings, id: \.self) { warning in
                            Text("• \(warning)")
                                .font(.caption2)
                                .foregroundColor(.orange)
                        }
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding()
                    .background(Color.orange.opacity(0.1))
                    .cornerRadius(8)

                    Divider()
                }

                // Full response
                Text(response.fullResponse)
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
            }
            .padding()
        }
        .localizedNavTitle("result_medication")
    }
}
