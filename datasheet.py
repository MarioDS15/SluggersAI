"""Build CSV datasheets from game and team data collected in startup."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import TYPE_CHECKING, Any

from game import Game, STADIUMS
from synergy import BAD_SYNERGY, GOOD_SYNERGY, NO_SYNERGY

if TYPE_CHECKING:
    from player import Player

# --- One-hot encoding: constants (start) ---

ABILITY_ENCODING: tuple[str, ...] = ()

PITCHING_STAR_SKILLS: tuple[str, ...] = (
    "Barrel Ball",
    "Banana Ball",
    "Breaking Ball",
    "Change-Up",
    "Fastball",
    "Fireball",
    "Flower Ball",
    "Graffiti Ball",
    "Heart Ball",
    "Killer Ball",
    "Liar Ball",
    "Phony Ball",
    "Rainbow Ball",
    "Suction Ball",
    "Tornado Ball",
)

BATTING_STAR_SKILLS: tuple[str, ...] = (
    "Banana Swing",
    "Barrel Swing",
    "Breath Swing",
    "Cannon Swing",
    "Egg Swing",
    "Fire Swing",
    "Flower Swing",
    "Fly Ball",
    "Graffiti Swing",
    "Ground Ball",
    "Heart Swing",
    "Liar Swing",
    "Line Drive",
    "Phony Swing",
    "Tornado Swing",
)

PITCHING_STAR_ENCODING: tuple[str, ...] = ()
BATTING_STAR_ENCODING: tuple[str, ...] = ()

# --- One-hot encoding: constants (end) ---

# --- One-hot encoding: registration (start) ---


def register_ability_encoding(abilities: list[str]) -> None:
    """Set the ordered ability list used for one-hot columns (call after roster load)."""
    global ABILITY_ENCODING
    unique = sorted({a.strip() for a in abilities if a and a.strip()})
    ABILITY_ENCODING = tuple(unique)


def register_pitching_star_encoding(stars: list[str]) -> None:
    """Set pitching star list for one-hot columns (merges with PITCHING_STAR_SKILLS)."""
    global PITCHING_STAR_ENCODING
    from_csv = {s.strip() for s in stars if s and s.strip()}
    merged = sorted(from_csv | set(PITCHING_STAR_SKILLS))
    PITCHING_STAR_ENCODING = tuple(merged)


def register_batting_star_encoding(stars: list[str]) -> None:
    """Set batting star list for one-hot columns (merges with BATTING_STAR_SKILLS)."""
    global BATTING_STAR_ENCODING
    from_csv = {s.strip() for s in stars if s and s.strip()}
    merged = sorted(from_csv | set(BATTING_STAR_SKILLS))
    BATTING_STAR_ENCODING = tuple(merged)


def register_encodings_from_roster(players: dict[str, Player]) -> None:
    """Initialize all one-hot column encodings from loaded roster data."""
    register_ability_encoding([p.ability for p in players.values() if p.ability])
    register_pitching_star_encoding(
        [p.pitching_star for p in players.values() if p.pitching_star]
    )
    register_batting_star_encoding(
        [p.batting_star for p in players.values() if p.batting_star]
    )

# --- One-hot encoding: registration (end) ---

# --- One-hot encoding: columns & encode (start) ---


def ability_one_hot_columns() -> list[str]:
    return [f"ability {name}" for name in ABILITY_ENCODING]


def pitching_star_one_hot_columns() -> list[str]:
    return [f"pitching star {name}" for name in PITCHING_STAR_ENCODING]


def batting_star_one_hot_columns() -> list[str]:
    return [f"batting star {name}" for name in BATTING_STAR_ENCODING]


def encode_ability(ability: str | None) -> dict[str, int]:
    columns = {col: 0 for col in ability_one_hot_columns()}
    if ability and ability in ABILITY_ENCODING:
        columns[f"ability {ability}"] = 1
    return columns


def encode_pitching_star(star: str | None) -> dict[str, int]:
    columns = {col: 0 for col in pitching_star_one_hot_columns()}
    if star and star in PITCHING_STAR_ENCODING:
        columns[f"pitching star {star}"] = 1
    return columns


def encode_batting_star(star: str | None) -> dict[str, int]:
    columns = {col: 0 for col in batting_star_one_hot_columns()}
    if star and star in BATTING_STAR_ENCODING:
        columns[f"batting star {star}"] = 1
    return columns

# --- One-hot encoding: columns & encode (end) ---

# --- Match row builders (start) ---
from team import (
    CATCHER,
    CENTER_FIELD,
    FIRST_BASE,
    LEFT_FIELD,
    PITCHER,
    RIGHT_FIELD,
    SECOND_BASE,
    SHORTSTOP,
    THIRD_BASE,
    Team,
    relation_key,
)

LINEUP_SIZE = 9

# --- Column definitions: game & stadium (start) ---

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

# --- Column definitions: game & stadium (end) ---

# --- Column definitions: pitching & synergies (start) ---

pitcherCols = ["Curveball Speed", "Charge Pitch Speed", "Curve", "Captain"]

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

# --- Column definitions: pitching & synergies (end) ---

# --- Column definitions: batting & fielding (start) ---

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

# --- Column definitions: batting & fielding (end) ---

# --- Column definitions: synergy map (start) ---

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

# --- Column definitions: synergy map (end) ---

BATTER_META_COLS = ["Player", "Captain"]

DATA_DIR = Path(__file__).resolve().parent / "Data"
DEFAULT_OUTPUT = DATA_DIR / "results.csv"

# --- Schema: column list builders (start) ---


def build_all_columns() -> list[str]:
    """Full header: game settings once, then each team's data."""
    columns = list(gameCols) + list(stadiumCols)

    ability_cols = ability_one_hot_columns()
    pitching_star_cols = pitching_star_one_hot_columns()
    batting_star_cols = batting_star_one_hot_columns()

    for team_num in (1, 2):
        prefix = f"Team {team_num}"
        # Defense: field synergies
        for col in fieldSynergyCols:
            columns.append(f"{prefix} {col}")
        # Pitching: pitcher stats + star skill
        for col in pitcherCols:
            columns.append(f"{prefix} {col}")
        for col in pitching_star_cols:
            columns.append(f"{prefix} {col}")
        # Defense: pitcher field ability
        for col in ability_cols:
            columns.append(f"{prefix} {col}")
        for slot in range(1, LINEUP_SIZE + 1):
            slot_prefix = f"{prefix} Batter {slot}"
            for col in BATTER_META_COLS:
                columns.append(f"{slot_prefix} {col}")
            # Batting: stats + star skill
            for col in battingCols:
                columns.append(f"{slot_prefix} {col}")
            for col in batting_star_cols:
                columns.append(f"{slot_prefix} {col}")
            # Defense: fielding stats + field ability
            for col in fieldingStatCols:
                columns.append(f"{slot_prefix} {col}")
            for col in ability_cols:
                columns.append(f"{slot_prefix} {col}")

    return columns


