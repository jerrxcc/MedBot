//
//  WatchSyncService.swift
//  MedBotiOS
//
//  Manages communication with Apple Watch via WatchConnectivity
//

import Foundation
import WatchConnectivity

class WatchSyncService: NSObject, ObservableObject {
    static let shared = WatchSyncService()

    @Published var isWatchPaired = false
    @Published var isWatchReachable = false
    @Published var lastSyncDate: Date?

    private var session: WCSession?

    override init() {
        super.init()

        if WCSession.isSupported() {
            session = WCSession.default
            session?.delegate = self
            session?.activate()
        }
    }

    // MARK: - Send Data to Watch

    func sendSettings(_ settings: [String: Any]) {
        guard let session = session, session.isPaired else { return }

        do {
            try session.updateApplicationContext(settings)
        } catch {
            print("Failed to send settings to Watch: \(error)")
        }
    }

    func sendMessage(_ message: [String: Any], replyHandler: (([String: Any]) -> Void)? = nil) {
        guard let session = session, session.isReachable else { return }

        session.sendMessage(message, replyHandler: replyHandler) { error in
            print("Failed to send message to Watch: \(error)")
        }
    }

    // MARK: - Sync History

    func syncHistory(_ history: [HistoryItem]) {
        guard let session = session, session.isPaired else { return }

        let historyData = history.prefix(10).map { item -> [String: Any] in
            return [
                "id": item.id.uuidString,
                "type": item.type.rawValue,
                "query": item.query,
                "summary": item.summary,
                "timestamp": item.timestamp.timeIntervalSince1970
            ]
        }

        do {
            try session.updateApplicationContext(["history": historyData])
            lastSyncDate = Date()
        } catch {
            print("Failed to sync history: \(error)")
        }
    }
}

// MARK: - WCSessionDelegate

extension WatchSyncService: WCSessionDelegate {
    func session(_ session: WCSession, activationDidCompleteWith activationState: WCSessionActivationState, error: Error?) {
        DispatchQueue.main.async {
            self.isWatchPaired = session.isPaired
            self.isWatchReachable = session.isReachable
        }
    }

    func sessionDidBecomeInactive(_ session: WCSession) {
        // Handle session becoming inactive
    }

    func sessionDidDeactivate(_ session: WCSession) {
        // Reactivate session
        session.activate()
    }

    func sessionReachabilityDidChange(_ session: WCSession) {
        DispatchQueue.main.async {
            self.isWatchReachable = session.isReachable
        }
    }

    func session(_ session: WCSession, didReceiveMessage message: [String: Any]) {
        // Handle messages from Watch
        if let type = message["type"] as? String {
            switch type {
            case "symptom_query":
                handleSymptomQuery(message)
            case "medication_query":
                handleMedicationQuery(message)
            default:
                break
            }
        }
    }

    func session(_ session: WCSession, didReceiveMessage message: [String: Any], replyHandler: @escaping ([String: Any]) -> Void) {
        // Handle messages that expect a reply
        if let type = message["type"] as? String {
            switch type {
            case "health_check":
                Task {
                    do {
                        let health = try await APIService.shared.healthCheck()
                        replyHandler(["status": health.status])
                    } catch {
                        replyHandler(["error": error.localizedDescription])
                    }
                }
            default:
                replyHandler(["error": "Unknown message type"])
            }
        }
    }

    // MARK: - Message Handlers

    private func handleSymptomQuery(_ message: [String: Any]) {
        guard let query = message["query"] as? String else { return }

        Task {
            do {
                let response = try await APIService.shared.analyzeSymptoms(query: query)

                // Save to history
                HistoryService.shared.addItem(
                    type: .symptoms,
                    query: query,
                    response: response.fullResponse,
                    summary: response.summary.short
                )
            } catch {
                print("Failed to process symptom query from Watch: \(error)")
            }
        }
    }

    private func handleMedicationQuery(_ message: [String: Any]) {
        guard let query = message["query"] as? String else { return }

        Task {
            do {
                let response = try await APIService.shared.lookupMedication(query: query)

                // Save to history
                HistoryService.shared.addItem(
                    type: .medication,
                    query: query,
                    response: response.fullResponse,
                    summary: response.summary.short
                )
            } catch {
                print("Failed to process medication query from Watch: \(error)")
            }
        }
    }
}
