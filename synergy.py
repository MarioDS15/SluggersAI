"""Synergy / chemistry between lineup players and defensive position pairs."""

from __future__ import annotations

from typing import TYPE_CHECKING

from team import ALL_RELATION_KEYS, parse_relation_key

if TYPE_CHECKING:
    from team import Team

    LineupPlayer = Team.Player
else:
    LineupPlayer = object

# 1 = good chemistry, -1 = bad, 0 = neutral / none
GOOD_SYNERGY = 1
BAD_SYNERGY = -1
NO_SYNERGY = 0


def link_value(player_a: LineupPlayer | None, player_b: LineupPlayer | None) -> int:
    """Chemistry score between two lineup players."""
    if player_a is None or player_b is None:
        return NO_SYNERGY
    if player_a.has_good_chemistry_with(player_b):
        return GOOD_SYNERGY
    if player_a.has_bad_chemistry_with(player_b):
        return BAD_SYNERGY
    return NO_SYNERGY


def link_label(value: int | None) -> str:
    if value is None:
        return "(not set)"
    if value == GOOD_SYNERGY:
        return "synergy"
    if value == BAD_SYNERGY:
        return "bad chemistry"
    return "neutral"


def has_batting_synergy(player_a: LineupPlayer | None, player_b: LineupPlayer | None) -> bool:
    """True only when the pair has good chemistry."""
    if player_a is None or player_b is None:
        return False
    return player_a.has_good_chemistry_with(player_b)


def batting_synergy_label(has_synergy: bool | None) -> str:
    if has_synergy is None:
        return "(not set)"
    return "synergy" if has_synergy else "no synergy"


def update_field_relations(team: Team) -> None:
    """Fill team.relations for every position pair from defensive lineup chemistry."""
    for key in ALL_RELATION_KEYS:
        pos_a, pos_b = parse_relation_key(key)
        team.relations[key] = link_value(
            team.positions[pos_a],
            team.positions[pos_b],
        )


def update_batting_synergy(team: Team) -> None:
    """Links between consecutive batters, plus last batter back to leadoff."""
    batters = team.batting_players
    n = len(batters)
    if n < 2:
        team.batting_synergy = []
        return

    links: list[bool] = []
    for i in range(n - 1):
        links.append(has_batting_synergy(batters[i], batters[i + 1]))
    links.append(has_batting_synergy(batters[-1], batters[0]))
    team.batting_synergy = links


def update_team_synergy(team: Team) -> None:
    """Update all synergy data on a team."""
    update_field_relations(team)
    update_batting_synergy(team)
