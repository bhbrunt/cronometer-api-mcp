"""Product barcode (EAN, UPC and GTIN) validation for custom foods."""

import re


def normalize_barcodes(barcodes: list[str]) -> list[str]:
    """Validate product barcodes and return them as bare digit strings.

    Accepts the GTIN family the app's scanner reads -- EAN-13, UPC-A (12),
    EAN-8 or UPC-E (8) and GTIN-14 -- including the spaces or dashes the
    digits are printed with under the bars ("0 12345 67890 5"). The check
    digit is verified, so a digit misread off a label is rejected instead of
    saved as a code that never scans. Duplicates are dropped. Bare digit
    strings are what get_food reports for branded foods (["602652270284"]).
    """
    normalized: list[str] = []
    for raw in barcodes:
        code = re.sub(r"[\s-]", "", str(raw))
        if not (code.isascii() and code.isdigit()) or len(code) not in (8, 12, 13, 14):
            raise ValueError(
                f"barcode {raw!r} must be 8, 12, 13 or 14 digits (EAN, UPC or GTIN)"
            )
        if not _has_valid_check_digit(code):
            raise ValueError(
                f"barcode {raw!r} has the wrong check digit (last digit); "
                f"re-check the digits"
            )
        if code not in normalized:
            normalized.append(code)
    return normalized


def _gtin_check_digit(body: str) -> int:
    """GS1 check digit for `body`: weights 3, 1, 3, ... from the right."""
    total = sum(int(d) * (1 if i % 2 else 3) for i, d in enumerate(reversed(body)))
    return -total % 10


def _has_valid_check_digit(code: str) -> bool:
    if _gtin_check_digit(code[:-1]) == int(code[-1]):
        return True
    # An 8-digit code that isn't a valid EAN-8 can still be UPC-E, whose check
    # digit is the one of the 12-digit UPC-A it abbreviates.
    return (
        len(code) == 8
        and code[0] in "01"
        and _gtin_check_digit(_expand_upc_e(code)) == int(code[-1])
    )


def _expand_upc_e(code: str) -> str:
    """The UPC-A digits (check digit excluded) a UPC-E code abbreviates."""
    system, d = code[0], code[1:7]
    if d[5] in "012":
        return system + d[0:2] + d[5] + "0000" + d[2:5]
    if d[5] == "3":
        return system + d[0:3] + "00000" + d[3:5]
    if d[5] == "4":
        return system + d[0:4] + "00000" + d[4]
    return system + d[0:5] + "0000" + d[5]
