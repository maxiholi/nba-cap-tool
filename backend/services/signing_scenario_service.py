from enum import Enum
from typing import Any

from services.cap_calculator import (
    calculate_payroll_position,
    evaluate_cap_room_signing,
)
from services.minimum_salary_service import (
    MinimumSalaryScaleRow,
    evaluate_minimum_signing,
)


class SigningMechanism(str, Enum):
    AUTO = "auto"
    CAP_ROOM = "cap_room"
    VETERAN_MINIMUM = "veteran_minimum"
    MID_LEVEL_EXCEPTION = "mid_level_exception"
    BI_ANNUAL_EXCEPTION = "bi_annual_exception"
    BIRD_RIGHTS = "bird_rights"


class SigningScenarioError(Exception):
    status_code: int
    detail: str

    def __init__(self, detail: str, status_code: int) -> None:
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


def run_signing_scenario(
    *,
    team: dict[str, Any],
    cap: dict[str, Any],
    current_cap_hit: int,
    player_name: str,
    season: str,
    mechanism: SigningMechanism,
    cap_hit: int | None,
    years_of_service: int | None,
    contract_years: int | None,
    minimum_scale_rows: list[MinimumSalaryScaleRow],
) -> dict[str, Any]:
    minimum_rule = None

    if mechanism == SigningMechanism.VETERAN_MINIMUM:
        if years_of_service is None:
            raise SigningScenarioError(
                "years_of_service is required for veteran minimum",
                status_code=422,
            )

        if contract_years is None:
            raise SigningScenarioError(
                "contract_years is required for veteran minimum",
                status_code=422,
            )

        minimum_rule = evaluate_minimum_signing(
            season=season,
            years_of_service=years_of_service,
            contract_years=contract_years,
            scale_rows=minimum_scale_rows,
        )

        if not minimum_rule["allowed"]:
            return {
                "team": team,
                "season": season,
                "proposed_player": {
                    "name": player_name,
                    "mechanism": mechanism.value,
                },
                "calculation": None,
                "legal_analysis": {
                    "overall_status": "not_allowed",
                    "rules": [minimum_rule],
                },
            }

        added_cap_hit = minimum_rule["cap_hit"]

        if added_cap_hit is None:
            raise SigningScenarioError(
                "Minimum signing produced no cap hit",
                status_code=500,
            )

    elif mechanism in (
        SigningMechanism.AUTO,
        SigningMechanism.CAP_ROOM,
    ):
        if cap_hit is None:
            raise SigningScenarioError(
                "cap_hit is required for this signing mechanism",
                status_code=422,
            )

        added_cap_hit = cap_hit

    else:
        raise SigningScenarioError(
            f"{mechanism.value} is not implemented yet",
            status_code=501,
        )

    calculation = calculate_payroll_position(
        current_cap_hit=current_cap_hit,
        added_cap_hit=added_cap_hit,
        salary_cap=cap["salary_cap"],
        luxury_tax=cap["luxury_tax"],
        first_apron=cap["first_apron"],
        second_apron=cap["second_apron"],
    )

    cap_room_rule = evaluate_cap_room_signing(
        current_cap_hit=current_cap_hit,
        proposed_cap_hit=added_cap_hit,
        salary_cap=cap["salary_cap"],
    )

    rules: list[Any] = []
    if minimum_rule is not None:
        rules.append(minimum_rule)
    rules.append(cap_room_rule)

    return {
        "team": team,
        "season": season,
        "proposed_player": {
            "name": player_name,
            "cap_hit": added_cap_hit,
        },
        "calculation": calculation,
        "legal_analysis": {
            "overall_status": (
                minimum_rule["status"]
                if minimum_rule
                else "payroll_impact_only"
            ),
            "rules": rules,
            "disclaimer": (
                "Only the selected signing mechanism has been evaluated. "
                "Other CBA restrictions may still apply."
            ),
        },
    }
