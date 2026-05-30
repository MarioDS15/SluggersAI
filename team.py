"""Team lineup: batting order, defensive positions, and position-pair relations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from player import Player as RosterPlayer

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

POSITION_LABELS = {
    PITCHER: "Pitcher",
    CATCHER: "Catcher",
    FIRST_BASE: "1st Base",
    SECOND_BASE: "2nd Base",
    THIRD_BASE: "3rd Base",
    SHORTSTOP: "Shortstop",
    LEFT_FIELD: "Left Field",
    CENTER_FIELD: "Center Field",
    RIGHT_FIELD: "Right Field",
}

# Defensive roles for one-hot encoding (same order as DEFENSIVE_POSITIONS)
ROLE_ENCODING: tuple[str, ...] = DEFENSIVE_POSITIONS


def role_one_hot_columns() -> list[str]:
    """Column names: role_<position_key> for each defensive role."""
    return [f"role_{role}" for role in ROLE_ENCODING]


def encode_role(role: str) -> dict[str, int]:
    """One-hot encode a defensive role. Empty role string yields all zeros."""
    columns = {col: 0 for col in role_one_hot_columns()}
    if role and role in ROLE_ENCODING:
        columns[f"role_{role}"] = 1
    return columns


def role_encoding_index(role: str) -> int | None:
    """Index of a role in ROLE_ENCODING, or None if unknown."""
    if role not in ROLE_ENCODING:
        return None
    return ROLE_ENCODING.index(role)


def relation_key(position_a: str, position_b: str) -> str:
    """Canonical relation key: earlier position first, e.g. 'pitcher to catcher'."""
    if position_a not in DEFENSIVE_POSITIONS or position_b not in DEFENSIVE_POSITIONS:
        raise ValueError(f"Invalid position pair: {position_a!r}, {position_b!r}")
    if position_a == position_b:
        raise ValueError("Cannot create a relation from a position to itself")
    first, second = (
        (position_a, position_b)
        if DEFENSIVE_POSITIONS.index(position_a)
        < DEFENSIVE_POSITIONS.index(position_b)
        else (position_b, position_a)
    )
    return f"{first} to {second}"


def all_relation_keys() -> tuple[str, ...]:
    """Every possible position-pair relation (36 for 9 field positions)."""
    keys: list[str] = []
    for i, pos_a in enumerate(DEFENSIVE_POSITIONS):
        for pos_b in DEFENSIVE_POSITIONS[i + 1 :]:
            keys.append(relation_key(pos_a, pos_b))
    return tuple(keys)


ALL_RELATION_KEYS = all_relation_keys()


def empty_positions() -> dict[str, None]:
    return {position: None for position in DEFENSIVE_POSITIONS}


def empty_relations() -> dict[str, None]:
    return {key: None for key in ALL_RELATION_KEYS}


def parse_relation_key(key: str) -> tuple[str, str]:
    """Split 'pitcher to catcher' into ('pitcher', 'catcher')."""
    if key not in ALL_RELATION_KEYS:
        raise ValueError(f"Unknown relation: {key!r}")
    left, _, right = key.partition(" to ")
    return left, right


@dataclass
class Team:
    """A team with batting order, defensive positions, and pairwise relations."""

    number: int
    batting_players: list[Team.Player] = field(default_factory=list)
    positions: dict[str, Team.Player | None] = field(default_factory=empty_positions)
    relations: dict[str, int | None] = field(default_factory=empty_relations)
    synergy_links: dict[str, list[str]] = field(default_factory=dict)
    batting_synergy: list[bool] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.number not in (1, 2):
            raise ValueError(f"team number must be 1 or 2, got {self.number}")
        for position in DEFENSIVE_POSITIONS:
            if position not in self.positions:
                self.positions[position] = None
        for key in ALL_RELATION_KEYS:
            if key not in self.relations:
                self.relations[key] = None

    @dataclass
    class Player:
        """A player on a team lineup; references teammates through the parent Team."""

        team: Team = field(repr=False, compare=False)
        stats: RosterPlayer = field(repr=False, compare=False)

        @classmethod
        def from_roster(cls, team: Team, roster_player: RosterPlayer) -> Team.Player:
            return cls(team=team, stats=roster_player)

        def get_player(self) -> str:
            return self.stats.get_player()

        def get_team_number(self) -> int:
            return self.team.number

        def get_teammates(self) -> list[Team.Player]:
            self_name = self.get_player()
            return [
                p
                for p in self.team.get_all_players()
                if p.get_player() != self_name
            ]

        def has_good_chemistry_with(self, other: Team.Player) -> bool:
            return other.get_player() in self.stats.good_chemistry

        def has_bad_chemistry_with(self, other: Team.Player) -> bool:
            return other.get_player() in self.stats.bad_chemistry

        def __getattr__(self, name: str) -> Any:
            return getattr(self.stats, name)

    def get_all_players(self, exclude: Team.Player | None = None) -> list[Team.Player]:
        seen: dict[str, Team.Player] = {}
        for player in self.batting_players:
            seen[player.get_player()] = player
        for player in self.positions.values():
            if player is not None:
                seen[player.get_player()] = player
        players = list(seen.values())
        if exclude is not None:
            players = [p for p in players if p is not exclude]
        return players

    def get_batting_players(self) -> list[Team.Player]:
        return list(self.batting_players)

    def get_positions(self) -> dict[str, Team.Player | None]:
        return dict(self.positions)

    def get_relations(self) -> dict[str, int | None]:
        return dict(self.relations)

    def get_player_at(self, position: str) -> Team.Player | None:
        if position not in DEFENSIVE_POSITIONS:
            raise ValueError(f"Unknown position: {position!r}")
        return self.positions[position]

    def set_position(self, position: str, player: Team.Player) -> None:
        if position not in DEFENSIVE_POSITIONS:
            raise ValueError(f"Unknown position: {position!r}")
        self.positions[position] = player

    def clear_position(self, position: str) -> None:
        if position not in DEFENSIVE_POSITIONS:
            raise ValueError(f"Unknown position: {position!r}")
        self.positions[position] = None

    def get_relation(self, position_a: str, position_b: str) -> int | None:
        return self.relations[relation_key(position_a, position_b)]

    def update_relations(self) -> None:
        from synergy import update_field_relations

        update_field_relations(self)

    def update_batting_synergy(self) -> None:
        from synergy import update_batting_synergy

        update_batting_synergy(self)

    def update_synergy(self) -> None:
        from synergy import update_team_synergy

        update_team_synergy(self)

    def to_dict(self) -> dict[str, Any]:
        return {
            "team": self.number,
            "batting_players": [p.get_player() for p in self.batting_players],
            "positions": {
                pos: p.get_player() if p else None
                for pos, p in self.positions.items()
            },
            "relations": dict(self.relations),
        }

    def format_summary(self, team_name: str = "Team") -> str:
        lines = [f"=== {team_name} ===", "", "Batting order:"]
        for i, player in enumerate(self.batting_players, start=1):
            lines.append(f"  {i}. {player.get_player()} (team {self.number})")
        lines.append("")
        lines.append("Positions:")
        for position in DEFENSIVE_POSITIONS:
            player = self.positions[position]
            label = POSITION_LABELS[position]
            name = (
                f"{player.get_player()} (team {self.number})"
                if player
                else "(empty)"
            )
            lines.append(f"  {label}: {name}")
        lines.append("")
        from synergy import batting_synergy_label, link_label

        lines.append("Fielding relations:")
        for key in ALL_RELATION_KEYS:
            pos_a, pos_b = parse_relation_key(key)
            label_a = POSITION_LABELS[pos_a]
            label_b = POSITION_LABELS[pos_b]
            lines.append(
                f"  {label_a} to {label_b}: {link_label(self.relations[key])}"
            )
        lines.append("")
        lines.append("Batting synergy (to next batter):")
        for i, player in enumerate(self.batting_players):
            next_name = (
                self.batting_players[i + 1].get_player()
                if i + 1 < len(self.batting_players)
                else self.batting_players[0].get_player()
            )
            has_synergy = self.batting_synergy[i] if i < len(self.batting_synergy) else None
            lines.append(
                f"  {player.get_player()} → {next_name}: {batting_synergy_label(has_synergy)}"
            )
        return "\n".join(lines)
