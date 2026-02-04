//
//  MedicationResponse.swift
//  MedBotWatch
//
//  Response model for medication lookup API
//

import Foundation

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
        case success
        case summary
        case fullResponse = "full_response"
        case drugName = "drug_name"
        case confidence
        case confidenceLevel = "confidence_level"
        case sourcesCount = "sources_count"
        case warnings
    }
}

struct MedicationRequest: Codable {
    let query: String
    let language: String?
    let history: [[String: String]]?
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
        case success
        case summary
        case fullResponse = "full_response"
        case abnormalValues = "abnormal_values"
        case confidence
        case confidenceLevel = "confidence_level"
        case sourcesCount = "sources_count"
    }
}

struct RecordsRequest: Codable {
    let content: String
    let language: String?
    let recordType: String?

    enum CodingKeys: String, CodingKey {
        case content
        case language
        case recordType = "record_type"
    }
}
