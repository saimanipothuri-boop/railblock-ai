"""
AI Optimization Engine for Indian Railways Automatic Block Planning.
Implements Multi-Objective Heuristic Constraint Solver, Shadow Block Detection,
and Dynamic Real-Time Delay Re-Scheduling.
"""
from typing import List, Dict, Tuple, Optional
import copy
from models import (
    Train, MaintenanceBlock, Section, Station,
    TrackDirection, BlockStatus, TrainCategory
)


class BlockOptimizer:
    def __init__(self, stations: List[Station], sections: List[Section]):
        self.stations = {s.code: s for s in stations}
        self.station_order_dn = [s.code for s in stations]
        self.station_order_up = list(reversed(self.station_order_dn))
        self.sections = {s.section_id: s for s in sections}

    def get_train_section_occupancy(self, train: Train) -> List[Dict]:
        """
        Calculates time intervals when the train occupies each section along its route.
        Accounts for any dynamic delay injected into the train.
        """
        occupancies = []
        sched = train.schedule
        delay = train.current_delay_min

        for i in range(len(sched) - 1):
            st_curr = sched[i]
            st_next = sched[i + 1]

            t_enter = st_curr.departure_min + delay
            t_exit = st_next.arrival_min + delay

            # Identify section
            if train.direction == TrackDirection.DOWN:
                sec_id = f"DN-{st_curr.station_code}-{st_next.station_code}"
            else:
                sec_id = f"UP-{st_curr.station_code}-{st_next.station_code}"

            occupancies.append({
                "train_no": train.train_no,
                "train_name": train.name,
                "category": train.category.value,
                "priority": train.priority_weight,
                "section_id": sec_id,
                "direction": train.direction.value,
                "enter_min": t_enter,
                "exit_min": t_exit
            })
        return occupancies

    def detect_conflicts(self, block: MaintenanceBlock, trains: List[Train], start_time: int, duration: int) -> List[Dict]:
        """
        Detects conflicts between a proposed block window [start_time, start_time + duration]
        and train movements on that section.
        """
        block_end = start_time + duration
        conflicts = []

        for train in trains:
            # Check direction compatibility
            if block.direction != TrackDirection.BOTH and train.direction != block.direction:
                continue

            occupancies = self.get_train_section_occupancy(train)
            for occ in occupancies:
                if occ["section_id"] == block.section_id:
                    # Check temporal overlap
                    # Overlap if max(start1, start2) < min(end1, end2)
                    t_in = occ["enter_min"]
                    t_out = occ["exit_min"]

                    # Safety buffer of 5 minutes before and after block
                    b_start = start_time - 5
                    b_end = block_end + 5

                    if max(t_in, b_start) < min(t_out, b_end):
                        # Calculate required train detention / delay
                        if t_in < start_time:
                            # Train reached during block
                            detention = block_end - t_in
                        else:
                            detention = block_end - t_in

                        conflicts.append({
                            "train_no": train.train_no,
                            "train_name": train.name,
                            "category": train.category.value,
                            "priority": train.priority_weight,
                            "train_enter_min": t_in,
                            "train_exit_min": t_out,
                            "block_start_min": start_time,
                            "block_end_min": block_end,
                            "detention_min": max(10, detention)
                        })
        return conflicts

    def find_shadow_blocks(self, block: MaintenanceBlock, trains: List[Train], time_window_start: int = 300, time_window_end: int = 1320) -> List[Dict]:
        """
        Finds natural timetable gaps ("Shadow Blocks") in the section where maintenance
        can be executed with zero or negligible delay to trains.
        """
        # Collect all train passages in this section
        passages = []
        for train in trains:
            if block.direction != TrackDirection.BOTH and train.direction != block.direction:
                continue
            for occ in self.get_train_section_occupancy(train):
                if occ["section_id"] == block.section_id:
                    passages.append((occ["enter_min"], occ["exit_min"], occ["train_name"]))

        passages.sort(key=lambda x: x[0])

        gaps = []
        curr_t = time_window_start

        for p_in, p_out, t_name in passages:
            if p_in - curr_t >= block.requested_duration_min:
                gaps.append({
                    "start_min": curr_t + 5,
                    "end_min": p_in - 5,
                    "available_duration": (p_in - 5) - (curr_t + 5),
                    "after_train": None if curr_t == time_window_start else "Traffic gap",
                    "before_train": t_name
                })
            curr_t = max(curr_t, p_out)

        if time_window_end - curr_t >= block.requested_duration_min:
            gaps.append({
                "start_min": curr_t + 5,
                "end_min": time_window_end,
                "available_duration": time_window_end - (curr_t + 5),
                "after_train": "Traffic gap",
                "before_train": "End of window"
            })

        return gaps

    def optimize_single_block(
        self,
        block: MaintenanceBlock,
        trains: List[Train],
        mode: str = "balanced"
    ) -> Dict:
        """
        Optimizes placement of a single maintenance block using AI heuristic search.
        Modes:
          - 'balanced': Minimizes weighted train delay while honoring requested window proximity.
          - 'zero_delay': Strict preference for shadow gaps; delays to passenger trains disallowed.
          - 'urgent_safety': Critical asset health overrides; grants block nearest to requested time.
        """
        best_start = block.requested_start_min
        best_duration = block.requested_duration_min
        best_score = float('inf')
        best_conflicts = []
        is_shadow = False
        rationale = ""

        # Search window around requested time (+/- 180 mins in 10-min increments)
        search_radius = 240 if mode == "balanced" else (360 if mode == "zero_delay" else 60)
        min_search = max(300, block.requested_start_min - search_radius)
        max_search = min(1380, block.requested_start_min + search_radius)

        # Check shadow gaps first
        shadow_gaps = self.find_shadow_blocks(block, trains, min_search, max_search)
        
        # Look for shadow gap closest to requested time
        closest_shadow = None
        min_shadow_dist = float('inf')
        for gap in shadow_gaps:
            if gap["available_duration"] >= block.requested_duration_min:
                dist = abs(gap["start_min"] - block.requested_start_min)
                if dist < min_shadow_dist:
                    min_shadow_dist = dist
                    closest_shadow = gap

        if closest_shadow and (mode == "zero_delay" or min_shadow_dist <= 120):
            best_start = closest_shadow["start_min"]
            best_duration = block.requested_duration_min
            is_shadow = True
            best_conflicts = []
            rationale = (
                f"AI identified natural shadow slot between {self.format_min(best_start)} "
                f"and {self.format_min(best_start + best_duration)} with ZERO train detention."
            )
            return {
                "granted_start_min": best_start,
                "granted_duration_min": best_duration,
                "delay_impact_min": 0,
                "is_shadow": True,
                "conflicts": [],
                "rationale": rationale,
                "score": 0.0
            }

        # Multi-objective heuristic evaluation
        candidate_times = range(min_search, max_search, 10)
        for cand_start in candidate_times:
            conflicts = self.detect_conflicts(block, trains, cand_start, block.requested_duration_min)

            # Weight calculations
            delay_penalty = 0
            has_high_priority_conflict = False

            for c in conflicts:
                weight = c["priority"]
                detention = c["detention_min"]
                delay_penalty += (weight ** 1.8) * detention
                if weight >= 8:
                    has_high_priority_conflict = True

            # Mode penalty adjustments
            if mode == "zero_delay" and has_high_priority_conflict:
                continue

            time_shift_penalty = abs(cand_start - block.requested_start_min) * 0.8
            
            # Critical urgency penalty (if urgent, penalize shifting away)
            if mode == "urgent_safety" or block.urgency_score > 90:
                time_shift_penalty *= 3.0
                delay_penalty *= 0.5  # Accept train delay for track safety

            total_score = delay_penalty + time_shift_penalty

            if total_score < best_score:
                best_score = total_score
                best_start = cand_start
                best_conflicts = conflicts

        # Formulate rationale
        total_delay = sum(c["detention_min"] for c in best_conflicts)
        shift = best_start - block.requested_start_min

        if len(best_conflicts) == 0:
            rationale = f"AI shifted block by {shift:+d} mins to completely eliminate train conflicts."
        else:
            affected_trains = ", ".join([f"{c['train_name']} (+{c['detention_min']}m)" for c in best_conflicts[:2]])
            rationale = (
                f"Optimized schedule shifted by {shift:+d} mins. Regulates {affected_trains} "
                f"on station loop lines while protecting premium train paths."
            )

        return {
            "granted_start_min": best_start,
            "granted_duration_min": best_duration,
            "delay_impact_min": total_delay,
            "is_shadow": len(best_conflicts) == 0,
            "conflicts": best_conflicts,
            "rationale": rationale,
            "score": best_score
        }

    def optimize_all_blocks(
        self,
        blocks: List[MaintenanceBlock],
        trains: List[Train],
        mode: str = "balanced"
    ) -> Tuple[List[MaintenanceBlock], Dict]:
        """
        Sequentially optimizes all pending maintenance blocks in order of urgency score.
        """
        # Sort by urgency descending (Critical safety USFD defects first)
        sorted_blocks = sorted(blocks, key=lambda b: b.urgency_score, reverse=True)
        optimized_blocks = []
        total_delay_impact = 0
        shadow_block_count = 0
        naive_manual_delay = 0

        for b in sorted_blocks:
            # Baseline: naive manual scheduling at requested time
            naive_conflicts = self.detect_conflicts(b, trains, b.requested_start_min, b.requested_duration_min)
            naive_delay = sum(c["detention_min"] for c in naive_conflicts)
            naive_manual_delay += naive_delay

            # Run AI optimization
            res = self.optimize_single_block(b, trains, mode)
            
            b_copy = copy.deepcopy(b)
            b_copy.granted_start_min = res["granted_start_min"]
            b_copy.granted_duration_min = res["granted_duration_min"]
            b_copy.delay_impact_min = res["delay_impact_min"]
            b_copy.shadow_block = res["is_shadow"]
            b_copy.rationale = res["rationale"]
            b_copy.status = BlockStatus.APPROVED

            if res["is_shadow"]:
                shadow_block_count += 1
            total_delay_impact += res["delay_impact_min"]
            optimized_blocks.append(b_copy)

        saved_delay = max(0, naive_manual_delay - total_delay_impact)
        
        # Key Performance Metrics
        total_section_minutes = len(self.sections) * 1440
        total_block_minutes = sum(b.granted_duration_min or 0 for b in optimized_blocks)
        track_availability_pct = round(((total_section_minutes - total_block_minutes) / total_section_minutes) * 100, 2)
        punctuality_pct = round(max(70.0, 100.0 - (total_delay_impact / (len(trains) * 20) * 10)), 1)

        kpis = {
            "total_blocks": len(optimized_blocks),
            "approved_blocks": len(optimized_blocks),
            "shadow_blocks": shadow_block_count,
            "naive_manual_delay_min": naive_manual_delay,
            "ai_optimized_delay_min": total_delay_impact,
            "saved_delay_min": saved_delay,
            "saved_delay_hours": round(saved_delay / 60, 1),
            "track_availability_pct": track_availability_pct,
            "network_punctuality_pct": punctuality_pct,
            "mode": mode
        }

        return optimized_blocks, kpis

    @staticmethod
    def format_min(minutes: int) -> str:
        h = (minutes // 60) % 24
        m = minutes % 60
        return f"{h:02d}:{m:02d}"
