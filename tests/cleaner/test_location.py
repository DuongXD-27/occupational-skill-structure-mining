"""
tests/cleaner/test_location.py
QR-02 location normalization tests.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pytest
from cleaner.location import normalize_location


class TestNormalizeLocation:
    # ── Standard recognized cities ──────────────────────────────────────────
    def test_hanoi_standard(self):
        loc, flags = normalize_location("Hà Nội")
        assert loc == "Hà Nội"
        assert flags == []

    def test_hanoi_unaccented(self):
        loc, flags = normalize_location("Ha Noi")
        assert loc == "Hà Nội"

    def test_hanoi_abbreviation(self):
        loc, flags = normalize_location("HN")
        assert loc == "Hà Nội"

    def test_hcm_standard(self):
        loc, flags = normalize_location("Hồ Chí Minh")
        assert loc == "Hồ Chí Minh"

    def test_hcm_abbreviation(self):
        loc, flags = normalize_location("HCM")
        assert loc == "Hồ Chí Minh"

    def test_hcm_sai_gon(self):
        loc, flags = normalize_location("Sài Gòn")
        assert loc == "Hồ Chí Minh"

    def test_hcm_tp_hcm(self):
        loc, flags = normalize_location("TP.HCM")
        assert loc == "Hồ Chí Minh"

    def test_danang(self):
        loc, flags = normalize_location("Đà Nẵng")
        assert loc == "Đà Nẵng"

    # ── Location with many writing styles ───────────────────────────────────
    def test_hanoi_uppercase(self):
        loc, flags = normalize_location("HANOI")
        assert loc == "Hà Nội"

    def test_hcm_hcmc(self):
        loc, flags = normalize_location("HCMC")
        assert loc == "Hồ Chí Minh"

    def test_hcm_ho_chi_minh_city(self):
        loc, flags = normalize_location("Ho Chi Minh City")
        assert loc == "Hồ Chí Minh"

    # ── Remote ──────────────────────────────────────────────────────────────
    def test_remote_english(self):
        loc, flags = normalize_location("Remote")
        assert loc == "Remote"

    def test_remote_wfh(self):
        loc, flags = normalize_location("WFH")
        assert loc == "Remote"

    def test_remote_work_from_home(self):
        loc, flags = normalize_location("Work from home")
        assert loc == "Remote"

    # ── District-only names ─────────────────────────────────────────────────
    def test_district_quan_1(self):
        loc, flags = normalize_location("Quận 1")
        assert loc == "Hồ Chí Minh"

    def test_district_thanh_xuan(self):
        loc, flags = normalize_location("Quận Thanh Xuân")
        assert loc == "Hà Nội"

    def test_district_cau_giay(self):
        loc, flags = normalize_location("Quận Cầu Giấy")
        assert loc == "Hà Nội"

    def test_district_thu_duc(self):
        loc, flags = normalize_location("Thành phố Thủ Đức")
        assert loc == "Hồ Chí Minh"

    # ── Multi-region ─────────────────────────────────────────────────────────
    def test_multi_region_comma(self):
        loc, flags = normalize_location("Quận 1, Quận Đống Đa")
        assert loc == "Nhiều địa điểm"
        assert "MULTI_LOCATION" in flags

    def test_multi_region_with_na(self):
        loc, flags = normalize_location("Quận Phú Nhuận, Not Available")
        assert loc == "Hồ Chí Minh"
        assert "MISSING_LOCATION" in flags

    def test_both_na(self):
        loc, flags = normalize_location("Not Available, Not Available")
        assert loc is None
        assert "MISSING_LOCATION" in flags

    # ── Placeholder / null ───────────────────────────────────────────────────
    def test_not_available(self):
        loc, flags = normalize_location("Not Available")
        assert loc is None
        assert "MISSING_LOCATION" in flags

    def test_null_input(self):
        loc, flags = normalize_location(None)
        assert loc is None
        assert "MISSING_LOCATION" in flags

    def test_empty_string(self):
        loc, flags = normalize_location("")
        assert loc is None

    # ── Unrecognized ─────────────────────────────────────────────────────────
    def test_unrecognized(self):
        loc, flags = normalize_location("Outer Space")
        assert loc is None
        assert "LOCATION_UNRECOGNIZED" in flags
