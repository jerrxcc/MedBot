//
//  DoctorCard.swift
//  MedBotWatch
//
//  Compact doctor information card for Watch display
//

import SwiftUI

struct DoctorCard: View {
    let doctor: DoctorResult

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            // Name and designation
            HStack {
                Image(systemName: "person.crop.circle.fill")
                    .foregroundColor(.blue)
                    .font(.title3)

                VStack(alignment: .leading, spacing: 2) {
                    Text(doctor.name)
                        .font(.caption)
                        .fontWeight(.semibold)
                        .lineLimit(1)

                    if let designation = doctor.designation {
                        Text(designation)
                            .font(.caption2)
                            .foregroundColor(.secondary)
                            .lineLimit(1)
                    }
                }
            }

            // Specialty
            HStack(spacing: 4) {
                Image(systemName: "stethoscope")
                    .font(.caption2)
                Text(doctor.specialty)
                    .font(.caption2)
            }
            .foregroundColor(.orange)

            // Languages
            HStack(spacing: 4) {
                Image(systemName: "globe")
                    .font(.caption2)
                Text(doctor.languages.joined(separator: ", "))
                    .font(.caption2)
                    .lineLimit(1)
            }
            .foregroundColor(.secondary)

            // Clinic if available
            if let clinic = doctor.clinicName {
                HStack(spacing: 4) {
                    Image(systemName: "building.2")
                        .font(.caption2)
                    Text(clinic)
                        .font(.caption2)
                        .lineLimit(1)
                }
                .foregroundColor(.secondary)
            }

            // Contact if available
            if let contact = doctor.contact {
                HStack(spacing: 4) {
                    Image(systemName: "phone")
                        .font(.caption2)
                    Text(contact)
                        .font(.caption2)
                }
                .foregroundColor(.blue)
            }
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.gray.opacity(0.1))
        .cornerRadius(12)
    }
}

#Preview {
    DoctorCard(doctor: DoctorResult(
        name: "Dr. John Smith",
        specialty: "Cardiology",
        languages: ["English", "Mandarin"],
        designation: "Senior Consultant",
        clinicName: "Heart Care Clinic",
        contact: "6123 4567",
        matchScore: 0.95
    ))
    .padding()
}
