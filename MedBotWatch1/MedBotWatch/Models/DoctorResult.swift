//
//  DoctorResult.swift
//  MedBotWatch
//
//  Response models for doctor search API
//

import Foundation

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
        case name
        case specialty
        case languages
        case designation
        case clinicName = "clinic_name"
        case contact
        case matchScore = "match_score"
    }
}

struct DoctorSearchResponse: Codable {
    let success: Bool
    let summary: WatchSummary
    let results: [DoctorResult]
    let totalCount: Int
    let searchPlan: [String: AnyCodable]?

    enum CodingKeys: String, CodingKey {
        case success
        case summary
        case results
        case totalCount = "total_count"
        case searchPlan = "search_plan"
    }
}

struct DoctorSearchRequest: Codable {
    let query: String
    let specialty: String?
    let language: String?
    let name: String?
    let limit: Int?
}

// Helper for dynamic JSON values
struct AnyCodable: Codable {
    let value: Any

    init(_ value: Any) {
        self.value = value
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()

        if let string = try? container.decode(String.self) {
            value = string
        } else if let int = try? container.decode(Int.self) {
            value = int
        } else if let double = try? container.decode(Double.self) {
            value = double
        } else if let bool = try? container.decode(Bool.self) {
            value = bool
        } else if let array = try? container.decode([AnyCodable].self) {
            value = array.map { $0.value }
        } else if let dictionary = try? container.decode([String: AnyCodable].self) {
            value = dictionary.mapValues { $0.value }
        } else {
            value = NSNull()
        }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()

        switch value {
        case let string as String:
            try container.encode(string)
        case let int as Int:
            try container.encode(int)
        case let double as Double:
            try container.encode(double)
        case let bool as Bool:
            try container.encode(bool)
        default:
            try container.encodeNil()
        }
    }
}
