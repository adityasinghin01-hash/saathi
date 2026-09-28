from eval.forecast_eval import build_scenario, evaluate, simulate_supply, simulate_supply_metrics


def test_scenario_truth_is_separate_from_observations():
    scenario = build_scenario("enrolment_gap", 3)
    assert len(scenario.future_demand) == 30
    assert len(scenario.store.list("patient")) == 48
    assert sum(scenario.future_demand) > 0
    assert all(row["patient_id"] for row in scenario.store.list("dispensing"))
    outside = build_scenario("outside_purchases", 3)
    assert sum(outside.future_demand) > sum(outside.future_clinic_requests)


def test_supply_counts_unmet_patient_days_and_replenishment_delay():
    assert simulate_supply([3] * 3, initial_stock=4, forecast=9, alert=False) == 5
    assert simulate_supply([3] * 3, initial_stock=4, forecast=9, alert=True,
                           delivery_delay=1) == 0


def test_overstock_uses_true_need_even_when_some_patients_buy_elsewhere():
    assert simulate_supply_metrics([0, 0], 100, 0, False, true_need_30=30) == (0, 70, 0)


def test_evaluation_has_all_methods_and_breaking_scenarios():
    result = evaluate(repetitions=2)
    assert "enrolment_gap" in result["scenarios"]
    assert "outside_purchases" in result["scenarios"]
    assert "long_stockout" in result["scenarios"]
    assert "false_reports" in result["scenarios"]
    assert set(result["scenarios"]["baseline"]["methods"]) == {
        "dispensing_only", "prescription_only", "calibrated", "combined"
    }
    assert result["scenarios"]["false_reports"]["false_report_count"] > 0
    assert (result["scenarios"]["false_reports"]["methods"]
            == result["scenarios"]["baseline"]["methods"])
    assert result["scenarios"]["baseline"]["methods"]["combined"]["mae_daily"] >= 0
    assert result["scenarios"]["baseline"]["methods"]["combined"]["overstock_units"] >= 0
    assert result["scenarios"]["baseline"]["methods"]["combined"]["stockout_days"] >= 0
