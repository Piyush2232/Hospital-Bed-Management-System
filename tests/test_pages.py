def test_page_routes_render(client):
    r1 = client.get("/")
    assert r1.status_code == 200
    assert b"Dashboard" in r1.data or b"BED.MGR" in r1.data

    r2 = client.get("/admit")
    assert r2.status_code == 200
    assert b"Admit Patient" in r2.data or b"ADMIT" in r2.data

    r3 = client.get("/patients")
    assert r3.status_code == 200
    assert b"Patients" in r3.data or b"PATIENTS" in r3.data
