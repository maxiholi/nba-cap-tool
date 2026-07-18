from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from database import supabase

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