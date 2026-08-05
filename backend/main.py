from pydantic import BaseModel, Field 
from services.cap_calculator import (
    calculate_payroll_position,
    evaluate_cap_room_signing,
)

from services.minimum_salary_service import evaluate_minimum_signing

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from database import supabase

from enum import Enum

app = FastAPI(title="NBA Cap Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SigningMechanism(str, Enum):
    AUTO = "auto"
    CAP_ROOM = "cap_room"
    VETERAN_MINIMUM = "veteran_minimum"
    MID_LEVEL_EXCEPTION = "mid_level_exception"
    BI_ANNUAL_EXCEPTION = "bi_annual_exception"
    BIRD_RIGHTS = "bird_rights"

class SigningScenarioRequest(BaseModel):
    player_name: str = Field(min_length=1, max_length=100)
    season: str = "2026-27"
    mechanism: SigningMechanism = SigningMechanism.AUTO

    cap_hit: int | None = Field(default=None, gt=0)
    years_of_service: int | None = Field(default=None, ge=0)
    contract_years: int | None = Field(default=None, ge=1, le=5)

@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/teams/{team_id}/payroll")
def get_team_payroll(team_id: str, season: str = "2026-27") -> dict[str, Any]:
    team_result = (
        supabase.table("teams")
        .select("id,name,abbreviation")
        .eq("id", team_id)
        .limit(1)
        .execute()
    )

    if not team_result.data:
        raise HTTPException(status_code=404, detail="Team not found")

    cap_result = (
        supabase.table("cap_settings")
        .select(
            "season,salary_cap,luxury_tax,first_apron,second_apron"
        )
        .eq("season", season)
        .limit(1)
        .execute()
    )

    if not cap_result.data:
        raise HTTPException(
            status_code=404,
            detail=f"Cap settings not found for season {season}",
        )

    contracts_result = (
        supabase.table("contracts")
        .select(
            "base_salary,"
            "cap_hit,"
            "guaranteed_amount,"
            "option_type,"
            "contract_type,"
            "age,"
            "players(id,name,position)"
        )
        .eq("team_id", team_id)
        .eq("season", season)
        .execute()
    )

    team = team_result.data[0]
    cap = cap_result.data[0]

    players = []

    for contract in contracts_result.data:
        player = contract["players"]

        players.append(
            {
                "id": player["id"],
                "name": player["name"],
                "position": player["position"],
                "age": contract["age"],
                "contract_type": contract["contract_type"],
                "base_salary": contract["base_salary"],
                "cap_hit": contract["cap_hit"],
                "guaranteed_amount": contract["guaranteed_amount"],
                "option_type": contract["option_type"],
            }
        )

    players.sort(key=lambda player: player["cap_hit"], reverse=True)

    total_cap_hit = sum(player["cap_hit"] for player in players)
    total_base_salary = sum(player["base_salary"] for player in players)

    return {
        "team": team,
        "season": season,
        "players": players,
        "totals": {
            #"team_salary": total_cap_hit,
            "total_cap_hit": total_cap_hit,
            "total_base_salary": total_base_salary,
            "salary_cap": cap["salary_cap"],
            "cap_space": cap["salary_cap"] - total_cap_hit,
            "luxury_tax": cap["luxury_tax"],
            "tax_room": cap["luxury_tax"] - total_cap_hit,
            "first_apron": cap["first_apron"],
            "first_apron_room": cap["first_apron"] - total_cap_hit,
            "second_apron": cap["second_apron"],
            "second_apron_room": cap["second_apron"] - total_cap_hit,
        },
        "is_sample_data": season == "sample",
    }

@app.post("/teams/{team_id}/scenarios/signing")
def simulate_signing(
    team_id: str,
    scenario: SigningScenarioRequest,
) -> dict[str, Any]:
    team_result = (
        supabase.table("teams")
        .select("id,name,abbreviation")
        .eq("id", team_id)
        .limit(1)
        .execute()
    )

    if not team_result.data:
        raise HTTPException(status_code=404, detail="Team not found")

    cap_result = (
        supabase.table("cap_settings")
        .select(
            "season,salary_cap,luxury_tax,first_apron,second_apron"
        )
        .eq("season", scenario.season)
        .limit(1)
        .execute()
    )

    if not cap_result.data:
        raise HTTPException(
            status_code=404,
            detail=f"Cap settings not found for {scenario.season}",
        )

    contracts_result = (
        supabase.table("contracts")
        .select("cap_hit")
        .eq("team_id", team_id)
        .eq("season", scenario.season)
        .execute()
    )

    current_cap_hit = sum(
        contract["cap_hit"]
        for contract in contracts_result.data
        if contract["cap_hit"] is not None
    )

    cap = cap_result.data[0]

    minimum_rule = None
    base_salary = None

    if scenario.mechanism == SigningMechanism.VETERAN_MINIMUM:
        if scenario.years_of_service is None:
            raise HTTPException(
                status_code=422,
                detail="years_of_service is required for veteran minimum",
            )

        if scenario.contract_years is None:
            raise HTTPException(
                status_code=422,
                detail="contract_years is required for veteran minimum",
            )

        scale_result = (
            supabase.table("minimum_salary_scale")
            .select(
                "season,"
                "years_of_service_min,"
                "years_of_service_max,"
                "base_salary,"
                "standard_cap_charge"
            )
            .eq("season", scenario.season)
            .execute()
        )

        minimum_rule = evaluate_minimum_signing(
            season=scenario.season,
            years_of_service=scenario.years_of_service,
            contract_years=scenario.contract_years,
            scale_rows=scale_result.data,
        )

        if not minimum_rule["allowed"]:
            return {
                "team": team_result.data[0],
                "season": scenario.season,
                "proposed_player": {
                    "name": scenario.player_name,
                    "mechanism": scenario.mechanism.value,
                },
                "calculation": None,
                "legal_analysis": {
                    "overall_status": "not_allowed",
                    "rules": [minimum_rule],
                },
            }

        added_cap_hit = minimum_rule["cap_hit"]
        base_salary = minimum_rule["base_salary"]

        if added_cap_hit is None:
            raise HTTPException(
                status_code=500,
                detail="Minimum signing produced no cap hit",
            )

    elif scenario.mechanism in (
        SigningMechanism.AUTO,
        SigningMechanism.CAP_ROOM,
    ):
        if scenario.cap_hit is None:
            raise HTTPException(
                status_code=422,
                detail="cap_hit is required for this signing mechanism",
            )

        added_cap_hit = scenario.cap_hit

    else:
        raise HTTPException(
            status_code=501,
            detail=f"{scenario.mechanism.value} is not implemented yet",
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

    return {
        "team": team_result.data[0],
        "season": scenario.season,
        "proposed_player": {
            "name": scenario.player_name,
            "cap_hit": added_cap_hit,
        },
        "calculation": calculation,
        "legal_analysis": {
    "overall_status": (
        minimum_rule["status"]
        if minimum_rule
        else "payroll_impact_only"
    ),
    "rules": [minimum_rule] if minimum_rule else [],
    "disclaimer": (
        "Only the selected signing mechanism has been evaluated. "
        "Other CBA restrictions may still apply."
            ),
        },
    }