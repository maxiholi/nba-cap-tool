from services.minimum_salary_service import evaluate_minimum_signing


SCALE_ROWS = [
    {
        "season": "2026-27",
        "years_of_service_min": 10,
        "years_of_service_max": None,
        "base_salary": 3_876_529,
        "standard_cap_charge": 2_449_421,
    }
]


def test_allows_one_year_veteran_minimum() -> None:
    result = evaluate_minimum_signing(
        season="2026-27",
        years_of_service=12,
        contract_years=1,
        scale_rows=SCALE_ROWS,
    )

    assert result["allowed"] is True
    assert result["status"] == "allowed"
    assert result["base_salary"] == 3_876_529
    assert result["cap_hit"] == 2_449_421


def test_allows_two_year_veteran_minimum() -> None:
    result = evaluate_minimum_signing(
        season="2026-27",
        years_of_service=10,
        contract_years=2,
        scale_rows=SCALE_ROWS,
    )

    assert result["allowed"] is True
    assert result["contract_years"] == 2


def test_rejects_three_year_minimum_contract() -> None:
    result = evaluate_minimum_signing(
        season="2026-27",
        years_of_service=12,
        contract_years=3,
        scale_rows=SCALE_ROWS,
    )

    assert result["allowed"] is False
    assert result["status"] == "not_allowed"
    assert result["cap_hit"] is None


def test_reports_missing_scale_row() -> None:
    result = evaluate_minimum_signing(
        season="2026-27",
        years_of_service=2,
        contract_years=1,
        scale_rows=SCALE_ROWS,
    )

    assert result["allowed"] is False
    assert result["base_salary"] is None
    assert "No minimum-salary scale entry" in result["explanation"]