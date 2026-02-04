//
//  APIService.swift
//  MedBotiOS
//
//  Network layer for communicating with MedBot REST API
//  Shared implementation with Watch app
//

import Foundation

/// Errors that can occur during API operations
enum APIError: Error, LocalizedError {
    case invalidURL
    case networkError(Error)
    case decodingError(Error)
    case serverError(String)
    case noData

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid server URL"
        case .networkError(let error):
            return "Network error: \(error.localizedDescription)"
        case .decodingError(let error):
            return "Failed to parse response: \(error.localizedDescription)"
        case .serverError(let message):
            return "Server error: \(message)"
        case .noData:
            return "No data received from server"
        }
    }
}

/// Main API service for MedBot backend communication
class APIService: ObservableObject {
    static let shared = APIService()

    private var baseURL: String
    private let session: URLSession
    private let decoder: JSONDecoder

    init(baseURL: String = "http://localhost:8001") {
        self.baseURL = baseURL

        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 60
        config.timeoutIntervalForResource = 120
        self.session = URLSession(configuration: config)

        self.decoder = JSONDecoder()
    }

    func updateBaseURL(_ url: String) {
        self.baseURL = url
    }

    // MARK: - Symptom Analysis

    func analyzeSymptoms(
        query: String,
        language: String = "auto",
        history: [[String: String]]? = nil,
        sessionId: String? = nil
    ) async throws -> SymptomResponse {
        let request = SymptomRequest(
            query: query,
            language: language,
            history: history,
            sessionId: sessionId
        )

        return try await post(
            endpoint: "/api/v1/symptoms/analyze",
            body: request
        )
    }

    // MARK: - Medication Lookup

    func lookupMedication(
        query: String,
        language: String = "auto",
        history: [[String: String]]? = nil
    ) async throws -> MedicationResponse {
        let request = MedicationRequest(
            query: query,
            language: language,
            history: history
        )

        return try await post(
            endpoint: "/api/v1/medication/lookup",
            body: request
        )
    }

    // MARK: - Records Analysis

    func analyzeRecords(
        content: String,
        language: String = "auto",
        recordType: String = "general"
    ) async throws -> RecordsResponse {
        let request = RecordsRequest(
            content: content,
            language: language,
            recordType: recordType
        )

        return try await post(
            endpoint: "/api/v1/records/analyze",
            body: request
        )
    }

    // MARK: - Doctor Search

    func searchDoctors(
        query: String,
        specialty: String? = nil,
        language: String? = nil,
        name: String? = nil,
        limit: Int = 10
    ) async throws -> DoctorSearchResponse {
        let request = DoctorSearchRequest(
            query: query,
            specialty: specialty,
            language: language,
            name: name,
            limit: limit
        )

        return try await post(
            endpoint: "/api/v1/doctors/search",
            body: request
        )
    }

    // MARK: - Clinic Search

    func searchClinics(
        query: String,
        postalCode: String? = nil,
        area: String? = nil,
        clinicName: String? = nil,
        limit: Int = 10
    ) async throws -> ClinicSearchResponse {
        let request = ClinicSearchRequest(
            query: query,
            postalCode: postalCode,
            area: area,
            clinicName: clinicName,
            limit: limit
        )

        return try await post(
            endpoint: "/api/v1/clinics/search",
            body: request
        )
    }

    // MARK: - Health Check

    func healthCheck() async throws -> HealthResponse {
        let url = URL(string: "\(baseURL)/api/v1/health")!
        let (data, response) = try await session.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw APIError.serverError("Health check failed")
        }

        return try decoder.decode(HealthResponse.self, from: data)
    }

    // MARK: - Private Helpers

    private func post<T: Encodable, R: Decodable>(
        endpoint: String,
        body: T
    ) async throws -> R {
        guard let url = URL(string: "\(baseURL)\(endpoint)") else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("MedBotiOS/1.0", forHTTPHeaderField: "User-Agent")

        let encoder = JSONEncoder()
        request.httpBody = try encoder.encode(body)

        do {
            let (data, response) = try await session.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse else {
                throw APIError.noData
            }

            guard httpResponse.statusCode == 200 else {
                if let errorJson = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                   let detail = errorJson["detail"] as? [String: Any],
                   let error = detail["error"] as? String {
                    throw APIError.serverError(error)
                }
                throw APIError.serverError("Server returned status \(httpResponse.statusCode)")
            }

            do {
                return try decoder.decode(R.self, from: data)
            } catch {
                throw APIError.decodingError(error)
            }
        } catch let error as APIError {
            throw error
        } catch {
            throw APIError.networkError(error)
        }
    }
}

// MARK: - Health Response

struct HealthResponse: Codable {
    let status: String
    let version: String
    let services: [String: ServiceStatus]
}

struct ServiceStatus: Codable {
    let status: String
    let error: String?
}
