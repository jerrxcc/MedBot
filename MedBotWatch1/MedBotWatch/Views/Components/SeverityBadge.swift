//
//  SeverityBadge.swift
//  MedBotWatch
//
//  Visual badge indicating severity level
//

import SwiftUI

struct SeverityBadge: View {
    let severity: SeverityLevel

    var backgroundColor: Color {
        switch severity {
        case .low:
            return .green
        case .medium:
            return .yellow
        case .high:
            return .orange
        case .emergency:
            return .red
        }
    }

    var textColor: Color {
        switch severity {
        case .medium:
            return .black
        default:
            return .white
        }
    }

    var icon: String {
        switch severity {
        case .low:
            return "checkmark.circle"
        case .medium:
            return "exclamationmark.triangle"
        case .high:
            return "exclamationmark.triangle.fill"
        case .emergency:
            return "exclamationmark.octagon.fill"
        }
    }

    var localizedText: String {
        switch severity {
        case .low:
            return L("severity_low")
        case .medium:
            return L("severity_medium")
        case .high:
            return L("severity_high")
        case .emergency:
            return L("severity_emergency")
        }
    }

    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: icon)
                .font(.caption2)
            Text(localizedText)
                .font(.caption2)
                .fontWeight(.semibold)
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(backgroundColor)
        .foregroundColor(textColor)
        .cornerRadius(8)
    }
}

// Large badge for result views
struct LargeSeverityBadge: View {
    let severity: SeverityLevel
    let action: ActionType

    var actionText: String {
        switch action {
        case .selfCare:
            return L("action_self_care")
        case .seeDoctor:
            return L("action_see_doctor")
        case .emergency:
            return L("action_emergency")
        case .info:
            return L("action_info")
        }
    }

    var actionIcon: String {
        switch action {
        case .selfCare:
            return "house.fill"
        case .seeDoctor:
            return "stethoscope"
        case .emergency:
            return "phone.fill"
        case .info:
            return "info.circle"
        }
    }

    var body: some View {
        VStack(spacing: 8) {
            SeverityBadge(severity: severity)

            HStack(spacing: 4) {
                Image(systemName: actionIcon)
                    .font(.caption)
                Text(actionText)
                    .font(.caption)
            }
            .foregroundColor(.secondary)
        }
    }
}

// Confidence indicator
struct ConfidenceIndicator: View {
    let confidence: Double
    let level: String

    var confidenceColor: Color {
        switch level {
        case "high":
            return .green
        case "medium":
            return .yellow
        case "low":
            return .orange
        default:
            return .red
        }
    }

    var body: some View {
        HStack(spacing: 4) {
            // Confidence bar
            GeometryReader { geometry in
                ZStack(alignment: .leading) {
                    Rectangle()
                        .fill(Color.gray.opacity(0.3))

                    Rectangle()
                        .fill(confidenceColor)
                        .frame(width: geometry.size.width * CGFloat(confidence))
                }
            }
            .frame(height: 4)
            .cornerRadius(2)

            Text("\(Int(confidence * 100))%")
                .font(.caption2)
                .foregroundColor(.secondary)
        }
    }
}

#Preview {
    VStack(spacing: 20) {
        SeverityBadge(severity: .low)
        SeverityBadge(severity: .medium)
        SeverityBadge(severity: .high)
        SeverityBadge(severity: .emergency)

        LargeSeverityBadge(severity: .medium, action: .selfCare)

        ConfidenceIndicator(confidence: 0.78, level: "high")
    }
    .padding()
}
