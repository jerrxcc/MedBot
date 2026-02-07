//
//  HomeView.swift
//  MedBotWatch
//
//  Main menu with access to 3 features + settings
//

import SwiftUI

struct HomeView: View {
    @EnvironmentObject var settingsManager: SettingsManager

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 12) {
                    // App Header
                    HStack {
                        Image(systemName: "cross.case.fill")
                            .foregroundColor(.pink)
                        Text("MedBot")
                            .font(.headline)
                    }
                    .padding(.bottom, 4)

                    // Feature Grid (2x2)
                    LazyVGrid(columns: [
                        GridItem(.flexible()),
                        GridItem(.flexible())
                    ], spacing: 10) {
                        FeatureButton(
                            destination: SymptomInputView(),
                            icon: "cross.case.fill",
                            titleKey: "feature_symptoms",
                            color: .pink
                        )

                        FeatureButton(
                            destination: DoctorSearchView(),
                            icon: "person.crop.circle.fill",
                            titleKey: "feature_doctors",
                            color: .yellow
                        )

                        FeatureButton(
                            destination: ClinicSearchView(),
                            icon: "building.2.crop.circle.fill",
                            titleKey: "feature_clinics",
                            color: .green
                        )

                        FeatureButton(
                            destination: SettingsView(),
                            icon: "gear",
                            titleKey: "feature_settings",
                            color: .gray
                        )
                    }
                }
                .padding()
            }
        }
    }
}

struct FeatureButton<Destination: View>: View {
    let destination: Destination
    let icon: String
    let titleKey: String
    let color: Color

    var body: some View {
        NavigationLink(destination: destination) {
            VStack(spacing: 6) {
                Image(systemName: icon)
                    .font(.title2)
                    .foregroundColor(color)

                Text(LocalizedStringKey(titleKey))
                    .font(.caption2)
                    .foregroundColor(.primary)
                    .lineLimit(1)
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 12)
            .background(color.opacity(0.15))
            .cornerRadius(12)
        }
        .buttonStyle(PlainButtonStyle())
    }
}

struct SettingsView: View {
    @EnvironmentObject var settingsManager: SettingsManager
    @State private var showingAPISettings = false
    @State private var showingTTSSettings = false

    var body: some View {
        List {
            // Language setting
            Section {
                Picker(selection: $settingsManager.language) {
                    ForEach(AppLanguage.allCases, id: \.self) { lang in
                        Text(lang.displayName).tag(lang)
                    }
                } label: {
                    Label {
                        Text(LocalizedStringKey("settings_language"))
                    } icon: {
                        Image(systemName: "globe")
                    }
                }
            }

            // API Settings
            Section {
                Button(action: { showingAPISettings = true }) {
                    Label {
                        Text(LocalizedStringKey("settings_api"))
                    } icon: {
                        Image(systemName: "network")
                    }
                }
            }

            // TTS Settings
            Section {
                Button(action: { showingTTSSettings = true }) {
                    Label {
                        Text(LocalizedStringKey("settings_tts"))
                    } icon: {
                        Image(systemName: "speaker.wave.2")
                    }
                }
            }

            // About
            Section {
                HStack {
                    Text(LocalizedStringKey("settings_version"))
                    Spacer()
                    Text("1.0.0")
                        .foregroundColor(.secondary)
                }
            }
        }
        .localizedNavTitle("feature_settings")
        .sheet(isPresented: $showingAPISettings) {
            APISettingsView()
        }
        .sheet(isPresented: $showingTTSSettings) {
            TTSSettingsView()
        }
    }
}

struct APISettingsView: View {
    @EnvironmentObject var settingsManager: SettingsManager
    @State private var apiURL: String = ""
    @State private var isHealthy = false
    @State private var isChecking = false
    @Environment(\.dismiss) var dismiss

    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                Text(LocalizedStringKey("settings_api_url"))
                    .font(.caption)

                TextField("http://localhost:8001", text: $apiURL)
                    .textFieldStyle(.plain)
                    .font(.caption2)

                Button(action: checkHealth) {
                    if isChecking {
                        ProgressView()
                    } else {
                        Text(LocalizedStringKey("button_test"))
                    }
                }

                if isHealthy {
                    Label {
                        Text(LocalizedStringKey("status_connected"))
                    } icon: {
                        Image(systemName: "checkmark.circle.fill")
                            .foregroundColor(.green)
                    }
                    .font(.caption)
                }

                Button(action: save) {
                    Text(LocalizedStringKey("button_save"))
                }
                .buttonStyle(.borderedProminent)
            }
            .padding()
        }
        .onAppear {
            apiURL = settingsManager.apiBaseURL
        }
    }

    func checkHealth() {
        isChecking = true
        APIService.shared.updateBaseURL(apiURL)

        Task {
            isHealthy = try await APIService.shared.healthCheck()
            isChecking = false
        }
    }

    func save() {
        settingsManager.apiBaseURL = apiURL
        APIService.shared.updateBaseURL(apiURL)
        dismiss()
    }
}

struct TTSSettingsView: View {
    @EnvironmentObject var settingsManager: SettingsManager
    @State private var apiKey: String = ""
    @State private var groupId: String = ""
    @Environment(\.dismiss) var dismiss

    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                Text(LocalizedStringKey("settings_tts"))
                    .font(.caption)
                    .fontWeight(.medium)

                VStack(alignment: .leading, spacing: 4) {
                    Text(LocalizedStringKey("settings_tts_key"))
                        .font(.caption2)
                        .foregroundColor(.secondary)
                    SecureField("API Key", text: $apiKey)
                        .textFieldStyle(.plain)
                        .font(.caption2)
                }

                VStack(alignment: .leading, spacing: 4) {
                    Text(LocalizedStringKey("settings_tts_group"))
                        .font(.caption2)
                        .foregroundColor(.secondary)
                    TextField("Group ID", text: $groupId)
                        .textFieldStyle(.plain)
                        .font(.caption2)
                }

                Button(action: save) {
                    Text(LocalizedStringKey("button_save"))
                }
                .buttonStyle(.borderedProminent)
            }
            .padding()
        }
        .onAppear {
            apiKey = settingsManager.minimaxAPIKey
            groupId = settingsManager.minimaxGroupId
        }
    }

    func save() {
        settingsManager.minimaxAPIKey = apiKey
        settingsManager.minimaxGroupId = groupId
        dismiss()
    }
}

#Preview {
    HomeView()
        .environmentObject(SettingsManager())
}
