//
//  BilingualText.swift
//  MedBotWatch
//
//  Helper for bilingual text display
//

import SwiftUI

struct BilingualText: View {
    let key: String
    @EnvironmentObject var settingsManager: SettingsManager

    var body: some View {
        Text(LocalizedStringKey(key))
    }
}

// Localized navigation title
struct LocalizedNavTitle: ViewModifier {
    let key: String

    func body(content: Content) -> some View {
        content.navigationTitle(Text(LocalizedStringKey(key)))
    }
}

extension View {
    func localizedNavTitle(_ key: String) -> some View {
        modifier(LocalizedNavTitle(key: key))
    }
}

// Loading view with localized text
struct LoadingView: View {
    let messageKey: String

    var body: some View {
        VStack(spacing: 12) {
            ProgressView()
            Text(LocalizedStringKey(messageKey))
                .font(.caption)
                .foregroundColor(.secondary)
        }
    }
}

// Error view with localized text
struct ErrorView: View {
    let message: String
    let retryAction: (() -> Void)?

    var body: some View {
        VStack(spacing: 12) {
            Image(systemName: "exclamationmark.triangle")
                .font(.title2)
                .foregroundColor(.orange)

            Text(message)
                .font(.caption)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)

            if let retry = retryAction {
                Button(action: retry) {
                    Text(LocalizedStringKey("button_retry"))
                        .font(.caption)
                }
            }
        }
        .padding()
    }
}

// Empty state view
struct EmptyStateView: View {
    let iconName: String
    let titleKey: String
    let messageKey: String

    var body: some View {
        VStack(spacing: 8) {
            Image(systemName: iconName)
                .font(.largeTitle)
                .foregroundColor(.secondary)

            Text(LocalizedStringKey(titleKey))
                .font(.headline)

            Text(LocalizedStringKey(messageKey))
                .font(.caption)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .padding()
    }
}
