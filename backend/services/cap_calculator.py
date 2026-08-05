from typing import Any, Literal, TypedDict, Union

class RuleResult(TypedDict):
    rule_id: str
    rule_name: str
    status: Literal["allowed", "not_allowed", "requires_exception"]
    allowed: bool
    explanation: str
    values: dict[str, int | bool]

def calculate_payroll_position(
    current_cap_hit: int,
    added_cap_hit: int,
    salary_cap: int,
    luxury_tax: int,
    first_apron: int,
    second_apron: int,
) -> dict[str, Any]:
    if added_cap_hit < 0:
        raise ValueError("Added cap hit cannot be negative")

    projected_cap_hit = current_cap_hit + added_cap_hit

    return {
        "current_cap_hit": current_cap_hit,
        "added_cap_hit": added_cap_hit,
        "projected_cap_hit": projected_cap_hit,
        "salary_cap_balance": salary_cap - projected_cap_hit,
        "tax_room": luxury_tax - projected_cap_hit,
        "first_apron_room": first_apron - projected_cap_hit,
        "second_apron_room": second_apron - projected_cap_hit,
        "over_salary_cap": projected_cap_hit > salary_cap,
        "over_luxury_tax": projected_cap_hit > luxury_tax,
        "over_first_apron": projected_cap_hit > first_apron,
        "over_second_apron": projected_cap_hit > second_apron,
    }

def evaluate_cap_room_signing(
    current_cap_hit: int,
    proposed_cap_hit: int,
    salary_cap: int,
) -> RuleResult:
    if current_cap_hit < 0:
        raise ValueError("Current cap hit cannot be negative")

    if proposed_cap_hit <= 0:
        raise ValueError("Proposed cap hit must be positive")

    available_cap_room = salary_cap - current_cap_hit
    projected_cap_hit = current_cap_hit + proposed_cap_hit

    if proposed_cap_hit <= available_cap_room:
        return {
            "rule_id": "CAP_ROOM_SIGNING",
            "rule_name": "Signing using salary-cap room",
            "status": "allowed",
            "allowed": True,
            "explanation": (
                f"The team has ${available_cap_room:,} in cap room, "
                f"which is enough for the proposed ${proposed_cap_hit:,} cap hit."
            ),
            "values": {
                "current_cap_hit": current_cap_hit,
                "salary_cap": salary_cap,
                "available_cap_room": available_cap_room,
                "proposed_cap_hit": proposed_cap_hit,
                "projected_cap_hit": projected_cap_hit,
            },
        }

    if available_cap_room <= 0:
        return {
            "rule_id": "CAP_ROOM_SIGNING",
            "rule_name": "Signing using salary-cap room",
            "status": "requires_exception",
            "allowed": False,
            "explanation": (
                f"The team is already ${abs(available_cap_room):,} "
                "above the salary cap and cannot use ordinary cap room. "
                "Another signing mechanism or exception would be required."
            ),
            "values": {
                "current_cap_hit": current_cap_hit,
                "salary_cap": salary_cap,
                "available_cap_room": available_cap_room,
                "proposed_cap_hit": proposed_cap_hit,
                "projected_cap_hit": projected_cap_hit,
            },
        }

    shortfall = proposed_cap_hit - available_cap_room

    return {
        "rule_id": "CAP_ROOM_SIGNING",
        "rule_name": "Signing using salary-cap room",
        "status": "requires_exception",
        "allowed": False,
        "explanation": (
            f"The team has ${available_cap_room:,} in cap room, "
            f"which is ${shortfall:,} less than the proposed cap hit. "
            "Another signing mechanism or exception would be required."
        ),
        "values": {
            "current_cap_hit": current_cap_hit,
            "salary_cap": salary_cap,
            "available_cap_room": available_cap_room,
            "proposed_cap_hit": proposed_cap_hit,
            "projected_cap_hit": projected_cap_hit,
        },
    }