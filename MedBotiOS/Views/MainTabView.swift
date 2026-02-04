//
//  MainTabView.swift
//  MedBotiOS
//
//  Main tab navigation for iOS app
//

import SwiftUI

struct MainTabView: View {
    @State private var selectedTab = 0

    var body: some View {
        TabView(selection: $selectedTab) {
            SymptomView()
                .tabItem {
                    Label("Symptoms", systemImage: "stethoscope")
                }
                .tag(0)

            MedicationView()
                .tabItem {
                    Label("Medication", systemImage: "pill.fill")
                }
                .tag(1)

            RecordsView()
                .tabItem {
                    Label("Records", systemImage: "doc.text.fill")
                }
                .tag(2)

            SearchTabView()
                .tabItem {
                    Label("Search", systemImage: "magnifyingglass")
                }
                .tag(3)

            SettingsView()
                .tabItem {
                    Label("Settings", systemImage: "gear")
                }
                .tag(4)
        }
    }
}

struct SearchTabView: View {
    @State private var selectedSearch = 0

    var body: some View {
        NavigationStack {
            VStack {
                Picker("Search Type", selection: $selectedSearch) {
                    Text("Doctors").tag(0)
                    Text("Clinics").tag(1)
                }
                .pickerStyle(.segmented)
                .padding()

                if selectedSearch == 0 {
                    DoctorsView()
                } else {
                    ClinicsView()
                }
            }
            .navigationTitle("Search")
        }
    }
}

#Preview {
    MainTabView()
        .environmentObject(SettingsManager())
        .environmentObject(WatchSyncService.shared)
        .environmentObject(HistoryService.shared)
}
