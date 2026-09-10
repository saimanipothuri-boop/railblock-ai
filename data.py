"""
Realistic Indian Railways corridor dataset (HDN-1 Corridor: New Delhi - Kanpur Central).
"""
from typing import List, Dict
from models import (
    Station, Section, Train, TrainStop, MaintenanceBlock,
    AssetHealth, TrainCategory, TrackDirection, BlockStatus, Department
)


def get_default_stations() -> List[Station]:
    return [
        Station(code="NDLS", name="New Delhi", km=0.0, has_loops=True, loop_lines_up=4, loop_lines_down=4),
        Station(code="GZB", name="Ghaziabad Jn", km=25.0, has_loops=True, loop_lines_up=3, loop_lines_down=3),
        Station(code="ALJN", name="Aligarh Jn", km=131.0, has_loops=True, loop_lines_up=3, loop_lines_down=3),
        Station(code="TDL", name="Tundla Jn", km=209.0, has_loops=True, loop_lines_up=4, loop_lines_down=4),
        Station(code="ETW", name="Etawah Jn", km=300.0, has_loops=True, loop_lines_up=2, loop_lines_down=2),
        Station(code="CNB", name="Kanpur Central", km=440.0, has_loops=True, loop_lines_up=5, loop_lines_down=5),
    ]


def get_default_sections() -> List[Section]:
    stations = get_default_stations()
    sections = []
    for i in range(len(stations) - 1):
        s_from = stations[i]
        s_to = stations[i + 1]
        dist = s_to.km - s_from.km

        # DOWN line (Delhi -> Kanpur)
        sections.append(Section(
            section_id=f"DN-{s_from.code}-{s_to.code}",
            from_station=s_from.code,
            to_station=s_to.code,
            direction=TrackDirection.DOWN,
            length_km=dist,
            max_speed_kmh=130.0
        ))
        # UP line (Kanpur -> Delhi)
        sections.append(Section(
            section_id=f"UP-{s_to.code}-{s_from.code}",
            from_station=s_to.code,
            to_station=s_from.code,
            direction=TrackDirection.UP,
            length_km=dist,
            max_speed_kmh=130.0
        ))
    return sections


def calculate_train_schedule(
    train_no: str, name: str, category: TrainCategory, direction: TrackDirection,
    priority: int, start_min: int, avg_speed: float, color: str, stops_at: List[str]
) -> Train:
    stations = get_default_stations()
    if direction == TrackDirection.UP:
        ordered_stations = list(reversed(stations))
    else:
        ordered_stations = stations

    schedule = []
    current_time = start_min
    last_km = ordered_stations[0].km

    for st in ordered_stations:
        travel_dist = abs(st.km - last_km)
        travel_time = int((travel_dist / avg_speed) * 60)
        arr_time = current_time + travel_time
        
        # Dwell time
        if st.code in stops_at and st.code not in (ordered_stations[0].code, ordered_stations[-1].code):
            dwell = 5
        elif st.code in (ordered_stations[0].code, ordered_stations[-1].code):
            dwell = 0
        else:
            dwell = 1 # Passing / token signal buffer

        dep_time = arr_time + dwell
        schedule.append(TrainStop(
            station_code=st.code,
            arrival_min=arr_time,
            departure_min=dep_time
        ))
        current_time = dep_time
        last_km = st.km

    return Train(
        train_no=train_no,
        name=name,
        category=category,
        direction=direction,
        priority_weight=priority,
        start_time_min=start_min,
        avg_speed_kmh=avg_speed,
        current_delay_min=0,
        schedule=schedule,
        color=color
    )


