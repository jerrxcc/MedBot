//
//  DoctorSearchView.swift
//  MedBotWatch
//
//  Search for doctors by specialty, language, or name
//

import SwiftUI

struct DoctorSearchView: View {
    @StateObject private var viewModel = DoctorSearchViewModel()
    @StateObject private var voiceService = VoiceService.shared

    var body: some View {
        ScrollView {
            VStack(spacing: 12) {
                // Voice input for natural language query
                CompactVoiceInput(
                    text: $viewModel.query,
                    placeholder: NSLocalizedString("doctor_placeholder", comment: "Find a doctor...")
                )

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

                // Search button
                Button(action: {
                    // Build query from filters if empty
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

                    Task {
                        await viewModel.searchDoctors()
                    }
                }) {
                    if viewModel.isLoading {
                        ProgressView()
                    } else {
                        Text(LocalizedStringKey("button_search"))
                    }
                }
                .buttonStyle(.borderedProminent)
                .disabled(viewModel.isLoading && viewModel.query.isEmpty && viewModel.specialty.isEmpty)

                // Error message
                if let error = viewModel.errorMessage {
                    Text(error)
                        .font(.caption2)
                        .foregroundColor(.red)
                }

                // Results
                if viewModel.hasResults {
                    Text("\(viewModel.totalCount) results")
                        .font(.caption2)
                        .foregroundColor(.secondary)

                    ForEach(viewModel.results) { doctor in
                        DoctorCard(doctor: doctor)
                    }
                }
            }
            .padding()
        }
        .localizedNavTitle("feature_doctors")
    }
}

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
