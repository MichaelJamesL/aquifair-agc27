from neraca.repositories.english import english


def test_names_and_terms_become_english() -> None:
    row = {
        "id": "3374",
        "name": "Kota Semarang",
        "regency": "Kab. Demak",
        "district": "Kaliwungu Selatan",
        "note": "Filter 4 uses kecamatan piped coverage until PDAM releases coverage per kelurahan "
        "(Pergub Jateng 7/2025).",
        "source_ids": ["PERDA-SMG-2024"],
    }
    assert english(row) == {
        "id": "3374",
        "name": "Semarang City",
        "regency": "Demak Regency",
        "district": "South Kaliwungu",
        "note": "Filter 4 uses district piped coverage until PDAM releases coverage per village "
        "(Central Java Governor Regulation 7/2025).",
        "source_ids": ["PERDA-SMG-2024"],
    }


def test_one_word_names_stay() -> None:
    assert english("Karang Tengah") == "Karang Tengah"
    assert english({"type": "kota", "wilayah": "A"}) == {"type": "kota", "wilayah": "A"}
