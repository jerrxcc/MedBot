//
//  SharedModels.swift
//  MedBotiOS
//
//  Shared data models (same as Watch app)
//

import Foundation

// MARK: - Common Types

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
}

enum ActionType: String, Codable {
    case selfCare = "self_care"
    case seeDoctor = "see_doctor"
    case emergency
    case info
}

// MARK: - Symptom Models

struct SymptomRequest: Codable {
    let query: String
    let language: String?
    let history: [[String: String]]?
    let sessionId: String?

    enum CodingKeys: String, CodingKey {
        case query, language, history
        case sessionId = "session_id"
    }
}

struct SymptomResponse: Codable {
    let success: Bool
    let summary: WatchSummary
    let fullResponse: String
    let confidence: Double
    let confidenceLevel: String
    let sourcesCount: Int
    let sources: [SourceInfo]?
    let languageDetected: String?

    enum CodingKeys: String, CodingKey {
        case success, summary, confidence, sources
        case fullResponse = "full_response"
        case confidenceLevel = "confidence_level"
        case sourcesCount = "sources_count"
        case languageDetected = "language_detected"
    }
}

struct SourceInfo: Codable {
    let source: String
    let category: String?
    let relevance: Double?
}

// MARK: - Medication Models

struct MedicationRequest: Codable {
    let query: String
    let language: String?
    let history: [[String: String]]?
}

struct MedicationResponse: Codable {
    let success: Bool
    let summary: WatchSummary
    let fullResponse: String
    let drugName: String?
    let confidence: Double
    let confidenceLevel: String
    let sourcesCount: Int
    let warnings: [String]?

    enum CodingKeys: String, CodingKey {
        case success, summary, confidence, warnings
        case fullResponse = "full_response"
        case drugName = "drug_name"
        case confidenceLevel = "confidence_level"
        case sourcesCount = "sources_count"
    }
}

// MARK: - Records Models

struct RecordsRequest: Codable {
    let content: String
    let language: String?
    let recordType: String?

    enum CodingKeys: String, CodingKey {
        case content, language
        case recordType = "record_type"
    }
}

struct RecordsResponse: Codable {
    let success: Bool
    let summary: WatchSummary
    let fullResponse: String
    let abnormalValues: [String]?
    let confidence: Double
    let confidenceLevel: String
    let sourcesCount: Int

    enum CodingKeys: String, CodingKey {
        case success, summary, confidence
        case fullResponse = "full_response"
        case abnormalValues = "abnormal_values"
        case confidenceLevel = "confidence_level"
        case sourcesCount = "sources_count"
    }
}

// MARK: - Doctor Models

struct DoctorSearchRequest: Codable {
    let query: String
    let specialty: String?
    let language: String?
    let name: String?
    let limit: Int?
}

struct DoctorSearchResponse: Codable {
    let success: Bool
    let summary: WatchSummary
    let results: [DoctorResult]
    let totalCount: Int

    enum CodingKeys: String, CodingKey {
        case success, summary, results
        case totalCount = "total_count"
    }
}

struct DoctorResult: Codable, Identifiable {
    var id: String { name }

    let name: String
    let specialty: String
    let languages: [String]
    let designation: String?
    let clinicName: String?
    let contact: String?
    let matchScore: Double?

    enum CodingKeys: String, CodingKey {
        case name, specialty, languages, designation, contact
        case clinicName = "clinic_name"
        case matchScore = "match_score"
    }
}

// MARK: - Clinic Models

struct ClinicSearchRequest: Codable {
    let query: String
    let postalCode: String?
    let area: String?
    let clinicName: String?
    let limit: Int?

    enum CodingKeys: String, CodingKey {
        case query, area, limit
        case postalCode = "postal_code"
        case clinicName = "clinic_name"
    }
}

struct ClinicSearchResponse: Codable {
    let success: Bool
    let summary: WatchSummary
    let results: [ClinicResult]
    let totalCount: Int
    let mapAvailable: Bool

    enum CodingKeys: String, CodingKey {
        case success, summary, results
        case totalCount = "total_count"
        case mapAvailable = "map_available"
    }
}

struct ClinicResult: Codable, Identifiable {
    var id: String { name + address }

    let name: String
    let address: String
    let area: String
    let contact: String?
    let distanceMeters: Int?
    let postalCode: String?
    let fromNearbyArea: String?

    enum CodingKeys: String, CodingKey {
        case name, address, area, contact
        case distanceMeters = "distance_meters"
        case postalCode = "postal_code"
        case fromNearbyArea = "from_nearby_area"
    }

    var distanceString: String? {
        guard let meters = distanceMeters else { return nil }
        if meters < 1000 {
            return "\(meters)m"
        } else {
            return String(format: "%.1f km", Double(meters) / 1000.0)
        }
    }
}
