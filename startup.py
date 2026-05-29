"""Load players from CSV and run interactive team setup on startup."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from player import Player
from team import DEFENSIVE_POSITIONS, Team

CSV_PATH = Path(__file__).resolve().parent / "sluggers_chemistry - Modded Stats.csv"
LINEUP_SIZE = 9

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

_POSITION_LABELS = {
    "pitcher": "Pitcher",
    "catcher": "Catcher",
    "1st_base": "1st Base",
    "2nd_base": "2nd Base",
    "3rd_base": "3rd Base",
    "shortstop": "Shortstop",
    "left_field": "Left Field",
    "center_field": "Center Field",
    "right_field": "Right Field",
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


def _prompt_player(players: dict[str, Player], prompt: str) -> Player:
    while True:
        name = input(prompt).strip()
        player = _lookup_player(name, players)
        if player:
            return player
        print(f"  Player not found: {name!r}. Try again.")


def _prompt_batting_order(players: dict[str, Player]) -> list[Player]:
    print(f"\nEnter your batting order ({LINEUP_SIZE} batters).")
    batting: list[Player] = []
    for slot in range(1, LINEUP_SIZE + 1):
        player = _prompt_player(players, f"  Batter {slot}: ")
        batting.append(player)
    return batting


def _prompt_defensive_lineup(players: dict[str, Player]) -> dict[str, Player]:
    print(f"\nEnter your defensive lineup ({LINEUP_SIZE} positions).")
    defense: dict[str, Player] = {}
    for position in DEFENSIVE_POSITIONS:
        label = _POSITION_LABELS[position]
        player = _prompt_player(players, f"  {label}: ")
        defense[position] = player
    return defense


def _prompt_team(players: dict[str, Player], default_name: str) -> tuple[str, Team]:
    name = input(f"\nTeam name [{default_name}]: ").strip() or default_name
    batting = _prompt_batting_order(players)
    defense = _prompt_defensive_lineup(players)
    return name, Team(batting_players=batting, defensive_lineup=defense)


def _prompt_yes_no(prompt: str) -> bool:
    while True:
        answer = input(prompt).strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("  Please enter y or n.")


def run_team_setup() -> list[tuple[str, Team]]:
    """Prompt for one or more teams and return (name, team) pairs."""
    print(f"Loaded {len(PLAYERS)} players from roster.\n")
    teams: list[tuple[str, Team]] = []

    team_number = 1
    while True:
        default_name = f"Team {team_number}"
        print(f"--- Building {default_name} ---")
        teams.append(_prompt_team(PLAYERS, default_name))
        team_number += 1

        if not _prompt_yes_no("\nAdd another team? (y/n): "):
            break

    return teams


def print_teams_verification(teams: list[tuple[str, Team]]) -> None:
    print("\n" + "=" * 40)
    print("LINEUP VERIFICATION")
    print("=" * 40)
    for name, team in teams:
        print()
        print(team.format_summary(name))
    print(f"\n{len(teams)} team(s) configured.")


if __name__ == "__main__":
    configured_teams = run_team_setup()
    print_teams_verification(configured_teams)
