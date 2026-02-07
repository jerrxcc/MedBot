//
//  DoctorSearchViewModel.swift
//  MedBotWatch
//
//  ViewModel for doctor search feature
//

import Foundation
import SwiftUI

@MainActor
class DoctorSearchViewModel: ObservableObject {
    @Published var query: String = ""
    @Published var specialty: String = ""
    @Published var language: String = ""
    @Published var results: [DoctorResult] = []
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var totalCount: Int = 0

    private let apiService = APIService.shared
    private let cacheService = CacheService.shared

    var hasResults: Bool {
        !results.isEmpty
    }

    // Common specialties for quick selection
    let commonSpecialties = [
        "Cardiology",
        "Dermatology",
        "ENT",
        "Gastroenterology",
        "General Practice",
        "Neurology",
        "Oncology",
        "Orthopedics",
        "Pediatrics",
        "Psychiatry"
    ]

    // Common languages
    let commonLanguages = [
        "English",
        "Mandarin",
        "Malay",
        "Tamil",
        "Cantonese",
        "Hokkien"
    ]

    func searchDoctors() async {
        guard !query.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            return
        }

        isLoading = true
        errorMessage = nil

        do {
            let response = try await apiService.searchDoctors(
                query: query,
                specialty: specialty.isEmpty ? nil : specialty,
                language: language.isEmpty ? nil : language,
                name: nil,
                limit: 5
            )

            results = response.results
            totalCount = response.totalCount

            // Cache results
            cacheService.cacheDoctorResults(results)

        } catch {
            errorMessage = error.localizedDescription

            // Try to use cached results
            if let cached = cacheService.getCachedDoctorResults() {
                results = cached
                errorMessage = nil
            }
        }

        isLoading = false
    }

    func clear() {
        results = []
        query = ""
        specialty = ""
        language = ""
        errorMessage = nil
        totalCount = 0
    }
}
