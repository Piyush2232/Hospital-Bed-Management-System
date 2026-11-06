import pytest
import json

class TestIntegrationAPI:
    """Level 2: Integration Testing of REST endpoints, database transactions, and error status codes."""

    def test_api_stats_initial(self, client, seeded_db):
        res = client.get("/api/stats")
        assert res.status_code == 200
        data = res.get_json()
        assert data["total"] == 4
        assert data["available"] == 4
        assert data["occupied"] == 0
        assert data["cleaning"] == 0
        assert data["maintenance"] == 0
        assert data["occupancy_rate"] == 0.0
        assert data["admitted_patients"] == 0

    def test_api_wards(self, client, seeded_db):
        res = client.get("/api/wards")
        assert res.status_code == 200
        wards = res.get_json()
        assert len(wards) == 3
        emergency_ward = next(w for w in wards if w["name"] == "Emergency Ward")
        assert len(emergency_ward["beds"]) == 2
        assert emergency_ward["beds"][0]["bed_number"] in ["EME-101", "EME-102"]

    def test_api_beds_recommend(self, client, seeded_db):
        # Query specific ventilator bed in ICU
        res = client.get("/api/beds/recommend?ward_type=ICU&bed_type=Ventilator")
        assert res.status_code == 200
        beds = res.get_json()
        assert len(beds) == 1
        assert beds[0]["bed_number"] == "ICU-201"
        assert beds[0]["bed_type"] == "Ventilator"

        # Query oxygen bed in Emergency
        res = client.get("/api/beds/recommend?ward_type=Emergency&bed_type=Oxygen")
        assert res.status_code == 200
        beds = res.get_json()
        assert len(beds) == 1
        assert beds[0]["bed_number"] == "EME-102"

        # Fallback test: query bed_type that doesn't exist in Emergency -> falls back to available in that ward
        res = client.get("/api/beds/recommend?ward_type=Emergency&bed_type=Ventilator")
        assert res.status_code == 200
        beds = res.get_json()
        assert len(beds) == 2

    def test_api_admit_success(self, client, seeded_db):
        bed_id = seeded_db["bed_ids"][0]  # EME-101
        payload = {
            "name": "Piyush Sharma",
            "age": 21,
            "gender": "Male",
            "priority": "Critical",
            "contact": "9998887776",
            "emergency_contact": "8887776665",
            "medical_condition": "Cardiac arrest observation",
            "bed_id": bed_id,
            "notes": "Admitted directly via ambulance"
        }
        res = client.post("/api/patients/admit", data=json.dumps(payload), content_type="application/json")
        assert res.status_code == 201
        data = res.get_json()
        assert "admitted to bed EME-101" in data["message"]
        assert data["patient"]["name"] == "Piyush Sharma"

        # Verify stats updated
        stats = client.get("/api/stats").get_json()
        assert stats["occupied"] == 1
        assert stats["available"] == 3
        assert stats["occupancy_rate"] == 25.0
        assert stats["admitted_patients"] == 1

    def test_api_admit_missing_fields(self, client, seeded_db):
        payload = {"name": "Incomplete Patient", "age": 45}
        res = client.post("/api/patients/admit", data=json.dumps(payload), content_type="application/json")
        assert res.status_code == 400
        data = res.get_json()
        assert "is required" in data["error"]

    def test_api_admit_bed_not_found(self, client, seeded_db):
        payload = {
            "name": "Ghost Patient",
            "age": 30,
            "gender": "Male",
            "bed_id": 99999
        }
        res = client.post("/api/patients/admit", data=json.dumps(payload), content_type="application/json")
        assert res.status_code == 404
        assert "Bed not found" in res.get_json()["error"]

    def test_api_admit_bed_conflict(self, client, seeded_db):
        bed_id = seeded_db["bed_ids"][0]  # EME-101
        p1 = {"name": "Patient One", "age": 30, "gender": "Male", "bed_id": bed_id}
        client.post("/api/patients/admit", data=json.dumps(p1), content_type="application/json")

        # Attempt duplicate admission on same occupied bed
        p2 = {"name": "Patient Two", "age": 40, "gender": "Female", "bed_id": bed_id}
        res = client.post("/api/patients/admit", data=json.dumps(p2), content_type="application/json")
        assert res.status_code == 409
        assert "is not available" in res.get_json()["error"]

    def test_api_discharge_flow(self, client, seeded_db):
        bed_id = seeded_db["bed_ids"][1]  # EME-102
        p = {"name": "Patient To Discharge", "age": 55, "gender": "Female", "bed_id": bed_id}
        adm_res = client.post("/api/patients/admit", data=json.dumps(p), content_type="application/json")
        patient_id = adm_res.get_json()["patient"]["id"]

        # Discharge patient
        res = client.post(f"/api/patients/{patient_id}/discharge")
        assert res.status_code == 200
        data = res.get_json()
        assert "discharged" in data["message"]
        assert "sent for cleaning" in data["message"]

        # Verify bed is in Cleaning state
        stats = client.get("/api/stats").get_json()
        assert stats["cleaning"] == 1
        assert stats["occupied"] == 0
        assert stats["available"] == 3

        # Attempting duplicate discharge returns 409
        res2 = client.post(f"/api/patients/{patient_id}/discharge")
        assert res2.status_code == 409

    def test_api_transfer_flow(self, client, seeded_db):
        source_bed_id = seeded_db["bed_ids"][0]  # EME-101
        target_bed_id = seeded_db["bed_ids"][2]  # ICU-201

        p = {"name": "Transfer Candidate", "age": 60, "gender": "Male", "bed_id": source_bed_id}
        adm_res = client.post("/api/patients/admit", data=json.dumps(p), content_type="application/json")
        patient_id = adm_res.get_json()["patient"]["id"]

        # Transfer to ICU
        transfer_payload = {
            "to_bed_id": target_bed_id,
            "reason": "Sudden drop in oxygen saturation"
        }
        res = client.post(f"/api/patients/{patient_id}/transfer", data=json.dumps(transfer_payload), content_type="application/json")
        assert res.status_code == 200
        assert "transferred from EME-101 to ICU-201" in res.get_json()["message"]

        # Verify old bed is Cleaning, new bed is Occupied
        wards = client.get("/api/wards").get_json()
        eme_ward = next(w for w in wards if w["name"] == "Emergency Ward")
        icu_ward = next(w for w in wards if w["name"] == "ICU - Block A")

        b1 = next(b for b in eme_ward["beds"] if b["id"] == source_bed_id)
        b2 = next(b for b in icu_ward["beds"] if b["id"] == target_bed_id)

        assert b1["status"] == "Cleaning"
        assert b2["status"] == "Occupied"

        # Verify TransferLog query
        tlogs = client.get("/api/transfers").get_json()
        assert len(tlogs) == 1
        assert tlogs[0]["patient_name"] == "Transfer Candidate"
        assert tlogs[0]["from_bed"] == "EME-101"
        assert tlogs[0]["to_bed"] == "ICU-201"

    def test_api_cleaning_signoff(self, client, seeded_db):
        bed_id = seeded_db["bed_ids"][3]  # GEN-101
        p = {"name": "Clean Test", "age": 22, "gender": "Male", "bed_id": bed_id}
        adm_res = client.post("/api/patients/admit", data=json.dumps(p), content_type="application/json")
        patient_id = adm_res.get_json()["patient"]["id"]
        client.post(f"/api/patients/{patient_id}/discharge")

        # Mark cleaned
        res = client.post(f"/api/beds/{bed_id}/cleaning/complete")
        assert res.status_code == 200
        assert "cleaned and now available" in res.get_json()["message"]

        # Duplicate clean returns 409
        res_repeat = client.post(f"/api/beds/{bed_id}/cleaning/complete")
        assert res_repeat.status_code == 409

    def test_api_maintenance_toggle(self, client, seeded_db):
        bed_id = seeded_db["bed_ids"][0]  # EME-101

        # Toggle to maintenance
        res1 = client.post(f"/api/beds/{bed_id}/maintenance")
        assert res1.status_code == 200
        assert "marked for maintenance" in res1.get_json()["message"]

        # Bed in maintenance cannot be admitted to
        p = {"name": "Patient Maintenance Test", "age": 33, "gender": "Male", "bed_id": bed_id}
        res_admit = client.post("/api/patients/admit", data=json.dumps(p), content_type="application/json")
        assert res_admit.status_code == 409

        # Toggle out of maintenance
        res2 = client.post(f"/api/beds/{bed_id}/maintenance")
        assert res2.status_code == 200
        assert "taken out of maintenance" in res2.get_json()["message"]

        # Admitting works now
        res_admit_ok = client.post("/api/patients/admit", data=json.dumps(p), content_type="application/json")
        assert res_admit_ok.status_code == 201
