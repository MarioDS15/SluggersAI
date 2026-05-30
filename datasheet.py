"""Build CSV datasheets from game and team data collected in startup."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from game import Game, STADIUMS
from synergy import BAD_SYNERGY, GOOD_SYNERGY, NO_SYNERGY
from team import (
    CATCHER,
    CENTER_FIELD,
    FIRST_BASE,
    LEFT_FIELD,
    PITCHER,
    RIGHT_FIELD,
    ROLE_ENCODING,
    SECOND_BASE,
    SHORTSTOP,
    THIRD_BASE,
    Team,
    encode_role,
    relation_key,
    role_one_hot_columns,
)

LINEUP_SIZE = 9

gameCols = [
    "Winner",
    "Team 1 Score",
    "Team 2 Score",
    "Items",
    "Mercy",
    "Innings",
    "Star Power",
]

stadiumCols = list(STADIUMS) + ["Size", "Hazard Level", "Obstacles Level"]

pitcherCols = ["Curveball Speed", "Charge Pitch Speed", "Curve"]

fieldSynergyCols = [
    "Pitch Synergy",
    "1st base synergy",
    "2nd base synergy",
    "3rd base synergy",
    "shortstop synergy",
    "left field synergy",
    "center field synergy",
    "right field synergy",
]

battingCols = [
    "Slap Hit Power",
    "Charge Hit Power",
    "Bunting",
    "Slap Contact Size",
    "Charge Contact Size",
    "Speed",
    "Batting Synergy",
    "Hit Trajectory",
]

fieldingStatCols = ["Fielding", "Outfield Throwing Speed"]

TRAJECTORY_MAP = {"low": 0, "medium": 1, "high": 2}

FIELD_SYNERGY_COLS = {
    "Pitch Synergy": (PITCHER, CATCHER),
    "1st base synergy": (PITCHER, FIRST_BASE),
    "2nd base synergy": (PITCHER, SECOND_BASE),
    "3rd base synergy": (PITCHER, THIRD_BASE),
    "shortstop synergy": (PITCHER, SHORTSTOP),
    "left field synergy": (PITCHER, LEFT_FIELD),
    "center field synergy": (PITCHER, CENTER_FIELD),
    "right field synergy": (PITCHER, RIGHT_FIELD),
}

BATTER_STAT_COLS = battingCols + fieldingStatCols

BATTER_META_COLS = ["Player"]

DEFAULT_OUTPUT = Path(__file__).resolve().parent / "match_datasheet.csv"


def build_all_columns() -> list[str]:
    """Full header: game settings once, then each team's data."""
    columns = list(gameCols) + list(stadiumCols)
    role_cols = role_one_hot_columns()

    for team_num in (1, 2):
        prefix = f"Team {team_num}"
        for col in fieldSynergyCols:
            columns.append(f"{prefix} {col}")
        for col in pitcherCols:
            columns.append(f"{prefix} {col}")
        for slot in range(1, LINEUP_SIZE + 1):
            slot_prefix = f"{prefix} Batter {slot}"
            for col in BATTER_META_COLS:
                columns.append(f"{slot_prefix} {col}")
            for col in role_cols:
                columns.append(f"{slot_prefix} {col}")
            for col in BATTER_STAT_COLS:
                columns.append(f"{slot_prefix} {col}")

    return columns


def get_all_columns() -> list[str]:
    return build_all_columns()


def _on_off(value: bool) -> str:
    return "on" if value else "off"


def _field_synergy_value(team: Team, pos_a: str, pos_b: str) -> int:
    """Field synergy: 1 = good chemistry, 0 = neutral, -1 = bad."""
    value = team.relations.get(relation_key(pos_a, pos_b))
    if value == GOOD_SYNERGY:
        return 1
    if value == BAD_SYNERGY:
        return -1
    return NO_SYNERGY


def _field_position_for_player(team: Team, player_name: str) -> str:
    for role in ROLE_ENCODING:
        fielder = team.positions.get(role)
        if fielder and fielder.get_player() == player_name:
            return role
    return ""


def _prefixed_one_hot(prefix: str, encoding: dict[str, int]) -> dict[str, Any]:
    return {f"{prefix} {col}": value for col, value in encoding.items()}


