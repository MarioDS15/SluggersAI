"""Player stats from CSV (roster templates, not tied to a team)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Player:
    """Base player stats loaded from the spreadsheet."""

    player: str
    hit_trajectory: str
    slap_hit_power: int
    charge_hit_power: int
    bunting: int
    slap_contact_size: int
    charge_contact_size: int
    speed: int
    outfield_throwing_speed: int
    fielding: int
    curveball_speed: int
    charge_pitch_speed: int
    curve: int
    stamina: int
    ability: str | None
    pitching_star: str | None
    batting_star: str | None
    good_chemistry: list[str]
    bad_chemistry: list[str]

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> Player:
        return cls(
            player=row["Player"],
            hit_trajectory=row["Hit Trajectory"],
            slap_hit_power=row["Slap Hit Power"],
            charge_hit_power=row["Charge Hit Power"],
            bunting=row["Bunting"],
            slap_contact_size=row["Slap Contact Size"],
            charge_contact_size=row["Charge Contact Size"],
            speed=row["Speed"],
            outfield_throwing_speed=row["Outfield Throwing Speed"],
            fielding=row["Fielding"],
            curveball_speed=row["Curveball Speed"],
            charge_pitch_speed=row["Charge Pitch Speed"],
            curve=row["Curve"],
            stamina=row["Stamina"],
            ability=(row.get("Ability") or "").strip() or None,
            pitching_star=(row.get("Pitching Star") or "").strip() or None,
            batting_star=(row.get("Batting Star") or "").strip() or None,
            good_chemistry=list(row["Good Chemistry"]),
            bad_chemistry=list(row["Bad Chemistry"]),
        )
