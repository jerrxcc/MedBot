//
//  MedBotiOSApp.swift
//  MedBotiOS
//
//  iOS Companion app for MedBot medical assistant
//  Syncs with Apple Watch and provides full feature access
//

import SwiftUI

@main
struct MedBotiOSApp: App {
    @StateObject private var settingsManager = SettingsManager()
    @StateObject private var syncService = WatchSyncService.shared
    @StateObject private var historyService = HistoryService.shared

    var body: some Scene {
        WindowGroup {
            MainTabView()
                .environmentObject(settingsManager)
                .environmentObject(syncService)
                .environmentObject(historyService)
        }
    }
}

/// Manages app-wide settings including language preferences
class SettingsManager: ObservableObject {
    @Published var language: AppLanguage {
        didSet {
            UserDefaults.standard.set(language.rawValue, forKey: "app_language")
            WatchSyncService.shared.sendSettings(["language": language.rawValue])
        }
    }

    @Published var apiBaseURL: String {
        didSet {
            UserDefaults.standard.set(apiBaseURL, forKey: "api_base_url")
            APIService.shared.updateBaseURL(apiBaseURL)
            WatchSyncService.shared.sendSettings(["api_url": apiBaseURL])
        }
    }

    @Published var saveHistory: Bool {
        didSet {
            UserDefaults.standard.set(saveHistory, forKey: "save_history")
        }
    }

    init() {
        let savedLanguage = UserDefaults.standard.string(forKey: "app_language") ?? "auto"
        self.language = AppLanguage(rawValue: savedLanguage) ?? .auto
        self.apiBaseURL = UserDefaults.standard.string(forKey: "api_base_url") ?? "http://localhost:8001"
        self.saveHistory = UserDefaults.standard.bool(forKey: "save_history")

        // Initialize API service
        APIService.shared.updateBaseURL(apiBaseURL)
    }
}

enum AppLanguage: String, CaseIterable {
    case auto = "auto"
    case english = "en"
    case chinese = "zh"

    var displayName: String {
        switch self {
        case .auto: return "Auto Detect"
        case .english: return "English"
        case .chinese: return "中文 (Chinese)"
        }
    }
}
