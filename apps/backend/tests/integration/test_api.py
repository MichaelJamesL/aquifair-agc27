from __future__ import annotations

from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["regions"] == 35
    assert body["sources"] >= 30
    assert body["years"] == [2020, 2021, 2022, 2023]


def test_accounts_for_all_regions(client: TestClient) -> None:
    response = client.get("/api/v1/accounts", params={"year": 2023})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 35
    semarang = next(item for item in body if item["region"]["id"] == "3374")
    assert semarang["declared"]["value"] == 10_069_814
    assert semarang["declared"]["label"] == "OFFICIAL"
    assert semarang["estimated_validated"]["label"] == "TESTED"
    assert semarang["gap"]["low"] < 0 < semarang["gap"]["high"]
    assert semarang["estimate_method"] == "validated_16km_split"
    others = [item for item in body if item["region"]["id"] != "3374"]
    assert all(item["estimate_method"] == "regency_model" for item in others)
    assert all(item["estimate"]["label"] == "CALCULATED" and item["gap"]["low"] >= 0 for item in others)


def test_account_history(client: TestClient) -> None:
    response = client.get("/api/v1/accounts/3374/history")
    assert response.status_code == 200
    body = response.json()
    assert [point["year"] for point in body] == [2020, 2021, 2022, 2023]
    assert body[-1]["declared"]["value"] == 10_069_814


def test_account_unknown_region_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/accounts/9999")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_scenario(client: TestClient) -> None:
    response = client.get("/api/v1/accounts/3374/scenario", params={"undeclared_m3": 5_000_000})
    assert response.status_code == 200
    body = response.json()
    assert body["tax"]["low"] == 44_269_000_000
    assert body["tax"]["high"] == 67_143_000_000
    assert body["tax"]["label"] == "CALCULATED"


def test_billing_check_runs_on_kota_semarang(client: TestClient) -> None:
    response = client.get("/api/v1/accounts/3374/billing-check")
    assert response.status_code == 200
    body = response.json()
    assert body["check"] == {"code": "V1", "status": "done", "result": "pass"}
    assert body["year"] == 2023
    assert body["realised_tax"]["value"] == 22_609_911_448
    assert body["implied_tax_per_m3"]["value"] == 2245
    assert (body["expected_band"]["low"], body["expected_band"]["high"]) == (2100, 2480)
    by_year = {row["year"]: row for row in body["history"]}
    assert by_year[2022]["implied_tax_per_m3"]["value"] == 2188
    assert by_year[2024]["result"] == "waiting"  # no 2024 declared volume yet


def test_billing_check_without_realised_tax_is_planned(client: TestClient) -> None:
    body = client.get("/api/v1/accounts/3301/billing-check").json()
    assert body["check"]["status"] == "planned"
    assert body["realised_tax"]["label"] == "MISSING"


def test_leads_reject_public_role(client: TestClient) -> None:
    response = client.get("/api/v1/leads")
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ROLE_FORBIDDEN"