def get_default_trains() -> List[Train]:
    trains = []

    # 1. 22436 Vande Bharat Express (NDLS -> CNB)
    trains.append(calculate_train_schedule(
        train_no="22436", name="Vande Bharat Express",
        category=TrainCategory.VANDE_BHARAT, direction=TrackDirection.DOWN,
        priority=10, start_min=360, avg_speed=110.0, color="#2563EB", stops_at=["NDLS", "CNB"]
    ))

    # 2. 12424 Dibrugarh Rajdhani Express (NDLS -> CNB)
    trains.append(calculate_train_schedule(
        train_no="12424", name="Dibrugarh Rajdhani",
        category=TrainCategory.RAJDHANI, direction=TrackDirection.DOWN,
        priority=9, start_min=420, avg_speed=95.0, color="#DC2626", stops_at=["NDLS", "CNB"]
    ))

    # 3. 12004 Lucknow Swarna Shatabdi (NDLS -> CNB)
    trains.append(calculate_train_schedule(
        train_no="12004", name="Lucknow Shatabdi",
        category=TrainCategory.SUPERFAST, direction=TrackDirection.DOWN,
        priority=8, start_min=480, avg_speed=92.0, color="#059669", stops_at=["NDLS", "GZB", "ALJN", "CNB"]
    ))

    # 4. 12556 Gorakhdham Superfast Express (NDLS -> CNB)
    trains.append(calculate_train_schedule(
        train_no="12556", name="Gorakhdham SF Exp",
        category=TrainCategory.SUPERFAST, direction=TrackDirection.DOWN,
        priority=7, start_min=570, avg_speed=80.0, color="#7C3AED", stops_at=["NDLS", "GZB", "ALJN", "TDL", "CNB"]
    ))

    # 5. BCN-882 Container Freight (Dadri -> Durgapur)
    trains.append(calculate_train_schedule(
        train_no="BCN-882", name="Dadri Goods Container",
        category=TrainCategory.FREIGHT, direction=TrackDirection.DOWN,
        priority=2, start_min=660, avg_speed=55.0, color="#D97706", stops_at=["GZB", "TDL"]
    ))

    # 6. 12398 Mahabodhi Express (NDLS -> CNB)
    trains.append(calculate_train_schedule(
        train_no="12398", name="Mahabodhi Express",
        category=TrainCategory.SUPERFAST, direction=TrackDirection.DOWN,
        priority=7, start_min=750, avg_speed=85.0, color="#0891B2", stops_at=["NDLS", "ALJN", "CNB"]
    ))

    # 7. 64583 Ghaziabad - Tundla MEMU
    trains.append(calculate_train_schedule(
        train_no="64583", name="Ghaziabad-Tundla MEMU",
        category=TrainCategory.PASSENGER, direction=TrackDirection.DOWN,
        priority=4, start_min=840, avg_speed=50.0, color="#4B5563", stops_at=["GZB", "ALJN", "TDL"]
    ))

    # 8. BTPN-108 POL Tanker Freight
    trains.append(calculate_train_schedule(
        train_no="BTPN-108", name="Mathura POL Oil Rake",
        category=TrainCategory.FREIGHT, direction=TrackDirection.DOWN,
        priority=2, start_min=960, avg_speed=52.0, color="#B45309", stops_at=["TDL"]
    ))

    # 9. 22435 Vande Bharat Express (CNB -> NDLS) [UP]
    trains.append(calculate_train_schedule(
        train_no="22435", name="Vande Bharat (Return)",
        category=TrainCategory.VANDE_BHARAT, direction=TrackDirection.UP,
        priority=10, start_min=400, avg_speed=110.0, color="#2563EB", stops_at=["CNB", "NDLS"]
    ))

    # 10. 12454 Ranchi Rajdhani (CNB -> NDLS) [UP]
    trains.append(calculate_train_schedule(
        train_no="12454", name="Ranchi Rajdhani",
        category=TrainCategory.RAJDHANI, direction=TrackDirection.UP,
        priority=9, start_min=460, avg_speed=95.0, color="#DC2626", stops_at=["CNB", "NDLS"]
    ))

    # 11. 12418 Prayagraj Express (CNB -> NDLS) [UP]
    trains.append(calculate_train_schedule(
        train_no="12418", name="Prayagraj Express",
        category=TrainCategory.SUPERFAST, direction=TrackDirection.UP,
        priority=7, start_min=540, avg_speed=85.0, color="#4F46E5", stops_at=["CNB", "ALJN", "GZB", "NDLS"]
    ))

    # 12. BOXN-412 Thermal Coal Freight [UP]
    trains.append(calculate_train_schedule(
        train_no="BOXN-412", name="Thermal Coal Rake",
        category=TrainCategory.FREIGHT, direction=TrackDirection.UP,
        priority=2, start_min=620, avg_speed=52.0, color="#92400E", stops_at=["CNB", "TDL", "GZB"]
    ))

    # 13. 12802 Purushottam Express (CNB -> NDLS) [UP]
    trains.append(calculate_train_schedule(
        train_no="12802", name="Purushottam Express",
        category=TrainCategory.SUPERFAST, direction=TrackDirection.UP,
        priority=7, start_min=720, avg_speed=82.0, color="#0D9488", stops_at=["CNB", "TDL", "ALJN", "GZB", "NDLS"]
    ))

    # 14. 64152 Tundla - Aligarh EMU [UP]
    trains.append(calculate_train_schedule(
        train_no="64152", name="Tundla-Aligarh EMU",
        category=TrainCategory.PASSENGER, direction=TrackDirection.UP,
        priority=4, start_min=800, avg_speed=50.0, color="#6B7280", stops_at=["TDL", "ALJN"]
    ))

    # 15. CONCOR-714 Fast Freight Container [UP]
    trains.append(calculate_train_schedule(
        train_no="CONCOR-714", name="CONCOR High-Speed Freight",
        category=TrainCategory.FREIGHT, direction=TrackDirection.UP,
        priority=3, start_min=900, avg_speed=65.0, color="#D97706", stops_at=["CNB", "GZB"]
    ))

    # 16. 14218 Unchahar Express (CNB -> NDLS) [UP]
    trains.append(calculate_train_schedule(
        train_no="14218", name="Unchahar Express",
        category=TrainCategory.SUPERFAST, direction=TrackDirection.UP,
        priority=6, start_min=990, avg_speed=75.0, color="#6366F1", stops_at=["CNB", "ETW", "TDL", "ALJN", "GZB", "NDLS"]
    ))

    return trains


