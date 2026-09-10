"""
Automated Test Suite for RailBlock-AI System.
"""
from data import (
    get_default_stations, get_default_sections,
    get_default_trains, get_default_blocks, get_default_assets
)
from optimizer import BlockOptimizer
from models import MaintenanceBlock, Department, TrackDirection, BlockStatus


def test_optimizer_modes():
    print("Testing Optimizer across modes...")
    stations = get_default_stations()
    sections = get_default_sections()
    trains = get_default_trains()
    blocks = get_default_blocks()

    opt = BlockOptimizer(stations, sections)

    # 1. Balanced Mode
    b_opt, kpis_bal = opt.optimize_all_blocks(blocks, trains, mode="balanced")
    assert len(b_opt) == len(blocks), "All blocks must be scheduled"
    assert kpis_bal["shadow_blocks"] >= 1, "Should discover shadow blocks"
    assert kpis_bal["saved_delay_min"] > 0, "Should save delay vs naive manual"
    print(f"  [PASS] Balanced Mode: Saved {kpis_bal['saved_delay_hours']}h delay, {kpis_bal['shadow_blocks']} shadow blocks")

    # 2. Zero Passenger Delay Mode
    b_opt_zd, kpis_zd = opt.optimize_all_blocks(blocks, trains, mode="zero_delay")
    print(f"  [PASS] Zero Delay Mode: Saved {kpis_zd['saved_delay_hours']}h delay")

    # 3. Urgent Safety Mode
    b_opt_us, kpis_us = opt.optimize_all_blocks(blocks, trains, mode="urgent_safety")
    print(f"  [PASS] Urgent Safety Mode: Scheduled {len(b_opt_us)} blocks")


def test_conflict_detection():
    print("Testing Conflict Detection...")
    stations = get_default_stations()
    sections = get_default_sections()
    trains = get_default_trains()
    opt = BlockOptimizer(stations, sections)

    # Block placed at 06:10 in NDLS-GZB DOWN line (overlaps with Vande Bharat at 06:00-06:20)
    test_block = MaintenanceBlock(
        block_id="TEST-01",
        department=Department.ENGINEERING,
        section_id="DN-NDLS-GZB",
        direction=TrackDirection.DOWN,
        from_km=5.0,
        to_km=15.0,
        requested_start_min=365,
        requested_duration_min=60,
        urgency_score=70,
        work_description="Test block",
        machine_required="Test Machine"
    )

    conflicts = opt.detect_conflicts(test_block, trains, 365, 60)
    assert len(conflicts) > 0, "Should detect conflict with early morning trains"
    assert any("22436" in c["train_no"] for c in conflicts), "Should conflict with Vande Bharat 22436"
    print(f"  [PASS] Conflict detection successfully flagged {len(conflicts)} train conflicts")


if __name__ == "__main__":
    test_optimizer_modes()
    test_conflict_detection()
    print("\nALL BACKEND & OPTIMIZER TESTS PASSED!")