def test_leads_pass_all_four_filters(client: TestClient) -> None:
    response = client.get("/api/v1/leads", params={"role": "inspector"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "available"
    assert body["items"]
    steps = {step["step"]: step["count"] for step in body["funnel"]}
    assert len(body["items"]) == steps["1-4"]
    for lead in body["items"]:
        assert lead["zone"] in {"critical", "damaged"}
        assert lead["use_class"] in {"factory", "hotel", "mall", "hospital"}
        assert lead["footprint_m2"] >= 1000
        if lead["use_class"] == "factory":
            assert lead["filters"]["4"] is None  # filter 4 is not applied to factories
        else:
            assert lead["pdam_coverage"] < 0.5


def test_each_funnel_step_lists_its_candidates(client: TestClient) -> None:
    funnel = client.get("/api/v1/leads", params={"role": "inspector"}).json()["funnel"]
    counts = [step["count"] for step in funnel if step["step"] != "unknown"]
    assert counts == sorted(counts, reverse=True)
    for step in funnel:
        items = client.get("/api/v1/leads", params={"role": "inspector", "stage": step["step"]}).json()["items"]
        assert len(items) == step["count"], step["step"]
    unknown = client.get("/api/v1/leads", params={"role": "inspector", "stage": "unknown"}).json()["items"]
    assert all(item["use_class"] == "unknown" and item["zone"] is not None for item in unknown)


def test_public_summary_counts_leads_only(client: TestClient) -> None:
    body = client.get("/api/v1/leads/public/summary").json()
    leads = client.get("/api/v1/leads", params={"role": "inspector"}).json()["items"]
    assert sum(row["leads"] for row in body["items"]) == len(leads)
    assert all("unknown" not in row["by_use_class"] for row in body["items"])


def test_lead_image_is_inspector_only(client: TestClient) -> None:
    lead_id = client.get("/api/v1/leads", params={"role": "inspector"}).json()["items"][0]["id"]
    image = client.get(f"/api/v1/leads/{lead_id}/image/2026", params={"role": "inspector"})
    assert image.status_code == 200
    assert image.headers["content-type"] == "image/png"
    assert client.get(f"/api/v1/leads/{lead_id}/image/2026").status_code == 403
    assert client.get(f"/api/v1/leads/{lead_id}/image/2019", params={"role": "inspector"}).status_code == 404


def test_public_summary_has_no_addresses(client: TestClient) -> None:
    response = client.get("/api/v1/leads/public/summary")
    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    assert all("lon" not in item and "lat" not in item for item in body["items"])


def test_post_feedback_without_lead_returns_404(client: TestClient) -> None:
    response = client.post(
        "/api/v1/leads/NOPE/feedback",
        headers={"X-Role": "inspector"},
        json={
            "inspector": "Rina S.",
            "outcome": "unregistered_well",
            "note": "test",
        },
    )
    assert response.status_code == 404


def test_pipes_spam_test(client: TestClient) -> None:
    response = client.get("/api/v1/pipes/spam-test")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "not_run"
    assert "has not been run" in body["outcome_wording"]


def test_pipes_priority_ranks_real_blocks(client: TestClient) -> None:
    response = client.get("/api/v1/pipes/priority", params={"w_demand": 1, "w_damage": 0, "w_supply": 0})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "available"
    assert len(body["items"]) == 22
    demands = [item["cell"]["demand_m3_yr"] for item in body["items"]]
    assert demands == sorted(demands, reverse=True)


def test_map_layers(client: TestClient) -> None:
    zones = client.get("/api/v1/maps/zones").json()
    assert {f["properties"]["zone"] for f in zones["features"]} >= {"critical", "damaged"}
    assert len(client.get("/api/v1/maps/zone-wells").json()["items"]) == 467
    coverage = client.get("/api/v1/maps/pdam-coverage").json()["items"]
    assert all(0 <= row["coverage"] <= 1 for row in coverage)


def test_tariff_table(client: TestClient) -> None:
    response = client.get("/api/v1/tariffs", params={"wilayah": "C"})
    assert response.status_code == 200
    body = response.json()
    assert len(body["rows"]) == 25
    first = body["rows"][0]
    assert first["group_name"] == "K1"
    assert first["tier_key"] == "0_50"
    assert first["npa_idr"]["value"] == 37_277
    assert first["npa_idr"]["label"] == "OFFICIAL"
    top_k2 = next(row for row in body["rows"] if row["group_name"] == "K2" and row["tier_key"] == "over_2500")
    assert top_k2["npa_idr"]["value"] == 67_143
    assert top_k2["tax_idr"]["value"] == 13_429


def test_sources_and_validation(client: TestClient) -> None:
    sources = client.get("/api/v1/sources").json()
    assert len(sources) >= 30
    assert any(source["id"] == "ESDM-NPA-2023" for source in sources)

    checks = client.get("/api/v1/validation").json()
    assert len(checks) == 8
    v2 = next(check for check in checks if check["code"] == "V2")
    assert v2["result"] == "pass"


def test_regions_and_geojson(client: TestClient) -> None:
    regions = client.get("/api/v1/regions").json()
    assert len(regions) == 35

    geometry = client.get("/api/v1/regions/geojson").json()
    assert geometry["type"] == "FeatureCollection"
    assert len(geometry["features"]) == 35
    ids = {feature["properties"]["region_id"] for feature in geometry["features"]}
    assert "3374" in ids


def test_meta(client: TestClient) -> None:
    body = client.get("/api/v1/meta/config").json()
    labels = {item["label"] for item in body["labels"]}
    assert labels == {
        "OFFICIAL",
        "MEASURED",
        "TESTED",
        "CALCULATED",
        "WEAK",
        "SCENARIO",
        "MISSING",
    }
    roles = {item["role"] for item in body["roles"]}
    assert roles == {"public", "regulator", "inspector", "planner"}
