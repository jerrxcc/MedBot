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
                .environment(\.locale, settingsManager.locale)
                .id(settingsManager.language)
        }
    }
}

/// Manages app-wide settings including language preferences
class SettingsManager: ObservableObject {
    /// Resolved locale for SwiftUI .environment(\.locale)
    var locale: Locale {
        switch language {
        case .auto: return Locale.current
        case .english: return Locale(identifier: "en")
        case .chinese: return Locale(identifier: "zh-Hans")
        }
    }

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

    @Published var minimaxAPIKey: String {
        didSet {
            UserDefaults.standard.set(minimaxAPIKey, forKey: "minimax_api_key")
        }
    }

    @Published var minimaxGroupId: String {
        didSet {
            UserDefaults.standard.set(minimaxGroupId, forKey: "minimax_group_id")
        }
    }

    init() {
        let savedLanguage = UserDefaults.standard.string(forKey: "app_language") ?? "auto"
        self.language = AppLanguage(rawValue: savedLanguage) ?? .auto
        self.apiBaseURL = UserDefaults.standard.string(forKey: "api_base_url") ?? "http://localhost:8001"
        self.minimaxAPIKey = UserDefaults.standard.string(forKey: "minimax_api_key") ?? "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJHcm91cE5hbWUiOiJNYXggWHUiLCJVc2VyTmFtZSI6Ik1heCBYdSIsIkFjY291bnQiOiIiLCJTdWJqZWN0SUQiOiIxODg4OTUwMTczNzIwMTI1NjEyIiwiUGhvbmUiOiIiLCJHcm91cElEIjoiMTg4ODk1MDE3MzcxNTkzMTMwOCIsIlBhZ2VOYW1lIjoiIiwiTWFpbCI6ImRlZXB0aG91Z2h0QGdtYWlsLmNvbSIsIkNyZWF0ZVRpbWUiOiIyMDI1LTEyLTE2IDE2OjU0OjM0IiwiVG9rZW5UeXBlIjoxLCJpc3MiOiJtaW5pbWF4In0.SaE5FN1SF3mwkwYbuXVj5_3pZ86xWvdR3Trc0VOyg8RmGLOxzEXjuPQvQYBQCMDtCDkRPitBXgABeAnCn3zqYV8WDVmapx5DV08x6mJHme_za2TFlCzlSLq7ZhqfLJ36Ce-_lrB_eC49wDEJuFvHTcTz3vIwgcsKjtnVG87nPPS6xCTA3TLsB1WKe7_URc6kSTQvOU9TfwuJKh_uBXpjk3Co0eT8cq4_2HT0BWoIhZRTfnMjxd1-77Rnvw7BfDnUkzr_AXAawnAX9gupZ67V2z8xQeuPxfmf5L2ZgBY-AWcF-9ugtwMljz4SE1rSGzkoS4Sm9TuLRyYxUyb2cu_bwQ"
        self.minimaxGroupId = UserDefaults.standard.string(forKey: "minimax_group_id") ?? "1888950173715931308"

        // Persist defaults to UserDefaults so TTSService can read them directly
        UserDefaults.standard.set(self.minimaxAPIKey, forKey: "minimax_api_key")
        UserDefaults.standard.set(self.minimaxGroupId, forKey: "minimax_group_id")
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
