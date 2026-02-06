//
//  ClinicCard.swift
//  MedBotWatch
//
//  Compact clinic information card for Watch display
//

import SwiftUI

struct ClinicCard: View {
    let clinic: ClinicResult

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            // Name and distance
            HStack {
                Image(systemName: "building.2.fill")
                    .foregroundColor(.red)
                    .font(.title3)

                VStack(alignment: .leading, spacing: 2) {
                    Text(clinic.name)
                        .font(.caption)
                        .fontWeight(.semibold)
                        .lineLimit(2)

                    if let distance = clinic.distanceString {
                        HStack(spacing: 2) {
                            Image(systemName: "location")
                                .font(.caption2)
                            Text(distance)
                                .font(.caption2)
                        }
                        .foregroundColor(.blue)
                    }
                }

                Spacer()
            }

            // Area
            HStack(spacing: 4) {
                Image(systemName: "map")
                    .font(.caption2)
                Text(clinic.area)
                    .font(.caption2)

                if let nearby = clinic.fromNearbyArea {
                    Text("(from \(nearby))")
                        .font(.caption2)
                        .foregroundColor(.secondary)
                }
            }
            .foregroundColor(.orange)

            // Address
            Text(clinic.address)
                .font(.caption2)
                .foregroundColor(.secondary)
                .lineLimit(2)

            // Contact if available
            if let contact = clinic.contact {
                Button(action: {
                    // Could trigger phone call on iOS
                }) {
                    HStack(spacing: 4) {
                        Image(systemName: "phone.fill")
                            .font(.caption2)
                        Text(contact)
                            .font(.caption2)
                    }
                    .foregroundColor(.blue)
                }
                .buttonStyle(PlainButtonStyle())
            }
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.gray.opacity(0.1))
        .cornerRadius(12)
    }
}

#Preview {
    ClinicCard(clinic: ClinicResult(
        name: "Bedok Family Clinic",
        address: "123 Bedok North Ave 3, #01-456",
        area: "Bedok",
        contact: "6789 0123",
        distanceMeters: 850,
        postalCode: "460123",
        fromNearbyArea: nil
    ))
    .padding()
}