def get_default_blocks() -> List[MaintenanceBlock]:
    return [
        # Critical USFD Rail Flaw renewal in TDL-ETW DOWN line
        MaintenanceBlock(
            block_id="MB-01",
            department=Department.ENGINEERING,
            section_id="DN-TDL-ETW",
            direction=TrackDirection.DOWN,
            from_km=235.0,
            to_km=248.0,
            requested_start_min=620,   # ~10:20 AM
            requested_duration_min=90,  # 1.5 hrs
            urgency_score=96,
            work_description="Immediate USFD Rail Flaw clamp replacement & Thermit Weld Renewal. High risk of rail fracture.",
            machine_required="Portable Thermit Welding Kit & Gang",
            status=BlockStatus.REQUESTED
        ),
        # Machine Track Tamping in ALJN-TDL DOWN line
        MaintenanceBlock(
            block_id="MB-02",
            department=Department.ENGINEERING,
            section_id="DN-ALJN-TDL",
            direction=TrackDirection.DOWN,
            from_km=155.0,
            to_km=172.0,
            requested_start_min=500,   # ~08:20 AM (Conflicts with Shatabdi and Gorakhdham manually!)
            requested_duration_min=120, # 2.0 hrs
            urgency_score=72,
            work_description="Plasser 09-3X Duomatic Tamping Machine track packing and alignment post-monsoon.",
            machine_required="Plasser Duomatic Tamper + DTS",
            status=BlockStatus.REQUESTED
        ),
        # OHE Contact Wire maintenance in GZB-ALJN UP line
        MaintenanceBlock(
            block_id="MB-03",
            department=Department.ELECTRICAL,
            section_id="UP-ALJN-GZB",
            direction=TrackDirection.UP,
            from_km=65.0,
            to_km=82.0,
            requested_start_min=640,   # ~10:40 AM
            requested_duration_min=150, # 2.5 hrs
            urgency_score=84,
            work_description="Overhead contact wire replacement and bracket insulator cleaning under power cutoff.",
            machine_required="8-Wheeler self-propelled OHE Tower Wagon",
            status=BlockStatus.REQUESTED
        ),
        # S&T Point machine testing at Aligarh Yard
        MaintenanceBlock(
            block_id="MB-04",
            department=Department.SIGNALING,
            section_id="DN-GZB-ALJN",
            direction=TrackDirection.DOWN,
            from_km=128.0,
            to_km=131.0,
            requested_start_min=860,   # ~14:20 PM
            requested_duration_min=60,  # 1.0 hr
            urgency_score=62,
            work_description="Electronic Interlocking (EI) testing and point machine 102A/B overhaul.",
            machine_required="S&T Test Van & Simulation Bench",
            status=BlockStatus.REQUESTED
        ),
        # Deep Ballast Screening Machine in ETW-CNB UP line
        MaintenanceBlock(
            block_id="MB-05",
            department=Department.ENGINEERING,
            section_id="UP-CNB-ETW",
            direction=TrackDirection.UP,
            from_km=360.0,
            to_km=375.0,
            requested_start_min=820,   # ~13:40 PM
            requested_duration_min=180, # 3.0 hrs
            urgency_score=78,
            work_description="Ballast Cleaning Machine (BCM) deep screening for fouled ballast drainage recovery.",
            machine_required="BCM RM-80 Ballast Cleaner + Hopper Rake",
            status=BlockStatus.REQUESTED
        )
    ]


