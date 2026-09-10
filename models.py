"""
Data models for Indian Railways Automatic Block Planning & Asset Availability Maximization.
"""
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
from enum import Enum


class TrainCategory(str, Enum):
    VANDE_BHARAT = "Vande Bharat"
    RAJDHANI = "Rajdhani Express"
    SUPERFAST = "Superfast / Mail Express"
    PASSENGER = "Suburban / Passenger"
    FREIGHT = "Freight / Goods (BOXN/Container)"


class TrackDirection(str, Enum):
    UP = "UP"      # Towards Delhi
    DOWN = "DOWN"  # Towards Kanpur / Prayagraj
    BOTH = "BOTH"


class BlockStatus(str, Enum):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"


class Department(str, Enum):
    ENGINEERING = "Civil Engineering (P-Way)"
    ELECTRICAL = "Electrical (TRD / OHE)"
    SIGNALING = "Signaling & Telecom (S&T)"


@dataclass
class Station:
    code: str
    name: str
    km: float
    has_loops: bool = True
    loop_lines_up: int = 2
    loop_lines_down: int = 2


@dataclass
class Section:
    section_id: str
    from_station: str
    to_station: str
    direction: TrackDirection
    length_km: float
    max_speed_kmh: float = 130.0
    is_blocked: bool = False
    active_block_id: Optional[str] = None


@dataclass
class TrainStop:
    station_code: str
    arrival_min: int   # Minutes from 00:00
    departure_min: int


@dataclass
class Train:
    train_no: str
    name: str
    category: TrainCategory
    direction: TrackDirection
    priority_weight: int       # 10: Vande Bharat, 9: Rajdhani, 7: Superfast, 4: Passenger, 2: Freight
    start_time_min: int        # Scheduled entry into section in minutes (0 - 1440)
    avg_speed_kmh: float
    current_delay_min: int = 0 # Injected or dynamic delay
    schedule: List[TrainStop] = field(default_factory=list)
    color: str = "#3B82F6"


@dataclass
class MaintenanceBlock:
    block_id: str
    department: Department
    section_id: str
    direction: TrackDirection
    from_km: float
    to_km: float
    requested_start_min: int
    requested_duration_min: int
    urgency_score: int         # 1-100 (e.g. 95 for USFD rail flaw, 40 for routine tamping)
    work_description: str
    machine_required: str      # e.g., "Duomatic Tamping Machine", "OHE Tower Wagon", "Manual Gang"
    status: BlockStatus = BlockStatus.REQUESTED
    granted_start_min: Optional[int] = None
    granted_duration_min: Optional[int] = None
    delay_impact_min: int = 0
    shadow_block: bool = False
    rationale: str = ""


@dataclass
class AssetHealth:
    asset_id: str
    asset_type: str            # "Track Geometry", "Rail USFD Flaw", "OHE Contact Wire", "Point Machine"
    section_id: str
    location_km: float
    health_score: float        # 0 - 100
    status: str                # "Critical", "Moderate", "Healthy"
    last_inspection: str
    recommended_maintenance: str
    urgency: int
