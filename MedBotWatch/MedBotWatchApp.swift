//
//  MedBotWatchApp.swift
//  MedBotWatch
//
//  Apple Watch app for MedBot medical assistant
//

import SwiftUI

@main
struct MedBotWatchApp: App {
    @StateObject private var settingsManager = SettingsManager()

    var body: some Scene {
        WindowGroup {
            HomeView()
                .environmentObject(settingsManager)
        }
    }
}

/// Manages app-wide settings including language preferences
class SettingsManager: ObservableObject {
    @Published var language: AppLanguage {
        didSet {
            UserDefaults.standard.set(language.rawValue, forKey: "app_language")
        }
    }

    @Published var apiBaseURL: String {
        didSet {
            UserDefaults.standard.set(apiBaseURL, forKey: "api_base_url")
        }
    }

    init() {
        let savedLanguage = UserDefaults.standard.string(forKey: "app_language") ?? "auto"
        self.language = AppLanguage(rawValue: savedLanguage) ?? .auto
        self.apiBaseURL = UserDefaults.standard.string(forKey: "api_base_url") ?? "http://localhost:8001"
    }
}

enum AppLanguage: String, CaseIterable {
    case auto = "auto"
    case english = "en"
    case chinese = "zh"

    var displayName: String {
        switch self {
        case .auto: return "Auto"
        case .english: return "English"
        case .chinese: return "中文"
        }
    }
}
