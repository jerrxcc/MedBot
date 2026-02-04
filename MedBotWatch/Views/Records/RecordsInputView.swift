//
//  RecordsInputView.swift
//  MedBotWatch
//
//  Input medical records for analysis
//

import SwiftUI

struct RecordsInputView: View {
    @StateObject private var viewModel = RecordsViewModel()
    @StateObject private var voiceService = VoiceService.shared
    @EnvironmentObject var settingsManager: SettingsManager
    @State private var showResult = false

    let recordTypes = [
        ("general", "records_type_general"),
        ("lab", "records_type_lab"),
        ("diagnosis", "records_type_diagnosis"),
        ("prescription", "records_type_prescription")
    ]

    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                // Record type picker
                Text(LocalizedStringKey("records_select_type"))
                    .font(.caption2)
                    .foregroundColor(.secondary)

                Picker("Type", selection: $viewModel.recordType) {
                    ForEach(recordTypes, id: \.0) { type in
                        Text(LocalizedStringKey(type.1)).tag(type.0)
                    }
                }
                .pickerStyle(.wheel)
                .frame(height: 60)

                // Voice input for record content
                CompactVoiceInput(
                    text: $viewModel.content,
                    placeholder: NSLocalizedString("records_placeholder", comment: "Enter lab values...")
                )

                // Example values
                Text(LocalizedStringKey("records_example"))
                    .font(.caption2)
                    .foregroundColor(.secondary)

                Button(action: {
                    viewModel.content = "HbA1c: 7.2%, Glucose: 130 mg/dL"
                }) {
                    Text("HbA1c: 7.2%")
                        .font(.caption2)
                }
                .buttonStyle(.bordered)

                // Analyze button
                if !viewModel.content.isEmpty {
                    Button(action: {
                        Task {
                            await viewModel.analyzeRecords(
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
        .localizedNavTitle("feature_records")
        .navigationDestination(isPresented: $showResult) {
            if let response = viewModel.response {
                RecordsResultView(response: response)
            }
        }
    }
}

struct RecordsResultView: View {
    let response: RecordsResponse

    var body: some View {
        ScrollView {
            VStack(spacing: 12) {
                // Severity badge
                LargeSeverityBadge(
                    severity: response.summary.severity,
                    action: response.summary.action
                )

                // Summary
                Text(response.summary.short)
                    .font(.caption)
                    .fontWeight(.medium)
                    .multilineTextAlignment(.center)

                // Confidence
                ConfidenceIndicator(
                    confidence: response.confidence,
                    level: response.confidenceLevel
                )
                .padding(.horizontal)

                Divider()

                // Abnormal values section
                if let abnormals = response.abnormalValues, !abnormals.isEmpty {
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Image(systemName: "exclamationmark.circle.fill")
                                .foregroundColor(.orange)
                            Text(LocalizedStringKey("records_abnormal"))
                                .font(.caption)
                                .fontWeight(.semibold)
                        }

                        ForEach(abnormals, id: \.self) { value in
                            Text("• \(value)")
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
        .localizedNavTitle("result_records")
    }
}
