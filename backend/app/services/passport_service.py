import base64


def encrypt_passport(passport: str | None) -> str | None:
    if not passport:
        return None
    return base64.b64encode(passport.encode("utf-8")).decode("utf-8")


def decrypt_passport(encoded: str | None) -> str | None:
    if not encoded:
        return None
    return base64.b64decode(encoded.encode("utf-8")).decode("utf-8")


def mask_passport(passport: str | None) -> str | None:
    if not passport:
        return None
    if len(passport) <= 4:
        return "*" * len(passport)
    return "*" * (len(passport) - 4) + passport[-4:]
