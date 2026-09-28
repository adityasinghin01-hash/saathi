from app.domain.status import can_transition


def test_case_path_and_side_exits():
    assert can_transition("reported", "verified", None)
    assert can_transition("verified", "transfer_drafted", "confirmed_stockout")
    assert can_transition("verified", "supplied", "stock_available")
    assert can_transition("verified", "closed", "household_only")
    assert can_transition("received", "supplied", "confirmed_stockout")
    assert can_transition("received", "partially_supplied", "confirmed_stockout")
    assert can_transition("partially_supplied", "partially_supplied", "confirmed_stockout")
    assert can_transition("partially_supplied", "supplied", "confirmed_stockout")
    assert can_transition("transfer_drafted", "verified", "confirmed_stockout")
    assert not can_transition("reported", "supplied", None)
    assert not can_transition("verified", "transfer_drafted", "stock_available")
    assert not can_transition("closed", "cancelled", "household_only")
