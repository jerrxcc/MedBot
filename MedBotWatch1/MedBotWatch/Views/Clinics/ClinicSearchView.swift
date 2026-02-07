//
//  ClinicSearchView.swift
//  MedBotWatch
//
//  Search for clinics by postal code or area
//

import SwiftUI

struct ClinicSearchView: View {
    @StateObject private var viewModel = ClinicSearchViewModel()

    var body: some View {
        ScrollView {
            VStack(spacing: 12) {
                ClinicSearchInput(viewModel: viewModel)
                ClinicAreaFilter(viewModel: viewModel)
                ClinicSearchButton(viewModel: viewModel)
                ClinicResultsList(viewModel: viewModel)
            }
            .padding()
        }
        .localizedNavTitle("feature_clinics")
    }
}

// MARK: - Sub-views

private struct ClinicSearchInput: View {
    @ObservedObject var viewModel: ClinicSearchViewModel

    var body: some View {
        HStack {
            Image(systemName: "location.fill")
                .foregroundColor(.blue)
                .font(.caption)

            TextField(
                L("clinic_postal"),
                text: $viewModel.postalCode
            )
            .font(.caption)
        }
        .padding(8)
        .background(Color.gray.opacity(0.1))
        .cornerRadius(8)
    }
}

private struct ClinicAreaFilter: View {
    @ObservedObject var viewModel: ClinicSearchViewModel

    var body: some View {
        VStack(spacing: 8) {
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
        }
    }
}

private struct ClinicSearchButton: View {
    @ObservedObject var viewModel: ClinicSearchViewModel

    var body: some View {
        VStack(spacing: 8) {
            Button(action: {
                Task { await viewModel.searchClinics() }
            }) {
                if viewModel.isLoading {
                    ProgressView()
                } else {
                    Text(LocalizedStringKey("button_search"))
                }
            }
            .buttonStyle(.borderedProminent)
            .disabled(viewModel.isLoading)

            if let error = viewModel.errorMessage {
                Text(error)
                    .font(.caption2)
                    .foregroundColor(.red)
            }
        }
    }
}

private struct ClinicResultsList: View {
    @ObservedObject var viewModel: ClinicSearchViewModel

    var body: some View {
        if viewModel.hasResults {
            VStack(spacing: 8) {
                Text("\(viewModel.totalCount) clinics found")
                    .font(.caption2)
                    .foregroundColor(.secondary)

                ForEach(viewModel.results) { clinic in
                    NavigationLink(destination: ClinicDetailView(clinic: clinic)) {
                        ClinicCard(clinic: clinic)
                    }
                    .buttonStyle(.plain)
                }
            }
        }
    }
}

// MARK: - Chips

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