# --- Schema: column list builders (end) ---

# --- Row helpers (start) ---


def _on_off(value: bool) -> str:
    return "on" if value else "off"


def _prefixed_one_hot(prefix: str, encoding: dict[str, int]) -> dict[str, Any]:
    return {f"{prefix} {col}": value for col, value in encoding.items()}


def _is_captain(player: Team.Player | None, captain: Team.Player | None) -> bool:
    if player is None or captain is None:
        return False
    return player.get_player().casefold() == captain.get_player().casefold()


def _field_synergy_value(team: Team, pos_a: str, pos_b: str) -> int:
    """Field synergy: 1 = good chemistry, 0 = neutral, -1 = bad."""
    value = team.relations.get(relation_key(pos_a, pos_b))
    if value == GOOD_SYNERGY:
        return 1
    if value == BAD_SYNERGY:
        return -1
    return NO_SYNERGY

# --- Row helpers (end) ---

# --- Game row builder (start) ---


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

# --- Game row builder (end) ---

# --- Team row builder (start) ---


def build_team_columns(
    team: Team,
    team_num: int,
    captain: Team.Player | None = None,
) -> dict[str, Any]:
    """Team data: defense (synergies, field abilities), pitching, batting (by order)."""
    prefix = f"Team {team_num}"
    row: dict[str, Any] = {}

    # --- Team row: field synergies (start) ---
    for col, (pos_a, pos_b) in FIELD_SYNERGY_COLS.items():
        row[f"{prefix} {col}"] = _field_synergy_value(team, pos_a, pos_b)
    # --- Team row: field synergies (end) ---

    # --- Team row: pitching (start) ---
    pitcher = team.positions.get(PITCHER)
    row[f"{prefix} Curveball Speed"] = pitcher.curveball_speed if pitcher else ""
    row[f"{prefix} Charge Pitch Speed"] = pitcher.charge_pitch_speed if pitcher else ""
    row[f"{prefix} Curve"] = pitcher.curve if pitcher else ""
    row[f"{prefix} Captain"] = _is_captain(pitcher, captain)
    row.update(
        _prefixed_one_hot(
            prefix,
            encode_pitching_star(pitcher.pitching_star if pitcher else None),
        )
    )
    row.update(
        _prefixed_one_hot(
            prefix,
            encode_ability(pitcher.ability if pitcher else None),
        )
    )
    # --- Team row: pitching (end) ---

    # --- Team row: batting & fielding (start) ---
    for slot in range(1, LINEUP_SIZE + 1):
        slot_prefix = f"{prefix} Batter {slot}"
        if slot > len(team.batting_players):
            row[f"{slot_prefix} Player"] = ""
            row[f"{slot_prefix} Captain"] = False
            for col in battingCols:
                row[f"{slot_prefix} {col}"] = ""
            row.update(_prefixed_one_hot(slot_prefix, encode_batting_star(None)))
            for col in fieldingStatCols:
                row[f"{slot_prefix} {col}"] = ""
            row.update(_prefixed_one_hot(slot_prefix, encode_ability(None)))
            continue

        batter = team.batting_players[slot - 1]

        row[f"{slot_prefix} Player"] = batter.get_player()
        row[f"{slot_prefix} Captain"] = _is_captain(batter, captain)
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
        row.update(
            _prefixed_one_hot(slot_prefix, encode_batting_star(batter.batting_star))
        )

        row[f"{slot_prefix} Fielding"] = batter.fielding
        row[f"{slot_prefix} Outfield Throwing Speed"] = batter.outfield_throwing_speed
        row.update(_prefixed_one_hot(slot_prefix, encode_ability(batter.ability)))

    # --- Team row: batting & fielding (end) ---
    return row

# --- Team row builder (end) ---

# --- Match row assembly (start) ---


def build_match_row(
    teams: list[tuple[str, Team]],
    game: Game,
) -> dict[str, Any]:
    """One CSV row for a full game."""
    row = {col: "" for col in build_all_columns()}
    row.update(build_game_columns(game))

    for team_num, (_, team) in enumerate(teams, start=1):
        if team_num > 2:
            break
        captain = game.team_1_captain if team_num == 1 else game.team_2_captain
        row.update(build_team_columns(team, team_num, captain))

    return row


# --- Match row assembly (end) ---

# --- CSV export (start) ---


def create_results_csv(
    teams: list[tuple[str, Team]],
    game: Game,
    output_path: Path | str = DEFAULT_OUTPUT,
    append: bool = True,
) -> Path:
    """Write one game per row. Game settings appear once; team data is prefixed."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    row = build_match_row(teams, game)
    headers = build_all_columns()
    body = [row.get(col, "") for col in headers]

    file_exists = path.exists() and path.stat().st_size > 0

    with path.open("a" if append and file_exists else "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not (append and file_exists):
            writer.writerow(headers)
        writer.writerow(body)

    return path


# --- CSV export (end) ---

# --- Match row builders (end) ---
