from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@app.get("/teams/nyk/payroll")
def get_knicks_payroll() -> dict[str, Any]:
    # Temporary sample data. We will replace this with database data later.
    salary_cap = 155_000_000
    luxury_tax = 188_000_000
    first_apron = 196_000_000
    second_apron = 208_000_000

    players = [
        {"name": "Player A", "salary": 45_000_000},
        {"name": "Player B", "salary": 38_000_000},
        {"name": "Player C", "salary": 29_000_000},
        {"name": "Player D", "salary": 21_000_000},
        {"name": "Player E", "salary": 12_000_000},
    ]

    total_salary = sum(player["salary"] for player in players)

    return {
        "team": {
            "id": "nyk",
            "name": "New York Knicks",
        },
        "season": "Sample season",
        "players": players,
        "totals": {
            "team_salary": total_salary,
            "salary_cap": salary_cap,
            "cap_space": salary_cap - total_salary,
            "luxury_tax": luxury_tax,
            "tax_room": luxury_tax - total_salary,
            "first_apron": first_apron,
            "first_apron_room": first_apron - total_salary,
            "second_apron": second_apron,
            "second_apron_room": second_apron - total_salary,
        },
        "is_sample_data": True,
    }