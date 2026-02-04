//
//  ClinicSearchViewModel.swift
//  MedBotWatch
//
//  ViewModel for clinic search feature
//

import Foundation
import SwiftUI

@MainActor
class ClinicSearchViewModel: ObservableObject {
    @Published var query: String = ""
    @Published var postalCode: String = ""
    @Published var area: String = ""
    @Published var results: [ClinicResult] = []
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var totalCount: Int = 0

    private let apiService = APIService.shared
    private let cacheService = CacheService.shared

    var hasResults: Bool {
        !results.isEmpty
    }

    // Singapore areas for quick selection
    let singaporeAreas = [
        "Ang Mo Kio",
        "Bedok",
        "Bishan",
        "Bukit Batok",
        "Bukit Merah",
        "Clementi",
        "Geylang",
        "Hougang",
        "Jurong East",
        "Jurong West",
        "Kallang",
        "Marine Parade",
        "Pasir Ris",
        "Punggol",
        "Queenstown",
        "Sembawang",
        "Sengkang",
        "Serangoon",
        "Tampines",
        "Toa Payoh",
        "Woodlands",
        "Yishun"
    ]

    func searchClinics() async {
        // Build query if empty but filters provided
        var searchQuery = query
        if searchQuery.isEmpty {
            if !postalCode.isEmpty {
                searchQuery = "Clinics near postal code \(postalCode)"
            } else if !area.isEmpty {
                searchQuery = "Clinics in \(area)"
            } else {
                return // Nothing to search
            }
        }

        isLoading = true
        errorMessage = nil

        do {
            let response = try await apiService.searchClinics(
                query: searchQuery,
                postalCode: postalCode.isEmpty ? nil : postalCode,
                area: area.isEmpty ? nil : area,
                clinicName: nil,
                limit: 5
            )

            results = response.results
            totalCount = response.totalCount

            // Cache results
            cacheService.cacheClinicResults(results)

        } catch {
            errorMessage = error.localizedDescription

            // Try to use cached results
            if let cached = cacheService.getCachedClinicResults() {
                results = cached
                errorMessage = nil
            }
        }

        isLoading = false
    }

    func clear() {
        results = []
        query = ""
        postalCode = ""
        area = ""
        errorMessage = nil
        totalCount = 0
    }
}
