"""Load players from CSV and run interactive team setup on startup."""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

from player import Player
from team import DEFENSIVE_POSITIONS, POSITION_LABELS, Team

TeamPlayer = Team.Player

CSV_PATH = Path(__file__).resolve().parent / "sluggers_chemistry - Modded Stats.csv"
LINEUP_SIZE = 9
NUM_TEAMS = 2
TEAM_NAMES = ("Team 1", "Team 2")

# ---------------------------------------------------------------------------
# Edit TEAM_CONFIG for both teams (leave blank to enter lineups interactively).
#
# Exactly two blocks: [Team 1] then [Team 2]
#   batting: 9 players, comma-separated (batting order)
#   pitcher, catcher, 1st_base, 2nd_base, 3rd_base, shortstop,
#   left_field, center_field, right_field: one player each
#
# Lines starting with # are ignored.
# ---------------------------------------------------------------------------
TEAM_CONFIG = """
[Team 1]
batting: Mario, Luigi, Daisy, Peach, Yoshi, Toadette, Bowser, Wario, Waluigi
pitcher: Peach
catcher: Luigi
1st_base: Mario
2nd_base: Daisy
3rd_base: Bowser
shortstop: Waluigi
left_field: Yoshi
center_field: Toadette
right_field: Wario

[Team 2]
batting: Donkey Kong, Diddy Kong, Dixie Kong, Funky Kong, Tiny Kong, Baby DK, Kritter, King K. Rool, Birdo
pitcher: King K. Rool
catcher: Kritter
1st_base: Donkey Kong
2nd_base: Diddy Kong
3rd_base: Dixie Kong
shortstop: Funky Kong
left_field: Tiny Kong
center_field: Baby DK
right_field: Birdo
"""

STAT_HEADERS = [
    "Player",
    "Hit Trajectory",
    "Slap Hit Power",
    "Charge Hit Power",
    "Bunting",
    "Slap Contact Size",
    "Charge Contact Size",
    "Speed",
    "Outfield Throwing Speed",
    "Fielding",
    "Curveball Speed",
    "Charge Pitch Speed",
    "Curve",
    "Stamina",
    "Ability",
    "Good Chemistry",
    "Bad Chemistry",
]

_INT_HEADERS = {
    "Slap Hit Power",
    "Charge Hit Power",
    "Bunting",
    "Slap Contact Size",
    "Charge Contact Size",
    "Speed",
    "Outfield Throwing Speed",
    "Fielding",
    "Curveball Speed",
    "Charge Pitch Speed",
    "Curve",
    "Stamina",
}

_POSITION_ALIASES: dict[str, str] = {
    "pitcher": "pitcher",
    "catcher": "catcher",
    "1st_base": "1st_base",
    "1st base": "1st_base",
    "2nd_base": "2nd_base",
    "2nd base": "2nd_base",
    "3rd_base": "3rd_base",
    "3rd base": "3rd_base",
    "shortstop": "shortstop",
    "left_field": "left_field",
    "left field": "left_field",
    "center_field": "center_field",
    "center field": "center_field",
    "right_field": "right_field",
    "right field": "right_field",
}


def _parse_chemistry(value: str) -> list[str]:
    if not value.strip():
        return []
    return [name.strip() for name in value.split(",") if name.strip()]


def _parse_row(row: list[str]) -> dict[str, Any]:
    raw = {header: row[i].strip() for i, header in enumerate(STAT_HEADERS)}
    stats: dict[str, Any] = {"Player": raw["Player"]}

    for header in STAT_HEADERS[1:]:
        value = raw[header]
        if header in _INT_HEADERS:
            stats[header] = int(value)
        elif header in ("Good Chemistry", "Bad Chemistry"):
            stats[header] = _parse_chemistry(value)
        elif header == "Ability":
            stats[header] = value or None
        else:
            stats[header] = value

    return stats


def load_all_players() -> dict[str, Player]:
    """Load every character from the CSV into a dict keyed by player name."""
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    data_rows = rows[2:] if rows and rows[0][0] == "Player Info" else rows[1:]
    players: dict[str, Player] = {}
    for row in data_rows:
        if not row or not row[0].strip():
            continue
        player = Player.from_row(_parse_row(row))
        players[player.player] = player
    return players


PLAYERS: dict[str, Player] = load_all_players()

def _lookup_player(name: str, players: dict[str, Player]) -> Player | None:
    key = name.strip()
    if not key:
        return None
    if key in players:
        return players[key]
    by_folded = {n.casefold(): p for n, p in players.items()}
    return by_folded.get(key.casefold())


def _require_player(
    name: str,
    players: dict[str, Player],
    team_name: str,
    field: str,
    team: Team,
) -> TeamPlayer:
    roster_player = _lookup_player(name, players)
    if roster_player is None:
        raise ValueError(f"[{team_name}] {field}: player not found: {name!r}")
    return TeamPlayer.from_roster(team, roster_player)


