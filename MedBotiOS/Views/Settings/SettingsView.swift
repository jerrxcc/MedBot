//
//  SettingsView.swift
//  MedBotiOS
//
//  App settings including language, API configuration, and Watch sync
//

import SwiftUI

struct SettingsView: View {
    @EnvironmentObject var settingsManager: SettingsManager
    @EnvironmentObject var syncService: WatchSyncService
    @EnvironmentObject var historyService: HistoryService

    var body: some View {
        NavigationStack {
            List {
                // Language Section
                Section("Language") {
                    Picker("App Language", selection: $settingsManager.language) {
                        ForEach(AppLanguage.allCases, id: \.self) { lang in
                            Text(lang.displayName).tag(lang)
                        }
                    }
                }

                // API Section
                Section("Server") {
                    NavigationLink(destination: APISettingsView()) {
                        HStack {
                            Label("API Configuration", systemImage: "network")
                            Spacer()
                            Text(URL(string: settingsManager.apiBaseURL)?.host ?? "localhost")
                                .foregroundColor(.secondary)
                                .lineLimit(1)
                        }
                    }
                }

                // Watch Section
                Section("Apple Watch") {
                    HStack {
                        Label("Watch Paired", systemImage: "applewatch")
                        Spacer()
                        Image(systemName: syncService.isWatchPaired ? "checkmark.circle.fill" : "xmark.circle")
                            .foregroundColor(syncService.isWatchPaired ? .green : .red)
                    }

                    HStack {
                        Label("Watch Reachable", systemImage: "antenna.radiowaves.left.and.right")
                        Spacer()
                        Image(systemName: syncService.isWatchReachable ? "checkmark.circle.fill" : "xmark.circle")
                            .foregroundColor(syncService.isWatchReachable ? .green : .secondary)
                    }

                    if let lastSync = syncService.lastSyncDate {
                        HStack {
                            Label("Last Synced", systemImage: "arrow.triangle.2.circlepath")
                            Spacer()
                            Text(lastSync, style: .relative)
                                .foregroundColor(.secondary)
                        }
                    }

                    Button(action: {
                        syncService.syncHistory(historyService.items)
                    }) {
                        Label("Sync Now", systemImage: "arrow.clockwise")
                    }
                    .disabled(!syncService.isWatchReachable)
                }

                // History Section
                Section("History") {
                    Toggle("Save History", isOn: $settingsManager.saveHistory)

                    NavigationLink(destination: HistoryListView()) {
                        HStack {
                            Label("View History", systemImage: "clock")
                            Spacer()
                            Text("\(historyService.items.count) items")
                                .foregroundColor(.secondary)
                        }
                    }

                    Button(role: .destructive, action: {
                        historyService.clearHistory()
                    }) {
                        Label("Clear History", systemImage: "trash")
                    }
                    .disabled(historyService.items.isEmpty)
                }

                // About Section
                Section("About") {
                    HStack {
                        Label("Version", systemImage: "info.circle")
                        Spacer()
                        Text("1.0.0")
                            .foregroundColor(.secondary)
                    }

                    Link(destination: URL(string: "https://github.com/anthropics/claude-code")!) {
                        Label("Help & Feedback", systemImage: "questionmark.circle")
                    }
                }
            }
            .navigationTitle("Settings")
        }
    }
}

struct APISettingsView: View {
    @EnvironmentObject var settingsManager: SettingsManager

    @State private var apiURL: String = ""
    @State private var isChecking = false
    @State private var healthStatus: HealthResponse?
    @State private var errorMessage: String?

    var body: some View {
        List {
            Section {
                TextField("Server URL", text: $apiURL)
                    .textContentType(.URL)
                    .autocapitalization(.none)
                    .keyboardType(.URL)

                Button(action: testConnection) {
                    HStack {
                        Text("Test Connection")
                        Spacer()
                        if isChecking {
                            ProgressView()
                        }
                    }
                }
                .disabled(isChecking || apiURL.isEmpty)

                Button("Save") {
                    settingsManager.apiBaseURL = apiURL
                }
                .disabled(apiURL == settingsManager.apiBaseURL)
            } header: {
                Text("Server Configuration")
            } footer: {
                Text("Enter the URL of your MedBot API server. Default is http://localhost:8001")
            }

            // Health status
            if let health = healthStatus {
                Section("Server Status") {
                    HStack {
                        Text("Status")
                        Spacer()
                        Text(health.status.capitalized)
                            .foregroundColor(health.status == "healthy" ? .green : .orange)
                    }

                    HStack {
                        Text("Version")
                        Spacer()
                        Text(health.version)
                            .foregroundColor(.secondary)
                    }

                    ForEach(Array(health.services.keys.sorted()), id: \.self) { key in
                        if let service = health.services[key] {
                            HStack {
                                Text(key.capitalized)
                                Spacer()
                                Image(systemName: service.status == "healthy" ? "checkmark.circle.fill" : "exclamationmark.circle.fill")
                                    .foregroundColor(service.status == "healthy" ? .green : .orange)
                            }
                        }
                    }
                }
            }

            // Error
            if let error = errorMessage {
                Section {
                    HStack {
                        Image(systemName: "exclamationmark.triangle.fill")
                            .foregroundColor(.orange)
                        Text(error)
                            .font(.caption)
                    }
                }
            }

            // Presets
            Section("Quick Setup") {
                Button("Local Development") {
                    apiURL = "http://localhost:8001"
                }

                Button("Local Network (Mac)") {
                    apiURL = "http://\(getLocalIP()):8001"
                }
            }
        }
        .navigationTitle("API Settings")
        .navigationBarTitleDisplayMode(.inline)
        .onAppear {
            apiURL = settingsManager.apiBaseURL
        }
    }

    private func testConnection() {
        isChecking = true
        errorMessage = nil
        healthStatus = nil

        // Update API service temporarily
        APIService.shared.updateBaseURL(apiURL)

        Task {
            do {
                let health = try await APIService.shared.healthCheck()

                await MainActor.run {
                    healthStatus = health
                    isChecking = false
                }
            } catch {
                await MainActor.run {
                    errorMessage = error.localizedDescription
                    isChecking = false
                }

                // Restore original URL
                APIService.shared.updateBaseURL(settingsManager.apiBaseURL)
            }
        }
    }

    private func getLocalIP() -> String {
        var address: String = "192.168.1.1"

        var ifaddr: UnsafeMutablePointer<ifaddrs>?
        guard getifaddrs(&ifaddr) == 0 else { return address }
        guard let firstAddr = ifaddr else { return address }

        for ptr in sequence(first: firstAddr, next: { $0.pointee.ifa_next }) {
            let interface = ptr.pointee
            let addrFamily = interface.ifa_addr.pointee.sa_family

            if addrFamily == UInt8(AF_INET) {
                let name = String(cString: interface.ifa_name)
                if name == "en0" {
                    var hostname = [CChar](repeating: 0, count: Int(NI_MAXHOST))
                    getnameinfo(interface.ifa_addr, socklen_t(interface.ifa_addr.pointee.sa_len),
                               &hostname, socklen_t(hostname.count), nil, socklen_t(0), NI_NUMERICHOST)
                    address = String(cString: hostname)
                }
            }
        }

        freeifaddrs(ifaddr)
        return address
    }
}

#Preview {
    SettingsView()
        .environmentObject(SettingsManager())
        .environmentObject(WatchSyncService.shared)
        .environmentObject(HistoryService.shared)
}