def build_game_columns(game: Game) -> dict[str, Any]:
    """Game settings — included once per game row."""
    row = {
        "Winner": "",
        "Team 1 Score": "",
        "Team 2 Score": "",
        "Items": _on_off(game.items),
        "Mercy": _on_off(game.mercy_rule),
        "Innings": game.innings,
        "Star Power": _on_off(game.star_power),
    }

    for stadium_name in STADIUMS:
        row[stadium_name] = 1 if game.stadium == stadium_name else 0

    info = game.get_stadium_info()
    row["Size"] = info["size"]
    row["Hazard Level"] = info["hazard"]
    row["Obstacles Level"] = info["obstacles"]
    return row


def build_team_columns(team: Team, team_num: int) -> dict[str, Any]:
    """Team field synergies, pitcher stats, and per-batter player/role + stats."""
    prefix = f"Team {team_num}"
    row: dict[str, Any] = {}

    for col, (pos_a, pos_b) in FIELD_SYNERGY_COLS.items():
        row[f"{prefix} {col}"] = _field_synergy_value(team, pos_a, pos_b)

    pitcher = team.positions.get(PITCHER)
    row[f"{prefix} Curveball Speed"] = pitcher.curveball_speed if pitcher else ""
    row[f"{prefix} Charge Pitch Speed"] = pitcher.charge_pitch_speed if pitcher else ""
    row[f"{prefix} Curve"] = pitcher.curve if pitcher else ""

    for slot in range(1, LINEUP_SIZE + 1):
        slot_prefix = f"{prefix} Batter {slot}"
        if slot > len(team.batting_players):
            row[f"{slot_prefix} Player"] = ""
            for col in role_one_hot_columns():
                row[f"{slot_prefix} {col}"] = 0
            for col in BATTER_STAT_COLS:
                row[f"{slot_prefix} {col}"] = ""
            continue

        batter = team.batting_players[slot - 1]
        name = batter.get_player()
        field_role = _field_position_for_player(team, name)

        row[f"{slot_prefix} Player"] = name
        row.update(_prefixed_one_hot(slot_prefix, encode_role(field_role)))

        row[f"{slot_prefix} Slap Hit Power"] = batter.slap_hit_power
        row[f"{slot_prefix} Charge Hit Power"] = batter.charge_hit_power
        row[f"{slot_prefix} Bunting"] = batter.bunting
        row[f"{slot_prefix} Slap Contact Size"] = batter.slap_contact_size
        row[f"{slot_prefix} Charge Contact Size"] = batter.charge_contact_size
        row[f"{slot_prefix} Speed"] = batter.speed

        link_index = slot - 1
        row[f"{slot_prefix} Batting Synergy"] = (
            team.batting_synergy[link_index]
            if link_index < len(team.batting_synergy)
            else False
        )

        trajectory = batter.hit_trajectory.strip().lower()
        row[f"{slot_prefix} Hit Trajectory"] = TRAJECTORY_MAP.get(trajectory, 1)

        row[f"{slot_prefix} Fielding"] = batter.fielding if field_role else ""
        row[f"{slot_prefix} Outfield Throwing Speed"] = (
            batter.outfield_throwing_speed if field_role else ""
        )

    return row


def build_match_row(
    teams: list[tuple[str, Team]],
    game: Game,
) -> dict[str, Any]:
    """One CSV row for a full game."""
    row = {col: "" for col in get_all_columns()}
    row.update(build_game_columns(game))

    for team_num, (_, team) in enumerate(teams, start=1):
        if team_num > 2:
            break
        row.update(build_team_columns(team, team_num))

    return row


def build_match_rows(
    teams: list[tuple[str, Team]],
    game: Game,
) -> list[dict[str, Any]]:
    """One entry per game."""
    return [build_match_row(teams, game)]


def rows_to_sheet_data(rows: list[dict[str, Any]]) -> tuple[list[str], list[list[Any]]]:
    headers = get_all_columns()
    body = [[row.get(col, "") for col in headers] for row in rows]
    return headers, body


def create_match_sheet(
    teams: list[tuple[str, Team]],
    game: Game,
    output_path: Path | str = DEFAULT_OUTPUT,
    append: bool = True,
) -> Path:
    """Write one game per row. Game settings appear once; team data is prefixed."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    row = build_match_row(teams, game)
    headers = get_all_columns()
    body = [row.get(col, "") for col in headers]

    file_exists = path.exists() and path.stat().st_size > 0

    with path.open("a" if append and file_exists else "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not (append and file_exists):
            writer.writerow(headers)
        writer.writerow(body)

    return path


create_csv_sheet = create_match_sheet
