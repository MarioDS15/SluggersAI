"""Load players from CSV and run team / game setup (JSON or interactive)."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from Data.datasheet import (
    DEFAULT_OUTPUT,
    create_results_csv,
    register_encodings_from_roster,
)
from Data.game import Game, game_from_config, print_game_verification, setup_game
from Data.player import Player
from Data.team import DEFENSIVE_POSITIONS, POSITION_LABELS, Team

ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "Data"
CONFIG_PATH = ROOT_DIR / "config.json"

TeamPlayer = Team.Player

CSV_PATH = DATA_DIR / "PlayerStats.csv"
LINEUP_SIZE = 9
NUM_TEAMS = 2
TEAM_NAMES = ("Team 1", "Team 2")

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
    "Pitching Star",
    "Batting Star",
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
        elif header in ("Ability", "Pitching Star", "Batting Star"):
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
register_encodings_from_roster(PLAYERS)


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
    data: dict[str, Any],
    players: dict[str, Player],
    team_number: int,
) -> Team:
    team = Team(number=team_number)
    if "batting" not in data:
        raise ValueError(f"[{team_name}] missing batting order")

    if isinstance(data["batting"], list):
        batter_names = [str(n).strip() for n in data["batting"] if str(n).strip()]
    else:
        batter_names = [n.strip() for n in str(data["batting"]).split(",") if n.strip()]

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
            str(data[position]),
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


def _team_entry_to_data(entry: dict[str, Any]) -> dict[str, Any]:
    """Convert one JSON team object into internal position map."""
    data: dict[str, Any] = {}

    batting = entry.get("batting", [])
    if isinstance(batting, list):
        data["batting"] = batting
    else:
        data["batting"] = str(batting)

    defense = entry.get("defense", {})
    if not isinstance(defense, dict):
        raise ValueError("team 'defense' must be an object")

    for key, value in defense.items():
        normalized = _POSITION_ALIASES.get(str(key).strip().lower(), str(key).strip().lower())
        data[normalized] = str(value).strip()

    return data


def load_json_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def parse_teams_from_json(
    config: dict[str, Any], players: dict[str, Player]
) -> list[tuple[str, Team]]:
    """Parse config.json 'teams' into two Team objects."""
    teams_cfg = config.get("teams")
    if not isinstance(teams_cfg, list) or len(teams_cfg) != NUM_TEAMS:
        raise ValueError(f"config must have exactly {NUM_TEAMS} teams")

    result: list[tuple[str, Team]] = []
    for i, entry in enumerate(teams_cfg):
        team_name = entry.get("name", TEAM_NAMES[i])
        team_data = _team_entry_to_data(entry)
        result.append(
            (
                str(team_name),
                _build_team_from_data(str(team_name), team_data, players, i + 1),
            )
        )
    return result


def _prompt_yes_no(prompt: str) -> bool:
    while True:
        answer = input(prompt).strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("  Enter y/yes or n/no.")


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


def run_team_setup() -> list[tuple[str, Team]]:
    """Prompt for Team 1 and Team 2 lineups."""
    teams: list[tuple[str, Team]] = []
    for i, name in enumerate(TEAM_NAMES):
        print(f"--- {name} ---")
        teams.append((name, _prompt_team(PLAYERS, i + 1)))
    return teams


def load_setup_from_json() -> tuple[list[tuple[str, Team]], Game]:
    config = load_json_config()
    teams = parse_teams_from_json(config, PLAYERS)
    game_cfg = config.get("game")
    if not isinstance(game_cfg, dict):
        raise ValueError("config.json must include a 'game' object")
    game = game_from_config(game_cfg, teams)
    return teams, game


def load_setup_interactive() -> tuple[list[tuple[str, Team]], Game]:
    teams = run_team_setup()
    game = setup_game(teams)
    return teams, game


def print_teams_verification(teams: list[tuple[str, Team]]) -> None:
    print("\n" + "=" * 40)
    print("LINEUP VERIFICATION")
    print("=" * 40)
    for name, team in teams:
        print()
        print(team.format_summary(name))
    print("\n2 teams configured.")


def run_results_export() -> None:
    """Load lineups and game settings, then write Data/results.csv."""
    print(f"Loaded {len(PLAYERS)} players from roster.\n")

    if _prompt_yes_no(f"Use lineup and game settings from {CONFIG_PATH.name}? (y/n): "):
        print(f"Loading from {CONFIG_PATH}...")
        teams, game = load_setup_from_json()
    else:
        print("Entering interactive setup...")
        teams, game = load_setup_interactive()

    print_teams_verification(teams)
    print_game_verification(game)

    if DEFAULT_OUTPUT.exists():
        DEFAULT_OUTPUT.unlink()

    path = create_results_csv(teams, game, append=False)
    print(f"\nResults written to: {path}")


if __name__ == "__main__":
    run_results_export()
