"""Tests for barcode validation of custom foods.

normalize_barcodes accepts the GTIN family (EAN-13, UPC-A, EAN-8, UPC-E,
GTIN-14), strips the spaces and dashes codes are printed with, and verifies
the GS1 check digit so a misread digit is rejected rather than saved.
"""

from __future__ import annotations

import pytest

from cronometer_api_mcp.barcode import normalize_barcodes


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("4006381333931", "4006381333931"),  # EAN-13
        ("602652270284", "602652270284"),  # UPC-A (from a real get_food)
        ("0 49000 05010 3", "049000050103"),  # UPC-A as printed on a label
        ("9638-5074", "96385074"),  # EAN-8
        # UPC-E, one per expansion rule (the sixth digit picks it). The first
        # three aren't valid EAN-8s, so only the UPC-E check accepts them;
        # under rule 5-9 the two check digits always coincide.
        ("04252614", "04252614"),  # -> UPC-A 042100005264
        ("01234531", "01234531"),  # -> UPC-A 012300000451
        ("01234543", "01234543"),  # -> UPC-A 012340000053
        ("01234565", "01234565"),  # -> UPC-A 012345000065
        ("10012345678902", "10012345678902"),  # GTIN-14
    ],
)
def test_normalize_barcodes_accepts_gtin_family(raw, expected):
    assert normalize_barcodes([raw]) == [expected]


@pytest.mark.parametrize(
    "raw",
    [
        "4006381333932",  # EAN-13, last digit off by one
        "602652270285",  # UPC-A, wrong check digit
        "04252615",  # neither a valid EAN-8 nor a valid UPC-E
        "24252618",  # UPC-E check digit, but UPC-E only has number systems 0, 1
        "01234566",  # rule 5-9: wrong check digit as EAN-8 and as UPC-E
    ],
)
def test_normalize_barcodes_rejects_wrong_check_digit(raw):
    with pytest.raises(ValueError, match="check digit"):
        normalize_barcodes([raw])


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "12345",  # no GTIN has 5 digits
        "400638133393a",
        "４００６３８１３３３９３１",  # full-width digits: isdigit() but not ASCII
    ],
)
def test_normalize_barcodes_rejects_malformed(raw):
    with pytest.raises(ValueError, match="must be 8, 12, 13 or 14 digits"):
        normalize_barcodes([raw])


def test_normalize_barcodes_drops_duplicates():
    assert normalize_barcodes(["4006381333931", "4006 3813 3393 1"]) == [
        "4006381333931"
    ]
