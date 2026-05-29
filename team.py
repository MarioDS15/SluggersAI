"""Team lineup: batting order and defensive positions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from player import Player

# Standard defensive positions (keys for defensive_lineup)
PITCHER = "pitcher"
CATCHER = "catcher"
FIRST_BASE = "1st_base"
SECOND_BASE = "2nd_base"
THIRD_BASE = "3rd_base"
SHORTSTOP = "shortstop"
LEFT_FIELD = "left_field"
CENTER_FIELD = "center_field"
RIGHT_FIELD = "right_field"

DEFENSIVE_POSITIONS = (
    PITCHER,
    CATCHER,
    FIRST_BASE,
    SECOND_BASE,
    THIRD_BASE,
    SHORTSTOP,
    LEFT_FIELD,
    CENTER_FIELD,
    RIGHT_FIELD,
)


@dataclass
class Team:
    """A team with a batting order and a defensive lineup by position."""

    batting_players: list[Player] = field(default_factory=list)
    defensive_lineup: dict[str, Player] = field(default_factory=dict)

    def get_batting_players(self) -> list[Player]:
        return list(self.batting_players)

    def get_defensive_lineup(self) -> dict[str, Player]:
        return dict(self.defensive_lineup)

    def get_player_at(self, position: str) -> Player | None:
        return self.defensive_lineup.get(position)

    def set_defensive_position(self, position: str, player: Player) -> None:
        self.defensive_lineup[position] = player

    def to_dict(self) -> dict[str, Any]:
        return {
            "batting_players": [p.get_player() for p in self.batting_players],
            "defensive_lineup": {
                pos: p.get_player() for pos, p in self.defensive_lineup.items()
            },
        }

    def format_summary(self, team_name: str = "Team") -> str:
        """Human-readable batting order and defensive lineup."""
        lines = [f"=== {team_name} ===", "", "Batting order:"]
        for i, player in enumerate(self.batting_players, start=1):
            lines.append(f"  {i}. {player.get_player()}")
        lines.append("")
        lines.append("Defensive lineup:")
        for position in DEFENSIVE_POSITIONS:
            player = self.defensive_lineup.get(position)
            label = position.replace("_", " ").title()
            name = player.get_player() if player else "(empty)"
            lines.append(f"  {label}: {name}")
        return "\n".join(lines)
