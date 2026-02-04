//
//  MedicationViewModel.swift
//  MedBotWatch
//
//  ViewModel for medication lookup feature
//

import Foundation
import SwiftUI

@MainActor
class MedicationViewModel: ObservableObject {
    @Published var query: String = ""
    @Published var response: MedicationResponse?
    @Published var isLoading = false
    @Published var errorMessage: String?

    private let apiService = APIService.shared
    private let cacheService = CacheService.shared

    var hasResponse: Bool {
        response != nil
    }

    var hasWarnings: Bool {
        guard let warnings = response?.warnings else { return false }
        return !warnings.isEmpty
    }

    func lookupMedication(language: String = "auto") async {
        guard !query.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            return
        }

        isLoading = true
        errorMessage = nil

        // Check cache first
        if let cached = cacheService.getCachedMedicationResponse(forQuery: query) {
            response = cached
            isLoading = false
            return
        }

        do {
            let result = try await apiService.lookupMedication(
                query: query,
                language: language
            )

            response = result

            // Cache the response
            cacheService.cacheMedicationResponse(result, forQuery: query)

        } catch {
            errorMessage = error.localizedDescription
        }

        isLoading = false
    }

    func clear() {
        response = nil
        query = ""
        errorMessage = nil
    }
}

@MainActor
class RecordsViewModel: ObservableObject {
    @Published var content: String = ""
    @Published var recordType: String = "general"
    @Published var response: RecordsResponse?
    @Published var isLoading = false
    @Published var errorMessage: String?

    private let apiService = APIService.shared

    var hasResponse: Bool {
        response != nil
    }

    var hasAbnormalValues: Bool {
        guard let values = response?.abnormalValues else { return false }
        return !values.isEmpty
    }

    func analyzeRecords(language: String = "auto") async {
        guard !content.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            return
        }

        isLoading = true
        errorMessage = nil

        do {
            let result = try await apiService.analyzeRecords(
                content: content,
                language: language,
                recordType: recordType
            )

            response = result

        } catch {
            errorMessage = error.localizedDescription
        }

        isLoading = false
    }

    func clear() {
        response = nil
        content = ""
        errorMessage = nil
    }
}
