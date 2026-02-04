//
//  HistoryService.swift
//  MedBotiOS
//
//  Manages conversation history persistence
//

import Foundation
import SwiftUI

enum HistoryType: String, Codable, CaseIterable {
    case symptoms = "symptoms"
    case medication = "medication"
    case records = "records"
    case doctors = "doctors"
    case clinics = "clinics"

    var icon: String {
        switch self {
        case .symptoms: return "stethoscope"
        case .medication: return "pill.fill"
        case .records: return "doc.text.fill"
        case .doctors: return "person.crop.circle"
        case .clinics: return "building.2.fill"
        }
    }

    var color: Color {
        switch self {
        case .symptoms: return .blue
        case .medication: return .green
        case .records: return .purple
        case .doctors: return .orange
        case .clinics: return .red
        }
    }
}

struct HistoryItem: Identifiable, Codable {
    let id: UUID
    let type: HistoryType
    let query: String
    let response: String
    let summary: String
    let timestamp: Date

    init(type: HistoryType, query: String, response: String, summary: String) {
        self.id = UUID()
        self.type = type
        self.query = query
        self.response = response
        self.summary = summary
        self.timestamp = Date()
    }
}

class HistoryService: ObservableObject {
    static let shared = HistoryService()

    @Published var items: [HistoryItem] = []

    private let storageKey = "medbot_history"
    private let maxItems = 100

    init() {
        loadHistory()
    }

    // MARK: - CRUD Operations

    func addItem(type: HistoryType, query: String, response: String, summary: String) {
        let item = HistoryItem(type: type, query: query, response: response, summary: summary)

        DispatchQueue.main.async {
            self.items.insert(item, at: 0)

            // Limit history size
            if self.items.count > self.maxItems {
                self.items = Array(self.items.prefix(self.maxItems))
            }

            self.saveHistory()

            // Sync with Watch
            WatchSyncService.shared.syncHistory(self.items)
        }
    }

    func deleteItem(_ item: HistoryItem) {
        items.removeAll { $0.id == item.id }
        saveHistory()
    }

    func deleteItems(at offsets: IndexSet) {
        items.remove(atOffsets: offsets)
        saveHistory()
    }

    func clearHistory() {
        items.removeAll()
        saveHistory()
    }

    func search(_ query: String) -> [HistoryItem] {
        let lowercased = query.lowercased()
        return items.filter {
            $0.query.lowercased().contains(lowercased) ||
            $0.response.lowercased().contains(lowercased) ||
            $0.summary.lowercased().contains(lowercased)
        }
    }

    func filter(by type: HistoryType) -> [HistoryItem] {
        items.filter { $0.type == type }
    }

    // MARK: - Persistence

    private func loadHistory() {
        guard let data = UserDefaults.standard.data(forKey: storageKey) else { return }

        do {
            items = try JSONDecoder().decode([HistoryItem].self, from: data)
        } catch {
            print("Failed to load history: \(error)")
        }
    }

    private func saveHistory() {
        do {
            let data = try JSONEncoder().encode(items)
            UserDefaults.standard.set(data, forKey: storageKey)
        } catch {
            print("Failed to save history: \(error)")
        }
    }

    // MARK: - Export

    func exportToJSON() -> Data? {
        try? JSONEncoder().encode(items)
    }
}
