from decimal import Decimal

from app.models.enums import TransplantType

DEFAULT_MULTIPLIER_BY_TYPE: dict[TransplantType, Decimal] = {
    TransplantType.BEARD: Decimal("0.5"),
    TransplantType.EYEBROW: Decimal("0.5"),
    TransplantType.HAIR: Decimal("1.0"),
    TransplantType.HAIR_BEARD: Decimal("1.0"),
    TransplantType.HAIR_EYEBROW: Decimal("1.0"),
    TransplantType.HAIR_BEARD_EYEBROW: Decimal("1.0"),
}

VALID_MULTIPLIERS = {Decimal("0.5"), Decimal("1.0")}


def get_default_multiplier(transplant_type: TransplantType) -> Decimal:
    return DEFAULT_MULTIPLIER_BY_TYPE[transplant_type]


def validate_multiplier(multiplier: Decimal) -> None:
    if multiplier not in VALID_MULTIPLIERS:
        raise ValueError("Multiplier must be 0.5 or 1.0")
