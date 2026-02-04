//
//  ClinicsView.swift
//  MedBotiOS
//
//  Clinic search view with location-based search
//

import SwiftUI

struct ClinicsView: View {
    @EnvironmentObject var historyService: HistoryService

    @State private var query = ""
    @State private var postalCode = ""
    @State private var selectedArea = ""
    @State private var isLoading = false
    @State private var results: [ClinicResult] = []
    @State private var errorMessage: String?
    @State private var showFilters = false

    let singaporeAreas = [
        "All", "Ang Mo Kio", "Bedok", "Bishan", "Bukit Batok", "Bukit Merah",
        "Clementi", "Geylang", "Hougang", "Jurong East", "Jurong West",
        "Kallang", "Marine Parade", "Pasir Ris", "Punggol", "Queenstown",
        "Sembawang", "Sengkang", "Serangoon", "Tampines", "Toa Payoh",
        "Woodlands", "Yishun"
    ]

    var body: some View {
        VStack(spacing: 0) {
            // Search bar
            HStack {
                Image(systemName: "magnifyingglass")
                    .foregroundColor(.secondary)

                TextField("Search clinics...", text: $query)
                    .textFieldStyle(.plain)
                    .onSubmit(searchClinics)

                if !query.isEmpty {
                    Button(action: { query = "" }) {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundColor(.secondary)
                    }
                }

                Button(action: { showFilters.toggle() }) {
                    Image(systemName: "location.circle")
                        .foregroundColor(hasFilters ? .blue : .secondary)
                }
            }
            .padding()
            .background(Color(.secondarySystemBackground))

            // Filters
            if showFilters {
                VStack(spacing: 12) {
                    // Postal code
                    HStack {
                        Text("Postal Code")
                            .font(.subheadline)
                        Spacer()
                        TextField("e.g., 640123", text: $postalCode)
                            .textFieldStyle(.roundedBorder)
                            .keyboardType(.numberPad)
                            .frame(width: 120)
                    }

                    // Area picker
                    Picker("Area", selection: $selectedArea) {
                        ForEach(singaporeAreas, id: \.self) {
                            Text($0).tag($0 == "All" ? "" : $0)
                        }
                    }
                }
                .padding()
                .background(Color(.tertiarySystemBackground))
            }

            // Results
            if isLoading {
                Spacer()
                ProgressView("Searching...")
                Spacer()
            } else if results.isEmpty {
                Spacer()
                EmptySearchView(icon: "building.2.crop.circle.badge.questionmark", message: "Search for clinics by postal code, area, or name")
                Spacer()
            } else {
                List(results) { clinic in
                    ClinicRow(clinic: clinic)
                }
                .listStyle(.plain)
            }

            // Error
            if let error = errorMessage {
                Text(error)
                    .font(.caption)
                    .foregroundColor(.red)
                    .padding()
            }
        }
        .onChange(of: postalCode) { _, newValue in
            if newValue.count == 6 {
                searchClinics()
            }
        }
        .onChange(of: selectedArea) { _, _ in searchClinics() }
    }

    var hasFilters: Bool {
        !postalCode.isEmpty || !selectedArea.isEmpty
    }

    private func searchClinics() {
        var searchQuery = query
        if searchQuery.isEmpty {
            if !postalCode.isEmpty {
                searchQuery = "Clinics near postal code \(postalCode)"
            } else if !selectedArea.isEmpty {
                searchQuery = "Clinics in \(selectedArea)"
            } else {
                return
            }
        }

        isLoading = true
        errorMessage = nil

        Task {
            do {
                let response = try await APIService.shared.searchClinics(
                    query: searchQuery,
                    postalCode: postalCode.isEmpty ? nil : postalCode,
                    area: selectedArea.isEmpty ? nil : selectedArea,
                    limit: 20
                )

                await MainActor.run {
                    results = response.results
                    isLoading = false
                }
            } catch {
                await MainActor.run {
                    errorMessage = error.localizedDescription
                    isLoading = false
                }
            }
        }
    }
}

struct ClinicRow: View {
    let clinic: ClinicResult

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "building.2.fill")
                    .font(.title)
                    .foregroundColor(.red)

                VStack(alignment: .leading) {
                    Text(clinic.name)
                        .font(.headline)

                    if let distance = clinic.distanceString {
                        HStack(spacing: 4) {
                            Image(systemName: "location")
                            Text(distance)
                        }
                        .font(.caption)
                        .foregroundColor(.blue)
                    }
                }

                Spacer()
            }

            HStack {
                Label(clinic.area, systemImage: "map")
                    .font(.caption)
                    .foregroundColor(.orange)

                if let nearby = clinic.fromNearbyArea {
                    Text("(from \(nearby))")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }

            Text(clinic.address)
                .font(.caption)
                .foregroundColor(.secondary)

            if let contact = clinic.contact {
                Button(action: {
                    if let url = URL(string: "tel:\(contact.replacingOccurrences(of: " ", with: ""))") {
                        UIApplication.shared.open(url)
                    }
                }) {
                    Label(contact, systemImage: "phone.fill")
                        .font(.caption)
                }
            }
        }
        .padding(.vertical, 8)
    }
}
