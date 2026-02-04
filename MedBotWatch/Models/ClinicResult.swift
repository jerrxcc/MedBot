//
//  ClinicResult.swift
//  MedBotWatch
//
//  Response models for clinic search API
//

import Foundation

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
        case name
        case address
        case area
        case contact
        case distanceMeters = "distance_meters"
        case postalCode = "postal_code"
        case fromNearbyArea = "from_nearby_area"
    }

    /// Formatted distance string
    var distanceString: String? {
        guard let meters = distanceMeters else { return nil }
        if meters < 1000 {
            return "\(meters)m"
        } else {
            let km = Double(meters) / 1000.0
            return String(format: "%.1fkm", km)
        }
    }
}

struct ClinicSearchResponse: Codable {
    let success: Bool
    let summary: WatchSummary
    let results: [ClinicResult]
    let totalCount: Int
    let searchPlan: [String: AnyCodable]?
    let mapAvailable: Bool

    enum CodingKeys: String, CodingKey {
        case success
        case summary
        case results
        case totalCount = "total_count"
        case searchPlan = "search_plan"
        case mapAvailable = "map_available"
    }
}

struct ClinicSearchRequest: Codable {
    let query: String
    let postalCode: String?
    let area: String?
    let clinicName: String?
    let limit: Int?

    enum CodingKeys: String, CodingKey {
        case query
        case postalCode = "postal_code"
        case area
        case clinicName = "clinic_name"
        case limit
    }
}
