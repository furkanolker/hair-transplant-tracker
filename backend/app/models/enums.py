from enum import Enum


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    VIEWER = "VIEWER"


class TransplantType(str, Enum):
    HAIR = "HAIR"
    BEARD = "BEARD"
    EYEBROW = "EYEBROW"
    HAIR_BEARD = "HAIR_BEARD"
    HAIR_EYEBROW = "HAIR_EYEBROW"
    HAIR_BEARD_EYEBROW = "HAIR_BEARD_EYEBROW"


class PersonnelRole(str, Enum):
    HARVESTER = "HARVESTER"
    PLANTER = "PLANTER"
    DHI_TECHNICIAN = "DHI_TECHNICIAN"
    HARVESTER_DHI = "HARVESTER_DHI"
