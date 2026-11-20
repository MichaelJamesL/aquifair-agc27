from __future__ import annotations

from enum import StrEnum


class ProvenanceLabel(StrEnum):
    """What backs a number. The seven labels used throughout the NERACA report."""

    OFFICIAL = "OFFICIAL"
    MEASURED = "MEASURED"
    TESTED = "TESTED"
    CALCULATED = "CALCULATED"
    WEAK = "WEAK"
    SCENARIO = "SCENARIO"
    MISSING = "MISSING"


class Role(StrEnum):
    """Role selected in the UI dropdown. No login and no real authentication."""

    PUBLIC = "public"
    REGULATOR = "regulator"
    INSPECTOR = "inspector"
    PLANNER = "planner"


class LeadOutcome(StrEnum):
    REGISTERED_WELL = "registered_well"
    UNREGISTERED_WELL = "unregistered_well"
    NO_WELL = "no_well"
    PDAM_CUSTOMER = "pdam_customer"


class ZoneClass(StrEnum):
    SAFE = "safe"
    VULNERABLE = "vulnerable"
    CRITICAL = "critical"
    DAMAGED = "damaged"


class UseClass(StrEnum):
    FACTORY = "factory"
    HOTEL = "hotel"
    MALL = "mall"
    HOSPITAL = "hospital"
    OTHER = "other"
    WAREHOUSE = "warehouse"
    # No class in OSM or Overture places: listed for a site check, not counted as a lead.
    UNKNOWN = "unknown"


class LeadStage(StrEnum):
    """A step of the method M3 funnel: the candidates that pass filters 1 to N, or the unknown-class site checks."""

    NEW_ROOF = "1"
    WATER_CLASS = "1-2"
    CLOSED_ZONE = "1-3"
    LEAD = "1-4"
    UNKNOWN = "unknown"


class CheckStatus(StrEnum):
    DONE = "done"
    PLANNED = "planned"
    WAITING = "waiting"
    NOT_RUN = "not_run"


class CheckResult(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    WAITING = "waiting"
    NOT_APPLICABLE = "not_applicable"


class PipeTestStatus(StrEnum):
    NOT_RUN = "not_run"
    PASS = "pass"
    FAIL = "fail"
    INCONCLUSIVE = "inconclusive"


class QualityClass(StrEnum):
    GOOD = "good"
    POOR = "poor"


class AlternativeSource(StrEnum):
    PRESENT = "present"
    ABSENT = "absent"


class RegionType(StrEnum):
    KABUPATEN = "kabupaten"
    KOTA = "kota"
