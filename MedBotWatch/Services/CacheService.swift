//
//  CacheService.swift
//  MedBotWatch
//
//  Simple caching service for offline support
//

import Foundation

/// Manages local caching for offline support and performance
class CacheService: ObservableObject {
    static let shared = CacheService()

    private let userDefaults = UserDefaults.standard
    private let cacheExpirationSeconds: TimeInterval = 3600 // 1 hour

    // Cache keys
    private let lastSymptomResponseKey = "cache_last_symptom"
    private let lastDoctorResultsKey = "cache_last_doctors"
    private let lastClinicResultsKey = "cache_last_clinics"
    private let cacheTimestampSuffix = "_timestamp"

    // MARK: - Symptom Cache

    func cacheSymptomResponse(_ response: SymptomResponse, forQuery query: String) {
        let cacheData = CachedResponse(query: query, response: response, timestamp: Date())
        if let encoded = try? JSONEncoder().encode(cacheData) {
            userDefaults.set(encoded, forKey: lastSymptomResponseKey)
        }
    }

    func getCachedSymptomResponse(forQuery query: String) -> SymptomResponse? {
        guard let data = userDefaults.data(forKey: lastSymptomResponseKey),
              let cached = try? JSONDecoder().decode(CachedResponse<SymptomResponse>.self, from: data) else {
            return nil
        }

        // Check if expired
        if Date().timeIntervalSince(cached.timestamp) > cacheExpirationSeconds {
            return nil
        }

        // Check if query matches (simple contains check for follow-up queries)
        let queryWords = Set(query.lowercased().split(separator: " ").map(String.init))
        let cachedWords = Set(cached.query.lowercased().split(separator: " ").map(String.init))
        let overlap = queryWords.intersection(cachedWords)

        if overlap.count >= min(2, queryWords.count) {
            return cached.response
        }

        return nil
    }

    // MARK: - Doctor Cache

    func cacheDoctorResults(_ results: [DoctorResult]) {
        if let encoded = try? JSONEncoder().encode(results) {
            userDefaults.set(encoded, forKey: lastDoctorResultsKey)
            userDefaults.set(Date().timeIntervalSince1970, forKey: lastDoctorResultsKey + cacheTimestampSuffix)
        }
    }

    func getCachedDoctorResults() -> [DoctorResult]? {
        let timestamp = userDefaults.double(forKey: lastDoctorResultsKey + cacheTimestampSuffix)
        if Date().timeIntervalSince1970 - timestamp > cacheExpirationSeconds {
            return nil
        }

        guard let data = userDefaults.data(forKey: lastDoctorResultsKey),
              let results = try? JSONDecoder().decode([DoctorResult].self, from: data) else {
            return nil
        }

        return results
    }

    // MARK: - Clinic Cache

    func cacheClinicResults(_ results: [ClinicResult]) {
        if let encoded = try? JSONEncoder().encode(results) {
            userDefaults.set(encoded, forKey: lastClinicResultsKey)
            userDefaults.set(Date().timeIntervalSince1970, forKey: lastClinicResultsKey + cacheTimestampSuffix)
        }
    }

    func getCachedClinicResults() -> [ClinicResult]? {
        let timestamp = userDefaults.double(forKey: lastClinicResultsKey + cacheTimestampSuffix)
        if Date().timeIntervalSince1970 - timestamp > cacheExpirationSeconds {
            return nil
        }

        guard let data = userDefaults.data(forKey: lastClinicResultsKey),
              let results = try? JSONDecoder().decode([ClinicResult].self, from: data) else {
            return nil
        }

        return results
    }

    // MARK: - Clear Cache

    func clearAllCache() {
        userDefaults.removeObject(forKey: lastSymptomResponseKey)
        userDefaults.removeObject(forKey: lastDoctorResultsKey)
        userDefaults.removeObject(forKey: lastDoctorResultsKey + cacheTimestampSuffix)
        userDefaults.removeObject(forKey: lastClinicResultsKey)
        userDefaults.removeObject(forKey: lastClinicResultsKey + cacheTimestampSuffix)
    }
}

// MARK: - Helper Types

struct CachedResponse<T: Codable>: Codable {
    let query: String
    let response: T
    let timestamp: Date
}
