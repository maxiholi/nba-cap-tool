from typing import Literal, TypedDict


class MinimumSalaryScaleRow(TypedDict):
    season: str
    years_of_service_min: int
    years_of_service_max: int | None
    base_salary: int
    standard_cap_charge: int


class MinimumSigningResult(TypedDict):
    rule_id: str
    rule_name: str
    status: Literal["allowed", "not_allowed"]
    allowed: bool
    season: str
    years_of_service: int
    contract_years: int
    base_salary: int | None
    cap_hit: int | None
    explanation: str


def service_range_matches(
    years_of_service: int,
    row: MinimumSalaryScaleRow,
) -> bool:
    minimum = row["years_of_service_min"]
    maximum = row["years_of_service_max"]

    if years_of_service < minimum:
        return False

    if maximum is not None and years_of_service > maximum:
        return False

    return True


def evaluate_minimum_signing(
    *,
    season: str,
    years_of_service: int,
    contract_years: int,
    scale_rows: list[MinimumSalaryScaleRow],
) -> MinimumSigningResult:
    if years_of_service < 0:
        raise ValueError("Years of service cannot be negative")

    if contract_years not in (1, 2):
        return {
            "rule_id": "MINIMUM_SALARY_EXCEPTION",
            "rule_name": "Minimum Salary Exception",
            "status": "not_allowed",
            "allowed": False,
            "season": season,
            "years_of_service": years_of_service,
            "contract_years": contract_years,
            "base_salary": None,
            "cap_hit": None,
            "explanation": (
                "The Minimum Salary Exception may only be used "
                "for a one-year or two-year contract."
            ),
        }

    matching_row = next(
        (
            row
            for row in scale_rows
            if row["season"] == season
            and service_range_matches(years_of_service, row)
        ),
        None,
    )

    if matching_row is None:
        return {
            "rule_id": "MINIMUM_SALARY_EXCEPTION",
            "rule_name": "Minimum Salary Exception",
            "status": "not_allowed",
            "allowed": False,
            "season": season,
            "years_of_service": years_of_service,
            "contract_years": contract_years,
            "base_salary": None,
            "cap_hit": None,
            "explanation": (
                f"No minimum-salary scale entry exists for "
                f"{years_of_service} years of service in {season}."
            ),
        }

    return {
        "rule_id": "MINIMUM_SALARY_EXCEPTION",
        "rule_name": "Minimum Salary Exception",
        "status": "allowed",
        "allowed": True,
        "season": season,
        "years_of_service": years_of_service,
        "contract_years": contract_years,
        "base_salary": matching_row["base_salary"],
        "cap_hit": matching_row["standard_cap_charge"],
        "explanation": (
            f"A player with {years_of_service} years of service "
            f"may sign this {contract_years}-year minimum contract. "
            f"The player salary is ${matching_row['base_salary']:,}, "
            f"and the stored team cap charge is "
            f"${matching_row['standard_cap_charge']:,}."
        ),
    }