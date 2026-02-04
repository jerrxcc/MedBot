//
//  SymptomView.swift
//  MedBotiOS
//
//  Full symptom analysis view with conversation history
//

import SwiftUI

struct SymptomView: View {
    @EnvironmentObject var settingsManager: SettingsManager
    @EnvironmentObject var historyService: HistoryService

    @State private var query = ""
    @State private var isLoading = false
    @State private var response: SymptomResponse?
    @State private var errorMessage: String?
    @State private var conversationHistory: [[String: String]] = []
    @State private var sessionId = UUID().uuidString

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 20) {
                    // Response section
                    if let response = response {
                        SymptomResponseCard(response: response)
                    }

                    // Error message
                    if let error = errorMessage {
                        ErrorCard(message: error) {
                            errorMessage = nil
                        }
                    }

                    // Conversation history
                    if !conversationHistory.isEmpty {
                        ConversationHistoryView(history: conversationHistory)
                    }

                    Spacer(minLength: 100)
                }
                .padding()
            }
            .navigationTitle("Symptom Analysis")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Clear") {
                        clearConversation()
                    }
                    .disabled(conversationHistory.isEmpty)
                }
            }
            .safeAreaInset(edge: .bottom) {
                InputBar(
                    text: $query,
                    placeholder: "Describe your symptoms...",
                    isLoading: isLoading,
                    onSubmit: analyzeSymptoms
                )
            }
        }
    }

    private func analyzeSymptoms() {
        guard !query.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }

        isLoading = true
        errorMessage = nil

        Task {
            do {
                let result = try await APIService.shared.analyzeSymptoms(
                    query: query,
                    language: settingsManager.language.rawValue,
                    history: conversationHistory.isEmpty ? nil : conversationHistory,
                    sessionId: sessionId
                )

                await MainActor.run {
                    response = result

                    // Update conversation history
                    conversationHistory.append(["role": "user", "content": query])
                    conversationHistory.append(["role": "assistant", "content": result.fullResponse])

                    // Save to history
                    historyService.addItem(
                        type: .symptoms,
                        query: query,
                        response: result.fullResponse,
                        summary: result.summary.short
                    )

                    query = ""
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

    private func clearConversation() {
        conversationHistory = []
        response = nil
        query = ""
        sessionId = UUID().uuidString
    }
}

struct SymptomResponseCard: View {
    let response: SymptomResponse

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

            // Full response
            Text(response.fullResponse)
                .font(.body)

            // Confidence and sources
            HStack {
                ConfidenceView(confidence: response.confidence, level: response.confidenceLevel)
                Spacer()
                Label("\(response.sourcesCount) sources", systemImage: "doc.text")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            // Sources expandable
            if let sources = response.sources, !sources.isEmpty {
                DisclosureGroup("View Sources") {
                    ForEach(sources, id: \.source) { source in
                        HStack {
                            Text(source.source)
                                .font(.caption)
                            Spacer()
                            if let relevance = source.relevance {
                                Text("\(Int(relevance))%")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                        }
                    }
                }
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(radius: 2)
    }
}

// MARK: - Supporting Views

struct SeverityBadge: View {
    let severity: SeverityLevel

    var color: Color {
        switch severity {
        case .low: return .green
        case .medium: return .yellow
        case .high: return .orange
        case .emergency: return .red
        }
    }

    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: "circle.fill")
                .font(.caption2)
            Text(severity.rawValue.capitalized)
                .font(.caption)
                .fontWeight(.semibold)
        }
        .foregroundColor(color)
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(color.opacity(0.2))
        .cornerRadius(8)
    }
}

struct ActionBadge: View {
    let action: ActionType

    var text: String {
        switch action {
        case .selfCare: return "Self Care"
        case .seeDoctor: return "See Doctor"
        case .emergency: return "Emergency"
        case .info: return "Info"
        }
    }

    var body: some View {
        Text(text)
            .font(.caption)
            .foregroundColor(.secondary)
    }
}

struct ConfidenceView: View {
    let confidence: Double
    let level: String

    var color: Color {
        switch level {
        case "high": return .green
        case "medium": return .yellow
        case "low": return .orange
        default: return .red
        }
    }

    var body: some View {
        HStack(spacing: 4) {
            ProgressView(value: confidence)
                .progressViewStyle(LinearProgressViewStyle(tint: color))
                .frame(width: 60)
            Text("\(Int(confidence * 100))%")
                .font(.caption)
                .foregroundColor(.secondary)
        }
    }
}

struct ConversationHistoryView: View {
    let history: [[String: String]]

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Conversation")
                .font(.headline)

            ForEach(Array(history.enumerated()), id: \.offset) { index, message in
                if let role = message["role"], let content = message["content"] {
                    HStack(alignment: .top) {
                        Image(systemName: role == "user" ? "person.circle.fill" : "cross.case.fill")
                            .foregroundColor(role == "user" ? .blue : .green)

                        Text(content)
                            .font(.subheadline)
                            .foregroundColor(role == "user" ? .primary : .secondary)
                    }
                }
            }
        }
        .padding()
        .background(Color(.secondarySystemBackground))
        .cornerRadius(12)
    }
}

struct InputBar: View {
    @Binding var text: String
    let placeholder: String
    let isLoading: Bool
    let onSubmit: () -> Void

    var body: some View {
        HStack(spacing: 12) {
            TextField(placeholder, text: $text, axis: .vertical)
                .textFieldStyle(.roundedBorder)
                .lineLimit(1...4)
                .disabled(isLoading)

            Button(action: onSubmit) {
                if isLoading {
                    ProgressView()
                        .frame(width: 44, height: 44)
                } else {
                    Image(systemName: "arrow.up.circle.fill")
                        .font(.title)
                        .foregroundColor(.blue)
                }
            }
            .disabled(text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || isLoading)
        }
        .padding()
        .background(.ultraThinMaterial)
    }
}

struct ErrorCard: View {
    let message: String
    let onDismiss: () -> Void

    var body: some View {
        HStack {
            Image(systemName: "exclamationmark.triangle.fill")
                .foregroundColor(.orange)
            Text(message)
                .font(.subheadline)
            Spacer()
            Button(action: onDismiss) {
                Image(systemName: "xmark.circle.fill")
                    .foregroundColor(.secondary)
            }
        }
        .padding()
        .background(Color.orange.opacity(0.1))
        .cornerRadius(8)
    }
}
