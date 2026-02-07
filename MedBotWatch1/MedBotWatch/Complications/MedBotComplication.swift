//
//  MedBotComplication.swift
//  MedBotWatch
//
//  Watch face complications for quick access to MedBot features
//

import WidgetKit
import SwiftUI

struct MedBotComplicationProvider: TimelineProvider {
    func placeholder(in context: Context) -> MedBotComplicationEntry {
        MedBotComplicationEntry(date: Date())
    }

    func getSnapshot(in context: Context, completion: @escaping (MedBotComplicationEntry) -> Void) {
        let entry = MedBotComplicationEntry(date: Date())
        completion(entry)
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<MedBotComplicationEntry>) -> Void) {
        let entry = MedBotComplicationEntry(date: Date())
        let timeline = Timeline(entries: [entry], policy: .never)
        completion(timeline)
    }
}

struct MedBotComplicationEntry: TimelineEntry {
    let date: Date
}

// MARK: - Complication Views

struct MedBotComplicationCircular: View {
    var body: some View {
        ZStack {
            AccessoryWidgetBackground()
            Image(systemName: "cross.case.fill")
                .font(.title2)
                .foregroundColor(.blue)
        }
    }
}

struct MedBotComplicationRectangular: View {
    var body: some View {
        HStack {
            Image(systemName: "cross.case.fill")
                .font(.title3)
                .foregroundColor(.blue)

            VStack(alignment: .leading) {
                Text("MedBot")
                    .font(.headline)
                Text("Medical Assistant")
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
        }
    }
}

struct MedBotComplicationInline: View {
    var body: some View {
        Label("MedBot", systemImage: "cross.case.fill")
    }
}

struct MedBotComplicationCorner: View {
    var body: some View {
        Image(systemName: "cross.case.fill")
            .font(.title3)
            .widgetLabel {
                Text("MedBot")
            }
    }
}

// MARK: - Widget Configuration

@main
struct MedBotComplicationWidget: Widget {
    let kind: String = "MedBotComplication"

    var body: some WidgetConfiguration {
        StaticConfiguration(kind: kind, provider: MedBotComplicationProvider()) { entry in
            MedBotComplicationEntryView(entry: entry)
        }
        .configurationDisplayName("MedBot")
        .description("Quick access to MedBot medical assistant")
        .supportedFamilies([
            .accessoryCircular,
            .accessoryRectangular,
            .accessoryInline,
            .accessoryCorner
        ])
    }
}

struct MedBotComplicationEntryView: View {
    @Environment(\.widgetFamily) var family
    var entry: MedBotComplicationEntry

    var body: some View {
        switch family {
        case .accessoryCircular:
            MedBotComplicationCircular()
        case .accessoryRectangular:
            MedBotComplicationRectangular()
        case .accessoryInline:
            MedBotComplicationInline()
        case .accessoryCorner:
            MedBotComplicationCorner()
        @unknown default:
            MedBotComplicationCircular()
        }
    }
}

#Preview("Circular", as: .accessoryCircular) {
    MedBotComplicationWidget()
} timeline: {
    MedBotComplicationEntry(date: Date())
}

#Preview("Rectangular", as: .accessoryRectangular) {
    MedBotComplicationWidget()
} timeline: {
    MedBotComplicationEntry(date: Date())
}
