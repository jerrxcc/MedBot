//
//  HistoryListView.swift
//  MedBotiOS
//
//  Conversation history with search and filtering
//

import SwiftUI

struct HistoryListView: View {
    @EnvironmentObject var historyService: HistoryService

    @State private var searchText = ""
    @State private var selectedType: HistoryType?
    @State private var showingClearAlert = false

    var filteredItems: [HistoryItem] {
        var items = historyService.items

        // Filter by type
        if let type = selectedType {
            items = items.filter { $0.type == type }
        }

        // Filter by search text
        if !searchText.isEmpty {
            items = items.filter {
                $0.query.localizedCaseInsensitiveContains(searchText) ||
                $0.response.localizedCaseInsensitiveContains(searchText) ||
                $0.summary.localizedCaseInsensitiveContains(searchText)
            }
        }

        return items
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Type filter
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 12) {
                        FilterChip(
                            title: "All",
                            isSelected: selectedType == nil,
                            color: .gray
                        ) {
                            selectedType = nil
                        }

                        ForEach(HistoryType.allCases, id: \.self) { type in
                            FilterChip(
                                title: type.rawValue.capitalized,
                                isSelected: selectedType == type,
                                color: type.color
                            ) {
                                selectedType = selectedType == type ? nil : type
                            }
                        }
                    }
                    .padding(.horizontal)
                    .padding(.vertical, 8)
                }
                .background(Color(.secondarySystemBackground))

                // History list
                if filteredItems.isEmpty {
                    Spacer()
                    EmptyHistoryView(hasItems: !historyService.items.isEmpty)
                    Spacer()
                } else {
                    List {
                        ForEach(filteredItems) { item in
                            NavigationLink(destination: HistoryDetailView(item: item)) {
                                HistoryRow(item: item)
                            }
                        }
                        .onDelete { indexSet in
                            for index in indexSet {
                                historyService.deleteItem(filteredItems[index])
                            }
                        }
                    }
                    .listStyle(.plain)
                }
            }
            .navigationTitle("History")
            .searchable(text: $searchText, prompt: "Search history")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: { showingClearAlert = true }) {
                        Image(systemName: "trash")
                    }
                    .disabled(historyService.items.isEmpty)
                }
            }
            .alert("Clear History", isPresented: $showingClearAlert) {
                Button("Cancel", role: .cancel) {}
                Button("Clear All", role: .destructive) {
                    historyService.clearHistory()
                }
            } message: {
                Text("Are you sure you want to delete all history? This cannot be undone.")
            }
        }
    }
}

struct FilterChip: View {
    let title: String
    let isSelected: Bool
    let color: Color
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(title)
                .font(.caption)
                .fontWeight(isSelected ? .semibold : .regular)
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(isSelected ? color : Color(.tertiarySystemBackground))
                .foregroundColor(isSelected ? .white : .primary)
                .cornerRadius(16)
        }
        .buttonStyle(.plain)
    }
}

struct HistoryRow: View {
    let item: HistoryItem

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: item.type.icon)
                .font(.title2)
                .foregroundColor(item.type.color)
                .frame(width: 40)

            VStack(alignment: .leading, spacing: 4) {
                Text(item.query)
                    .font(.headline)
                    .lineLimit(1)

                Text(item.summary)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .lineLimit(2)

                Text(item.timestamp, style: .relative)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding(.vertical, 4)
    }
}

struct HistoryDetailView: View {
    let item: HistoryItem

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                // Header
                HStack {
                    Image(systemName: item.type.icon)
                        .font(.title)
                        .foregroundColor(item.type.color)

                    VStack(alignment: .leading) {
                        Text(item.type.rawValue.capitalized)
                            .font(.headline)
                        Text(item.timestamp, style: .date)
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }

                Divider()

                // Query
                VStack(alignment: .leading, spacing: 8) {
                    Text("Query")
                        .font(.headline)
                    Text(item.query)
                        .font(.body)
                        .padding()
                        .background(Color(.secondarySystemBackground))
                        .cornerRadius(8)
                }

                // Summary
                VStack(alignment: .leading, spacing: 8) {
                    Text("Summary")
                        .font(.headline)
                    Text(item.summary)
                        .font(.body)
                        .foregroundColor(.secondary)
                }

                // Full Response
                VStack(alignment: .leading, spacing: 8) {
                    Text("Full Response")
                        .font(.headline)
                    Text(item.response)
                        .font(.body)
                }
            }
            .padding()
        }
        .navigationTitle("Details")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                ShareLink(item: formatForShare(item))
            }
        }
    }

    private func formatForShare(_ item: HistoryItem) -> String {
        """
        MedBot - \(item.type.rawValue.capitalized)
        Date: \(item.timestamp.formatted())

        Query: \(item.query)

        Summary: \(item.summary)

        Response:
        \(item.response)
        """
    }
}

struct EmptyHistoryView: View {
    let hasItems: Bool

    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "clock.arrow.circlepath")
                .font(.system(size: 50))
                .foregroundColor(.secondary)

            Text(hasItems ? "No matching results" : "No History Yet")
                .font(.headline)

            Text(hasItems ? "Try adjusting your filters or search" : "Your medical consultations will appear here")
                .font(.subheadline)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
        }
    }
}
