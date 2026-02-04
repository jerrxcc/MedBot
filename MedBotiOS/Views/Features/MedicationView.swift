//
//  MedicationView.swift
//  MedBotiOS
//
//  Medication lookup view with full drug information
//

import SwiftUI

struct MedicationView: View {
    @EnvironmentObject var settingsManager: SettingsManager
    @EnvironmentObject var historyService: HistoryService

    @State private var query = ""
    @State private var isLoading = false
    @State private var response: MedicationResponse?
    @State private var errorMessage: String?

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 20) {
                    // Response card
                    if let response = response {
                        MedicationResponseCard(response: response)
                    }

                    // Error message
                    if let error = errorMessage {
                        ErrorCard(message: error) {
                            errorMessage = nil
                        }
                    }

                    // Quick search suggestions
                    if response == nil {
                        QuickSearchSection(onSelect: { drug in
                            query = drug
                            lookupMedication()
                        })
                    }

                    Spacer(minLength: 100)
                }
                .padding()
            }
            .navigationTitle("Medication Lookup")
            .safeAreaInset(edge: .bottom) {
                InputBar(
                    text: $query,
                    placeholder: "Enter drug name or question...",
                    isLoading: isLoading,
                    onSubmit: lookupMedication
                )
            }
        }
    }

    private func lookupMedication() {
        guard !query.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }

        isLoading = true
        errorMessage = nil

        Task {
            do {
                let result = try await APIService.shared.lookupMedication(
                    query: query,
                    language: settingsManager.language.rawValue
                )

                await MainActor.run {
                    response = result

                    // Save to history
                    historyService.addItem(
                        type: .medication,
                        query: query,
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

struct MedicationResponseCard: View {
    let response: MedicationResponse

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            // Drug name header
            if let drugName = response.drugName {
                HStack {
                    Image(systemName: "pill.fill")
                        .foregroundColor(.green)
                    Text(drugName)
                        .font(.title2)
                        .fontWeight(.bold)
                }
            }

            // Summary
            Text(response.summary.short)
                .font(.headline)
                .foregroundColor(.secondary)

            Divider()

            // Warnings section
            if let warnings = response.warnings, !warnings.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Image(systemName: "exclamationmark.triangle.fill")
                            .foregroundColor(.orange)
                        Text("Warnings")
                            .font(.headline)
                    }

                    ForEach(warnings, id: \.self) { warning in
                        HStack(alignment: .top) {
                            Text("•")
                            Text(warning)
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

struct QuickSearchSection: View {
    let onSelect: (String) -> Void

    let commonDrugs = [
        "Paracetamol", "Ibuprofen", "Aspirin", "Amoxicillin",
        "Metformin", "Omeprazole", "Lisinopril", "Atorvastatin"
    ]

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Common Medications")
                .font(.headline)

            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
                ForEach(commonDrugs, id: \.self) { drug in
                    Button(action: { onSelect(drug) }) {
                        Text(drug)
                            .font(.subheadline)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 12)
                            .background(Color(.secondarySystemBackground))
                            .cornerRadius(8)
                    }
                    .buttonStyle(.plain)
                }
            }
        }
    }
}
