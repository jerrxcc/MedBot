//
//  SymptomResultView.swift
//  MedBotWatch
//
//  Display symptom analysis results
//

import SwiftUI

struct SymptomResultView: View {
    let response: SymptomResponse

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
                Text(response.summary.short)
                    .font(.caption)
                    .fontWeight(.medium)
                    .multilineTextAlignment(.center)

                // Confidence indicator
                ConfidenceIndicator(
                    confidence: response.confidence,
                    level: response.confidenceLevel
                )
                .padding(.horizontal)

                Divider()

                // Full response preview
                Text(response.fullResponse)
                    .font(.caption2)
                    .foregroundColor(.secondary)
                    .lineLimit(10)
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
