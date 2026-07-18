from typing import Any


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