//
//  DoctorsView.swift
//  MedBotiOS
//
//  Doctor search view with filtering
//

import SwiftUI

struct DoctorsView: View {
    @EnvironmentObject var historyService: HistoryService

    @State private var query = ""
    @State private var specialty = ""
    @State private var language = ""
    @State private var isLoading = false
    @State private var results: [DoctorResult] = []
    @State private var errorMessage: String?
    @State private var showFilters = false

    let specialties = [
        "All", "Cardiology", "Dermatology", "ENT", "Gastroenterology",
        "General Practice", "Neurology", "Oncology", "Orthopedics",
        "Pediatrics", "Psychiatry"
    ]

    let languages = [
        "All", "English", "Mandarin", "Malay", "Tamil", "Cantonese", "Hokkien"
    ]

    var body: some View {
        VStack(spacing: 0) {
            // Search bar
            HStack {
                Image(systemName: "magnifyingglass")
                    .foregroundColor(.secondary)

                TextField("Search doctors...", text: $query)
                    .textFieldStyle(.plain)
                    .onSubmit(searchDoctors)

                if !query.isEmpty {
                    Button(action: { query = "" }) {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundColor(.secondary)
                    }
                }

                Button(action: { showFilters.toggle() }) {
                    Image(systemName: "line.3.horizontal.decrease.circle")
                        .foregroundColor(hasFilters ? .blue : .secondary)
                }
            }
            .padding()
            .background(Color(.secondarySystemBackground))

            // Filters
            if showFilters {
                VStack(spacing: 12) {
                    Picker("Specialty", selection: $specialty) {
                        ForEach(specialties, id: \.self) { Text($0).tag($0 == "All" ? "" : $0) }
                    }

                    Picker("Language", selection: $language) {
                        ForEach(languages, id: \.self) { Text($0).tag($0 == "All" ? "" : $0) }
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
                EmptySearchView(icon: "person.crop.circle.badge.questionmark", message: "Search for doctors by name, specialty, or language")
                Spacer()
            } else {
                List(results) { doctor in
                    DoctorRow(doctor: doctor)
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
        .onChange(of: specialty) { _, _ in searchDoctors() }
        .onChange(of: language) { _, _ in searchDoctors() }
    }

    var hasFilters: Bool {
        !specialty.isEmpty || !language.isEmpty
    }

    private func searchDoctors() {
        var searchQuery = query
        if searchQuery.isEmpty {
            if !specialty.isEmpty {
                searchQuery = specialty
            } else if !language.isEmpty {
                searchQuery = "speaks \(language)"
            } else {
                return
            }
        }

        isLoading = true
        errorMessage = nil

        Task {
            do {
                let response = try await APIService.shared.searchDoctors(
                    query: searchQuery,
                    specialty: specialty.isEmpty ? nil : specialty,
                    language: language.isEmpty ? nil : language,
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

struct DoctorRow: View {
    let doctor: DoctorResult

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "person.crop.circle.fill")
                    .font(.title)
                    .foregroundColor(.blue)

                VStack(alignment: .leading) {
                    Text(doctor.name)
                        .font(.headline)

                    if let designation = doctor.designation {
                        Text(designation)
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                }

                Spacer()

                if let score = doctor.matchScore {
                    Text("\(Int(score * 100))%")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }

            HStack {
                Label(doctor.specialty, systemImage: "stethoscope")
                    .font(.caption)
                    .foregroundColor(.orange)
            }

            HStack {
                Label(doctor.languages.joined(separator: ", "), systemImage: "globe")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            if let clinic = doctor.clinicName {
                Label(clinic, systemImage: "building.2")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            if let contact = doctor.contact {
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

struct EmptySearchView: View {
    let icon: String
    let message: String

    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: icon)
                .font(.system(size: 50))
                .foregroundColor(.secondary)

            Text(message)
                .font(.subheadline)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
        }
    }
}
