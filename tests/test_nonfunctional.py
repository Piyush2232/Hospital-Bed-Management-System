import pytest
import time
import json

class TestNonFunctional:
    """Level 4: Non-Functional Testing (Performance / Latency, Security, Edge Cases)."""

    def test_nfr1_stats_latency_benchmark(self, client, seeded_db):
        """NFR-1 specifies /api/stats and /api/wards must respond in under 300ms."""
        times = []
        for _ in range(10):
            start = time.perf_counter()
            res = client.get("/api/stats")
            duration_ms = (time.perf_counter() - start) * 1000
            assert res.status_code == 200
            times.append(duration_ms)

        avg_latency = sum(times) / len(times)
        max_latency = max(times)
        assert avg_latency < 300.0, f"Average latency {avg_latency:.2f}ms exceeded 300ms threshold"
        assert max_latency < 300.0, f"Peak latency {max_latency:.2f}ms exceeded 300ms threshold"

    def test_nfr2_admission_transaction_latency(self, client, seeded_db):
        """NFR-2 specifies transactions like admission must commit in under 500ms."""
        bed_id = seeded_db["bed_ids"][0]
        payload = {
            "name": "Benchmark Patient",
            "age": 35,
            "gender": "Male",
            "bed_id": bed_id
        }
        start = time.perf_counter()
        res = client.post("/api/patients/admit", data=json.dumps(payload), content_type="application/json")
        duration_ms = (time.perf_counter() - start) * 1000
        assert res.status_code == 201
        assert duration_ms < 500.0, f"Transaction latency {duration_ms:.2f}ms exceeded 500ms threshold"

    def test_security_sql_injection_resilience(self, client, seeded_db):
        """NFR-4: Verify SQL injection payloads are safely parameterized and sanitized."""
        bed_id = seeded_db["bed_ids"][1]
        sqli_payload = {
            "name": "Robert'); DROP TABLE patients;--",
            "age": 42,
            "gender": "Male",
            "medical_condition": "' OR 1=1;--",
            "bed_id": bed_id
        }
        res = client.post("/api/patients/admit", data=json.dumps(sqli_payload), content_type="application/json")
        assert res.status_code == 201

        # Verify tables intact and name saved verbatim without executing arbitrary SQL
        patients = client.get("/api/patients").get_json()
        assert any(p["name"] == "Robert'); DROP TABLE patients;--" for p in patients)

        stats = client.get("/api/stats")
        assert stats.status_code == 200

    def test_security_xss_payload_safety(self, client, seeded_db):
        """NFR-5: Verify Cross-Site Scripting (XSS) script tags do not compromise data tier."""
        bed_id = seeded_db["bed_ids"][2]
        xss_payload = {
            "name": "<script>alert('XSS')</script>",
            "age": 25,
            "gender": "Female",
            "medical_condition": "<img src=x onerror=alert(1)>",
            "bed_id": bed_id
        }
        res = client.post("/api/patients/admit", data=json.dumps(xss_payload), content_type="application/json")
        assert res.status_code == 201
        patients = client.get("/api/patients").get_json()
        saved = next(p for p in patients if "<script>" in p["name"])
        assert saved["medical_condition"] == "<img src=x onerror=alert(1)>"

    def test_edge_case_zero_and_boundary_age(self, client, seeded_db):
        """Boundary test: Neonatal patient (age 0) and geriatric patient (age 115)."""
        bed_id1 = seeded_db["bed_ids"][0]
        bed_id2 = seeded_db["bed_ids"][3]

        p_infant = {"name": "Baby Doe", "age": 0, "gender": "Female", "bed_id": bed_id1}
        res1 = client.post("/api/patients/admit", data=json.dumps(p_infant), content_type="application/json")
        assert res1.status_code == 201

        p_geriatric = {"name": "Elder Doe", "age": 115, "gender": "Male", "bed_id": bed_id2}
        res2 = client.post("/api/patients/admit", data=json.dumps(p_geriatric), content_type="application/json")
        assert res2.status_code == 201
