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
            return NSLocalizedString("severity_low", comment: "Low")
        case .medium:
            return NSLocalizedString("severity_medium", comment: "Medium")
        case .high:
            return NSLocalizedString("severity_high", comment: "High")
        case .emergency:
            return NSLocalizedString("severity_emergency", comment: "Emergency")
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
            return NSLocalizedString("action_self_care", comment: "Self Care")
        case .seeDoctor:
            return NSLocalizedString("action_see_doctor", comment: "See Doctor")
        case .emergency:
            return NSLocalizedString("action_emergency", comment: "Emergency")
        case .info:
            return NSLocalizedString("action_info", comment: "Info")
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
