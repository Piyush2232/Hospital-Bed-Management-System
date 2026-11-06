import pytest
import json

class TestSystemE2E:
    """Level 3: System / End-to-End Testing modeling the complete clinical workflow."""

    def test_complete_patient_inpatient_journey(self, client, seeded_db):
        # Step 1: Query recommendation
        rec_res = client.get("/api/beds/recommend?ward_type=Emergency&bed_type=Oxygen")
        assert rec_res.status_code == 200
        rec_beds = rec_res.get_json()
        assert len(rec_beds) > 0
        assigned_eme_bed = rec_beds[0]["id"]

        # Step 2: Admit Patient
        admit_payload = {
            "name": "Vikram Seth",
            "age": 48,
            "gender": "Male",
            "priority": "High",
            "medical_condition": "Acute breathlessness",
            "bed_id": assigned_eme_bed
        }
        admit_res = client.post("/api/patients/admit", data=json.dumps(admit_payload), content_type="application/json")
        assert admit_res.status_code == 201
        patient_id = admit_res.get_json()["patient"]["id"]

        # Verify bed is occupied
        stats1 = client.get("/api/stats").get_json()
        assert stats1["occupied"] == 1
        assert stats1["admitted_patients"] == 1

        # Step 3: Patient acuity worsens -> Transfer to ICU (ICU-201)
        icu_bed_id = seeded_db["bed_ids"][2]
        transfer_payload = {
            "to_bed_id": icu_bed_id,
            "reason": "Intubation required - acute respiratory failure"
        }
        transfer_res = client.post(f"/api/patients/{patient_id}/transfer", data=json.dumps(transfer_payload), content_type="application/json")
        assert transfer_res.status_code == 200

        # Verify: EME bed is Cleaning, ICU bed is Occupied
        stats2 = client.get("/api/stats").get_json()
        assert stats2["occupied"] == 1
        assert stats2["cleaning"] == 1
        assert stats2["available"] == 2

        # Step 4: Housekeeping sanitizes EME bed
        clean_res = client.post(f"/api/beds/{assigned_eme_bed}/cleaning/complete")
        assert clean_res.status_code == 200

        stats3 = client.get("/api/stats").get_json()
        assert stats3["cleaning"] == 0
        assert stats3["available"] == 3

        # Step 5: Patient recovers and is discharged from ICU
        discharge_res = client.post(f"/api/patients/{patient_id}/discharge")
        assert discharge_res.status_code == 200

        stats4 = client.get("/api/stats").get_json()
        assert stats4["occupied"] == 0
        assert stats4["cleaning"] == 1
        assert stats4["admitted_patients"] == 0

        # Step 6: Housekeeping sanitizes ICU bed
        clean_icu_res = client.post(f"/api/beds/{icu_bed_id}/cleaning/complete")
        assert clean_icu_res.status_code == 200

        # Step 7: Final state verification
        stats_final = client.get("/api/stats").get_json()
        assert stats_final["total"] == 4
        assert stats_final["available"] == 4
        assert stats_final["occupied"] == 0
        assert stats_final["cleaning"] == 0
        assert stats_final["occupancy_rate"] == 0.0

        # Verify audit trails
        transfers = client.get("/api/transfers").get_json()
        assert len(transfers) == 1
        assert transfers[0]["patient_name"] == "Vikram Seth"

        # Verify patient record reflects Discharged
        patients = client.get("/api/patients?status=Discharged").get_json()
        assert len(patients) == 1
        assert patients[0]["name"] == "Vikram Seth"
        assert patients[0]["status"] == "Discharged"