def _build_team_from_data(
    team_name: str,
    data: dict[str, str],
    players: dict[str, Player],
    team_number: int,
) -> Team:
    team = Team(number=team_number)
    if "batting" not in data:
        raise ValueError(f"[{team_name}] missing 'batting:' line")

    batter_names = [n.strip() for n in data["batting"].split(",") if n.strip()]
    if len(batter_names) != LINEUP_SIZE:
        raise ValueError(
            f"[{team_name}] batting must have {LINEUP_SIZE} players, got {len(batter_names)}"
        )

    batting = [
        _require_player(name, players, team_name, f"batter {i + 1}", team)
        for i, name in enumerate(batter_names)
    ]

    defense: dict[str, TeamPlayer] = {}
    for position in DEFENSIVE_POSITIONS:
        if position not in data:
            label = POSITION_LABELS[position]
            raise ValueError(f"[{team_name}] missing defensive position: {label}")
        defense[position] = _require_player(
            data[position],
            players,
            team_name,
            POSITION_LABELS[position],
            team,
        )

    team.batting_players = batting
    for position, player in defense.items():
        team.set_position(position, player)
    team.update_synergy()
    return team


def parse_teams_from_config(
    config: str, players: dict[str, Player]
) -> list[tuple[str, Team]]:
    """Parse TEAM_CONFIG into exactly two teams: Team 1 and Team 2."""
    config = config.strip()
    if not config:
        return []

    team_data: list[dict[str, str]] = []
    current_data: dict[str, str] | None = None

    for line in config.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if re.match(r"^\[.+\]$", line):
            if current_data is not None:
                team_data.append(current_data)
            current_data = {}
            continue

        if current_data is None:
            raise ValueError("TEAM_CONFIG must start with [Team 1]")

        key, _, value = line.partition(":")
        if not value.strip():
            team_label = TEAM_NAMES[len(team_data)] if len(team_data) < NUM_TEAMS else "Team"
            raise ValueError(f"[{team_label}] empty value for {key!r}")

        normalized_key = _POSITION_ALIASES.get(key.strip().lower(), key.strip().lower())
        current_data[normalized_key] = value.strip()

    if current_data is not None:
        team_data.append(current_data)

    if len(team_data) != NUM_TEAMS:
        raise ValueError(
            f"TEAM_CONFIG must define exactly {NUM_TEAMS} teams, found {len(team_data)}"
        )

    return [
        (
            TEAM_NAMES[i],
            _build_team_from_data(TEAM_NAMES[i], team_data[i], players, i + 1),
        )
        for i in range(NUM_TEAMS)
    ]


def _prompt_player(players: dict[str, Player], prompt: str, team: Team) -> TeamPlayer:
    while True:
        name = input(prompt).strip()
        roster_player = _lookup_player(name, players)
        if roster_player:
            return TeamPlayer.from_roster(team, roster_player)
        print(f"  Player not found: {name!r}. Try again.")


def _prompt_batting_order(players: dict[str, Player], team: Team) -> list[TeamPlayer]:
    print(f"\nEnter your batting order ({LINEUP_SIZE} batters).")
    batting: list[TeamPlayer] = []
    for slot in range(1, LINEUP_SIZE + 1):
        player = _prompt_player(players, f"  Batter {slot}: ", team)
        batting.append(player)
    return batting


def _prompt_defensive_lineup(
    players: dict[str, Player], team: Team
) -> dict[str, TeamPlayer]:
    print(f"\nEnter your defensive lineup ({LINEUP_SIZE} positions).")
    defense: dict[str, TeamPlayer] = {}
    for position in DEFENSIVE_POSITIONS:
        label = POSITION_LABELS[position]
        player = _prompt_player(players, f"  {label}: ", team)
        defense[position] = player
    return defense


def _prompt_team(players: dict[str, Player], team_number: int) -> Team:
    team = Team(number=team_number)
    team.batting_players = _prompt_batting_order(players, team)
    for position, player in _prompt_defensive_lineup(players, team).items():
        team.set_position(position, player)
    team.update_synergy()
    return team


def load_teams() -> list[tuple[str, Team]]:
    """Load Team 1 and Team 2 from TEAM_CONFIG or interactive prompts."""
    print(f"Loaded {len(PLAYERS)} players from roster.\n")
    if TEAM_CONFIG.strip():
        teams = parse_teams_from_config(TEAM_CONFIG, PLAYERS)
        print("Loaded Team 1 and Team 2 from TEAM_CONFIG.")
        return teams
    return run_team_setup()


def run_team_setup() -> list[tuple[str, Team]]:
    """Prompt for Team 1 and Team 2 lineups."""
    teams: list[tuple[str, Team]] = []
    for i, name in enumerate(TEAM_NAMES):
        print(f"--- {name} ---")
        teams.append((name, _prompt_team(PLAYERS, i + 1)))
    return teams


def print_teams_verification(teams: list[tuple[str, Team]]) -> None:
    print("\n" + "=" * 40)
    print("LINEUP VERIFICATION")
    print("=" * 40)
    for name, team in teams:
        print()
        print(team.format_summary(name))
    print("\n2 teams configured.")


if __name__ == "__main__":
    configured_teams = load_teams()
    print_teams_verification(configured_teams)
