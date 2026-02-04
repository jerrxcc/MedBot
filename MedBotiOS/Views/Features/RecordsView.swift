//
//  RecordsView.swift
//  MedBotiOS
//
//  Medical records analysis view
//

import SwiftUI

struct RecordsView: View {
    @EnvironmentObject var settingsManager: SettingsManager
    @EnvironmentObject var historyService: HistoryService

    @State private var content = ""
    @State private var recordType = "general"
    @State private var isLoading = false
    @State private var response: RecordsResponse?
    @State private var errorMessage: String?

    let recordTypes = [
        ("general", "General"),
        ("lab", "Lab Results"),
        ("diagnosis", "Diagnosis"),
        ("prescription", "Prescription")
    ]

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 20) {
                    // Record type picker
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Record Type")
                            .font(.headline)

                        Picker("Type", selection: $recordType) {
                            ForEach(recordTypes, id: \.0) { type in
                                Text(type.1).tag(type.0)
                            }
                        }
                        .pickerStyle(.segmented)
                    }

                    // Input area
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Enter Medical Record")
                            .font(.headline)

                        TextEditor(text: $content)
                            .frame(minHeight: 150)
                            .padding(8)
                            .background(Color(.secondarySystemBackground))
                            .cornerRadius(8)

                        // Example button
                        Button("Use Example") {
                            content = "HbA1c: 7.2%\nFasting Glucose: 130 mg/dL\nTotal Cholesterol: 220 mg/dL\nHDL: 45 mg/dL\nLDL: 150 mg/dL"
                        }
                        .font(.caption)
                    }

                    // Analyze button
                    Button(action: analyzeRecords) {
                        if isLoading {
                            ProgressView()
                                .frame(maxWidth: .infinity)
                        } else {
                            Text("Analyze Records")
                                .frame(maxWidth: .infinity)
                        }
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(content.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || isLoading)

                    // Response card
                    if let response = response {
                        RecordsResponseCard(response: response)
                    }

                    // Error message
                    if let error = errorMessage {
                        ErrorCard(message: error) {
                            errorMessage = nil
                        }
                    }
                }
                .padding()
            }
            .navigationTitle("Records Analysis")
        }
    }

    private func analyzeRecords() {
        guard !content.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }

        isLoading = true
        errorMessage = nil

        Task {
            do {
                let result = try await APIService.shared.analyzeRecords(
                    content: content,
                    language: settingsManager.language.rawValue,
                    recordType: recordType
                )

                await MainActor.run {
                    response = result

                    // Save to history
                    historyService.addItem(
                        type: .records,
                        query: content,
                        response: result.fullResponse,
                        summary: result.summary.short
                    )

                    isLoading = false
                }
            } catch {
                await MainActor.run {
                    errorMessage = error.localizedDescription
                    isLoading = false
                }
            }
        }
    }
}

struct RecordsResponseCard: View {
    let response: RecordsResponse

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            // Severity header
            HStack {
                SeverityBadge(severity: response.summary.severity)
                Spacer()
                ActionBadge(action: response.summary.action)
            }

            // Summary
            Text(response.summary.short)
                .font(.headline)

            Divider()

            // Abnormal values section
            if let abnormals = response.abnormalValues, !abnormals.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Image(systemName: "exclamationmark.circle.fill")
                            .foregroundColor(.orange)
                        Text("Abnormal Values")
                            .font(.headline)
                    }

                    ForEach(abnormals, id: \.self) { value in
                        HStack(alignment: .top) {
                            Text("•")
                            Text(value)
                                .font(.subheadline)
                        }
                        .foregroundColor(.orange)
                    }
                }
                .padding()
                .background(Color.orange.opacity(0.1))
                .cornerRadius(8)

                Divider()
            }

            // Full response
            Text(response.fullResponse)
                .font(.body)

            // Confidence
            HStack {
                ConfidenceView(confidence: response.confidence, level: response.confidenceLevel)
                Spacer()
                Label("\(response.sourcesCount) sources", systemImage: "doc.text")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(radius: 2)
    }
}
