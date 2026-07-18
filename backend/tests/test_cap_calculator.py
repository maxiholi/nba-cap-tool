import pytest

from services.cap_calculator import calculate_payroll_position


def test_calculates_projected_payroll() -> None:
    result = calculate_payroll_position(
        current_cap_hit=200_000_000,
        added_cap_hit=10_000_000,
        salary_cap=165_000_000,
        luxury_tax=200_000_000,
        first_apron=210_000_000,
        second_apron=222_000_000,
    )

    assert result["projected_cap_hit"] == 210_000_000
    assert result["over_salary_cap"] is True
    assert result["over_luxury_tax"] is True
    assert result["over_first_apron"] is False
    assert result["over_second_apron"] is False
    assert result["second_apron_room"] == 12_000_000


def test_rejects_negative_added_cap_hit() -> None:
    with pytest.raises(ValueError):
        calculate_payroll_position(
            current_cap_hit=200_000_000,
            added_cap_hit=-1,
            salary_cap=165_000_000,
            luxury_tax=200_000_000,
            first_apron=210_000_000,
            second_apron=222_000_000,
        )