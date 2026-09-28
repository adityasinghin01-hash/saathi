import math
from datetime import date, timedelta

from app.domain.forecast import daily_combined, latest_snapshot


def distance_km(a: dict, b: dict) -> float:
    lat1, lat2 = math.radians(a["lat"]), math.radians(b["lat"])
    dlat = lat2 - lat1
    dlng = math.radians(b["lng"] - a["lng"])
    hav = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(hav))


def select_donor(store, case: dict, today: date) -> dict | None:
    from ortools.graph.python import min_cost_flow

    receiver = store.get("facility", case["facility_id"])
    drug = store.get("drug", case["drug_id"])
    if not receiver or not drug:
        return None
    candidates = []
    for facility in sorted(store.list("facility"), key=lambda row: row["id"]):
        if (facility["type"] != "PHC" or facility["id"] == receiver["id"]
                or facility["district"] != receiver["district"]):
            continue
        snapshot = latest_snapshot(store, facility["id"], drug["id"])
        if not snapshot:
            continue
        safety = math.ceil(14 * daily_combined(store, facility["id"], drug["id"]))
        surplus = max(0, snapshot["on_hand"] - safety)
        # ASSUMPTION: arrival is one day after the draft; expiry must be later than 30 days after it.
        eligible = sorted((batch for batch in snapshot["batches"]
                           if date.fromisoformat(batch["expiry_date"]) > today + timedelta(days=31)),
                          key=lambda batch: (batch["expiry_date"], batch["id"]))
        if surplus < case["requested_qty"] or sum(b["quantity"] for b in eligible) < case["requested_qty"]:
            continue
        # Drug identity fixes unit identity because each drug has one contract unit.
        candidates.append((facility, eligible, distance_km(facility, receiver)))
    if not candidates:
        return None

    # One Transfer has one donor. Each candidate can supply the full request; min-cost flow
    # chooses the lowest-distance donor, with stable ordering for equal distances.
    flow = min_cost_flow.SimpleMinCostFlow()
    sink = len(candidates) + 1
    for index, (_, _, distance) in enumerate(candidates, start=1):
        flow.add_arc_with_capacity_and_unit_cost(0, index, case["requested_qty"], 0)
        flow.add_arc_with_capacity_and_unit_cost(index, sink, case["requested_qty"],
                                                  round(distance * 1000) * 100 + index)
        flow.set_node_supply(index, 0)
    flow.set_node_supply(0, case["requested_qty"])
    flow.set_node_supply(sink, -case["requested_qty"])
    if flow.solve() != flow.OPTIMAL:
        return None
    chosen_index = next(index for index in range(len(candidates))
                        if flow.flow(2 * index + 1) > 0)
    facility, batches, distance = candidates[chosen_index]
    remaining = case["requested_qty"]
    selected = []
    for batch in batches:
        if remaining <= 0:
            break
        take = min(remaining, batch["quantity"])
        selected.append({"batch_id": batch["id"], "quantity": take,
                         "expiry_date": batch["expiry_date"]})
        remaining -= take
    return {"donor": facility, "batches": selected, "distance_km": distance,
            "unit": drug["unit"]}
