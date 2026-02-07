//
//  DoctorSearchView.swift
//  MedBotWatch
//
//  Search for doctors by specialty, language, or name
//

import SwiftUI

struct DoctorSearchView: View {
    @StateObject private var viewModel = DoctorSearchViewModel()

    var body: some View {
        ScrollView {
            VStack(spacing: 12) {
                DoctorSearchInput(viewModel: viewModel)
                DoctorFilters(viewModel: viewModel)
                DoctorSearchButton(viewModel: viewModel)
                DoctorResultsList(viewModel: viewModel)
            }
            .padding()
        }
        .localizedNavTitle("feature_doctors")
    }
}

// MARK: - Sub-views

private struct DoctorSearchInput: View {
    @ObservedObject var viewModel: DoctorSearchViewModel

    var body: some View {
        TextField(
            L("doctor_placeholder"),
            text: $viewModel.query
        )
        .font(.caption)
        .textFieldStyle(.plain)
        .padding(8)
        .background(Color.gray.opacity(0.15))
        .cornerRadius(8)
    }
}

private struct DoctorFilters: View {
    @ObservedObject var viewModel: DoctorSearchViewModel

    var body: some View {
        VStack(spacing: 8) {
            // Specialty filter
            if !viewModel.commonSpecialties.isEmpty {
                Text(LocalizedStringKey("doctor_specialty"))
                    .font(.caption2)
                    .foregroundColor(.secondary)

                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        ForEach(viewModel.commonSpecialties.prefix(5), id: \.self) { specialty in
                            SpecialtyChip(
                                specialty: specialty,
                                isSelected: viewModel.specialty == specialty
                            ) {
                                viewModel.specialty = viewModel.specialty == specialty ? "" : specialty
                            }
                        }
                    }
                }
            }

            // Language filter
            Text(LocalizedStringKey("doctor_language"))
                .font(.caption2)
                .foregroundColor(.secondary)

            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 8) {
                    ForEach(viewModel.commonLanguages.prefix(4), id: \.self) { lang in
                        LanguageChip(
                            language: lang,
                            isSelected: viewModel.language == lang
                        ) {
                            viewModel.language = viewModel.language == lang ? "" : lang
                        }
                    }
                }
            }
        }
    }
}

private struct DoctorSearchButton: View {
    @ObservedObject var viewModel: DoctorSearchViewModel

    var body: some View {
        VStack(spacing: 8) {
            Button(action: {
                if viewModel.query.isEmpty {
                    var parts: [String] = []
                    if !viewModel.specialty.isEmpty {
                        parts.append(viewModel.specialty)
                    }
                    if !viewModel.language.isEmpty {
                        parts.append("speaks \(viewModel.language)")
                    }
                    viewModel.query = parts.joined(separator: " ")
                }
                Task { await viewModel.searchDoctors() }
            }) {
                if viewModel.isLoading {
                    ProgressView()
                } else {
                    Text(LocalizedStringKey("button_search"))
                }
            }
            .buttonStyle(.borderedProminent)
            .disabled(viewModel.isLoading && viewModel.query.isEmpty && viewModel.specialty.isEmpty)

            if let error = viewModel.errorMessage {
                Text(error)
                    .font(.caption2)
                    .foregroundColor(.red)
            }
        }
    }
}

private struct DoctorResultsList: View {
    @ObservedObject var viewModel: DoctorSearchViewModel

    var body: some View {
        if viewModel.hasResults {
            VStack(spacing: 8) {
                Text("\(viewModel.totalCount) results")
                    .font(.caption2)
                    .foregroundColor(.secondary)

                ForEach(viewModel.results) { doctor in
                    NavigationLink(destination: DoctorDetailView(doctor: doctor)) {
                        DoctorCard(doctor: doctor)
                    }
                    .buttonStyle(.plain)
                }
            }
        }
    }
}

// MARK: - Chips

struct SpecialtyChip: View {
    let specialty: String
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(specialty)
                .font(.caption2)
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(isSelected ? Color.blue : Color.gray.opacity(0.3))
                .foregroundColor(isSelected ? .white : .primary)
                .cornerRadius(12)
        }
        .buttonStyle(PlainButtonStyle())
    }
}

struct LanguageChip: View {
    let language: String
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(language)
                .font(.caption2)
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(isSelected ? Color.orange : Color.gray.opacity(0.3))
                .foregroundColor(isSelected ? .white : .primary)
                .cornerRadius(12)
        }
        .buttonStyle(PlainButtonStyle())
    }
}
