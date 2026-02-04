//
//  ClinicSearchView.swift
//  MedBotWatch
//
//  Search for clinics by postal code or area
//

import SwiftUI

struct ClinicSearchView: View {
    @StateObject private var viewModel = ClinicSearchViewModel()
    @StateObject private var voiceService = VoiceService.shared

    var body: some View {
        ScrollView {
            VStack(spacing: 12) {
                // Voice input
                CompactVoiceInput(
                    text: $viewModel.query,
                    placeholder: NSLocalizedString("clinic_placeholder", comment: "Find clinics...")
                )

                // Postal code input
                HStack {
                    Image(systemName: "location.fill")
                        .foregroundColor(.blue)
                        .font(.caption)

                    TextField(
                        NSLocalizedString("clinic_postal", comment: "Postal Code"),
                        text: $viewModel.postalCode
                    )
                    .font(.caption)
                    .keyboardType(.numberPad)
                }
                .padding(8)
                .background(Color.gray.opacity(0.1))
                .cornerRadius(8)

                // Area picker
                Text(LocalizedStringKey("clinic_area"))
                    .font(.caption2)
                    .foregroundColor(.secondary)

                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        ForEach(viewModel.singaporeAreas.prefix(6), id: \.self) { area in
                            AreaChip(
                                area: area,
                                isSelected: viewModel.area == area
                            ) {
                                viewModel.area = viewModel.area == area ? "" : area
                            }
                        }
                    }
                }

                // Search button
                Button(action: {
                    Task {
                        await viewModel.searchClinics()
                    }
                }) {
                    if viewModel.isLoading {
                        ProgressView()
                    } else {
                        Text(LocalizedStringKey("button_search"))
                    }
                }
                .buttonStyle(.borderedProminent)
                .disabled(viewModel.isLoading)

                // Error message
                if let error = viewModel.errorMessage {
                    Text(error)
                        .font(.caption2)
                        .foregroundColor(.red)
                }

                // Results
                if viewModel.hasResults {
                    Text("\(viewModel.totalCount) clinics found")
                        .font(.caption2)
                        .foregroundColor(.secondary)

                    ForEach(viewModel.results) { clinic in
                        ClinicCard(clinic: clinic)
                    }
                }
            }
            .padding()
        }
        .localizedNavTitle("feature_clinics")
    }
}

struct AreaChip: View {
    let area: String
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(area)
                .font(.caption2)
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(isSelected ? Color.red : Color.gray.opacity(0.3))
                .foregroundColor(isSelected ? .white : .primary)
                .cornerRadius(12)
        }
        .buttonStyle(PlainButtonStyle())
    }
}
