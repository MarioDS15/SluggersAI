"""Player stats from CSV (roster templates, not tied to a team)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Canonical player list for one-hot encoding (filled by register_player_encoding)
PLAYER_ENCODING: tuple[str, ...] = ()


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
            ability=row["Ability"],
            good_chemistry=list(row["Good Chemistry"]),
            bad_chemistry=list(row["Bad Chemistry"]),
        )

    def get_player(self) -> str:
        return self.player

    def get_hit_trajectory(self) -> str:
        return self.hit_trajectory

    def get_slap_hit_power(self) -> int:
        return self.slap_hit_power

    def get_charge_hit_power(self) -> int:
        return self.charge_hit_power

    def get_bunting(self) -> int:
        return self.bunting

    def get_slap_contact_size(self) -> int:
        return self.slap_contact_size

    def get_charge_contact_size(self) -> int:
        return self.charge_contact_size

    def get_speed(self) -> int:
        return self.speed

    def get_outfield_throwing_speed(self) -> int:
        return self.outfield_throwing_speed

    def get_fielding(self) -> int:
        return self.fielding

    def get_curveball_speed(self) -> int:
        return self.curveball_speed

    def get_charge_pitch_speed(self) -> int:
        return self.charge_pitch_speed

    def get_curve(self) -> int:
        return self.curve

    def get_stamina(self) -> int:
        return self.stamina

    def get_ability(self) -> str | None:
        return self.ability

    def get_good_chemistry(self) -> list[str]:
        return list(self.good_chemistry)

    def get_bad_chemistry(self) -> list[str]:
        return list(self.bad_chemistry)

    def to_dict(self) -> dict[str, Any]:
        """All stats using exact stat-sheet column names."""
        return {
            "Player": self.get_player(),
            "Hit Trajectory": self.get_hit_trajectory(),
            "Slap Hit Power": self.get_slap_hit_power(),
            "Charge Hit Power": self.get_charge_hit_power(),
            "Bunting": self.get_bunting(),
            "Slap Contact Size": self.get_slap_contact_size(),
            "Charge Contact Size": self.get_charge_contact_size(),
            "Speed": self.get_speed(),
            "Outfield Throwing Speed": self.get_outfield_throwing_speed(),
            "Fielding": self.get_fielding(),
            "Curveball Speed": self.get_curveball_speed(),
            "Charge Pitch Speed": self.get_charge_pitch_speed(),
            "Curve": self.get_curve(),
            "Stamina": self.get_stamina(),
            "Ability": self.get_ability(),
            "Good Chemistry": self.get_good_chemistry(),
            "Bad Chemistry": self.get_bad_chemistry(),
        }


def register_player_encoding(player_names: list[str]) -> None:
    """Set the ordered player list used for one-hot columns (call after roster load)."""
    global PLAYER_ENCODING
    PLAYER_ENCODING = tuple(sorted(player_names))


def player_one_hot_columns() -> list[str]:
    """Column names: player_<name> for each character in PLAYER_ENCODING."""
    return [f"player_{name}" for name in PLAYER_ENCODING]


def encode_player(name: str) -> dict[str, int]:
    """One-hot encode a player name. All keys are 0 except the matching player."""
    columns = {col: 0 for col in player_one_hot_columns()}
    key = f"player_{name}"
    if key in columns:
        columns[key] = 1
    return columns


def player_encoding_index(name: str) -> int | None:
    """Index of a player in PLAYER_ENCODING, or None if unknown."""
    try:
        return PLAYER_ENCODING.index(name)
    except ValueError:
        return None
