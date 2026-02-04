//
//  SymptomViewModel.swift
//  MedBotWatch
//
//  ViewModel for symptom analysis feature
//

import Foundation
import SwiftUI

@MainActor
class SymptomViewModel: ObservableObject {
    @Published var query: String = ""
    @Published var response: SymptomResponse?
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var conversationHistory: [[String: String]] = []

    private let apiService = APIService.shared
    private let cacheService = CacheService.shared

    var hasResponse: Bool {
        response != nil
    }

    func analyzeSymptoms(language: String = "auto") async {
        guard !query.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            return
        }

        isLoading = true
        errorMessage = nil

        // Check cache first
        if let cached = cacheService.getCachedSymptomResponse(forQuery: query) {
            response = cached
            isLoading = false
            return
        }

        do {
            let result = try await apiService.analyzeSymptoms(
                query: query,
                language: language,
                history: conversationHistory.isEmpty ? nil : conversationHistory
            )

            response = result

            // Update conversation history
            conversationHistory.append(["role": "user", "content": query])
            conversationHistory.append(["role": "assistant", "content": result.fullResponse])

            // Keep only last 10 turns
            if conversationHistory.count > 20 {
                conversationHistory = Array(conversationHistory.suffix(20))
            }

            // Cache the response
            cacheService.cacheSymptomResponse(result, forQuery: query)

        } catch {
            errorMessage = error.localizedDescription
        }

        isLoading = false
    }

    func clearConversation() {
        conversationHistory = []
        response = nil
        query = ""
        errorMessage = nil
    }
}