def get_default_assets() -> List[AssetHealth]:
    return [
        AssetHealth(
            asset_id="TRK-TDL-ETW-245",
            asset_type="Rail USFD Flaw",
            section_id="DN-TDL-ETW",
            location_km=245.2,
            health_score=28.5,
            status="Critical",
            last_inspection="2026-09-07 (USFD Hand Trolley)",
            recommended_maintenance="Immediate Thermit rail weld renewal & fishplate clamp",
            urgency=96
        ),
        AssetHealth(
            asset_id="OHE-GZB-ALJN-72",
            asset_type="OHE Contact Wire",
            section_id="UP-ALJN-GZB",
            location_km=72.4,
            health_score=52.0,
            status="Moderate",
            last_inspection="2026-09-04 (TRD Inspection)",
            recommended_maintenance="Wire thickness worn to 8.8mm (Limit 8.25mm); dropper renewal",
            urgency=84
        ),
        AssetHealth(
            asset_id="TRK-ALJN-TDL-162",
            asset_type="Track Geometry (TQI)",
            section_id="DN-ALJN-TDL",
            location_km=162.0,
            health_score=61.0,
            status="Moderate",
            last_inspection="2026-08-28 (Track Recording Car)",
            recommended_maintenance="TQI index degraded to 34.2; machine tamping and lifting required",
            urgency=72
        ),
        AssetHealth(
            asset_id="SIG-ALJN-YARD-102",
            asset_type="Point Machine 102A",
            section_id="DN-GZB-ALJN",
            location_km=130.8,
            health_score=68.0,
            status="Moderate",
            last_inspection="2026-09-01 (S&T Monthly Audit)",
            recommended_maintenance="Operating current 4.2A; friction clutch and lock slide adjustment",
            urgency=62
        ),
        AssetHealth(
            asset_id="TRK-ETW-CNB-368",
            asset_type="Ballast Bed Condition",
            section_id="UP-CNB-ETW",
            location_km=368.5,
            health_score=48.0,
            status="Moderate",
            last_inspection="2026-08-22 (P-Way Gang walk)",
            recommended_maintenance="Ballast cushion fouled with silt; BCM deep screening needed",
            urgency=78
        ),
        AssetHealth(
            asset_id="TRK-NDLS-GZB-14",
            asset_type="Track Geometry (TQI)",
            section_id="DN-NDLS-GZB",
            location_km=14.0,
            health_score=92.0,
            status="Healthy",
            last_inspection="2026-09-05 (Track Recording Car)",
            recommended_maintenance="Routine monitoring; TQI within excellent limit (19.4)",
            urgency=15
        )
    ]
