//
//  SymptomResponse.swift
//  MedBotWatch
//
//  Response model for symptom analysis API
//

import Foundation

struct WatchSummary: Codable {
    let short: String
    let severity: SeverityLevel
    let action: ActionType
}

enum SeverityLevel: String, Codable {
    case low
    case medium
    case high
    case emergency

    var color: String {
        switch self {
        case .low: return "green"
        case .medium: return "yellow"
        case .high: return "orange"
        case .emergency: return "red"
        }
    }

    var emoji: String {
        switch self {
        case .low: return "✓"
        case .medium: return "⚠"
        case .high: return "⚠"
        case .emergency: return "🚨"
        }
    }
}

enum ActionType: String, Codable {
    case selfCare = "self_care"
    case seeDoctor = "see_doctor"
    case emergency
    case info

    var localizedKey: String {
        switch self {
        case .selfCare: return "action_self_care"
        case .seeDoctor: return "action_see_doctor"
        case .emergency: return "action_emergency"
        case .info: return "action_info"
        }
    }
}

struct SymptomResponse: Codable {
    let success: Bool
    let summary: WatchSummary
    let fullResponse: String
    let confidence: Double
    let confidenceLevel: String
    let sourcesCount: Int
    let languageDetected: String?

    enum CodingKeys: String, CodingKey {
        case success
        case summary
        case fullResponse = "full_response"
        case confidence
        case confidenceLevel = "confidence_level"
        case sourcesCount = "sources_count"
        case languageDetected = "language_detected"
    }
}

struct SymptomRequest: Codable {
    let query: String
    let language: String?
    let history: [[String: String]]?
    let sessionId: String?

    enum CodingKeys: String, CodingKey {
        case query
        case language
        case history
        case sessionId = "session_id"
    }
}
