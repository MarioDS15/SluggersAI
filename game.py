"""Game setup: stadium, captains, rules, and options."""

from __future__ import annotations

from dataclasses import dataclass

from player import Player as RosterPlayer
from startup import PLAYERS, TEAM_NAMES
from team import Team

TeamPlayer = Team.Player

# Size: 1 (low) → 3 (high). Hazard / obstacles: 0 (low) → 2 (high).
Stadiums = [
    {"name": "Mario Stadium (Day)", "size": 2, "hazard": 0, "obstacles": 0},
    {"name": "Mario Stadium (Night)", "size": 2, "hazard": 0, "obstacles": 0},
    {"name": "Luigi Mansion (Night)", "size": 1, "hazard": 2, "obstacles": 2},
    {"name": "Daisy Cruiser (Day)", "size": 1, "hazard": 0, "obstacles": 2},
    {"name": "Daisy Cruiser (Night)", "size": 1, "hazard": 1, "obstacles": 1},
    {"name": "Peach Ice Garden (Day)", "size": 3, "hazard": 2, "obstacles": 2},
    {"name": "Peach Ice Garden (Night)", "size": 3, "hazard": 2, "obstacles": 2},
    {"name": "Yoshi Park (Day)", "size": 1, "hazard": 2, "obstacles": 2},
    {"name": "Yoshi Park (Night)", "size": 1, "hazard": 2, "obstacles": 2},
    {"name": "DK Jungle (Day)", "size": 2, "hazard": 2, "obstacles": 0},
    {"name": "DK Jungle (Night)", "size": 2, "hazard": 2, "obstacles": 0},
    {"name": "Bowser Castle (Night)", "size": 3, "hazard": 2, "obstacles": 0},
    {"name": "Wario City (Day)", "size": 2, "hazard": 2, "obstacles": 0},
    {"name": "Wario City (Night)", "size": 2, "hazard": 0, "obstacles": 0},
    {"name": "Bowser Jr Playroom (Day)", "size": 3, "hazard": 0, "obstacles": 0},
]

STADIUMS = tuple(s["name"] for s in Stadiums)

INNING_OPTIONS = (1, 3, 5, 7, 9)


@dataclass
class Game:
    """Match settings for a Mario Super Sluggers game."""

    stadium: str
    team_1_captain: TeamPlayer
    team_2_captain: TeamPlayer
    star_power: bool
    innings: int
    mercy_rule: bool
    items: bool

    def get_stadium(self) -> str:
        return self.stadium

    def get_stadium_info(self) -> dict[str, int]:
        """Size 1–3; hazard and obstacles 0–2."""
        for entry in Stadiums:
            if entry["name"].casefold() == self.stadium.casefold():
                return {
                    "size": int(entry["size"]),
                    "hazard": int(entry["hazard"]),
                    "obstacles": int(entry["obstacles"]),
                }
        return {"size": 0, "hazard": 0, "obstacles": 0}

    def get_team_1_captain(self) -> TeamPlayer:
        return self.team_1_captain

    def get_team_2_captain(self) -> TeamPlayer:
        return self.team_2_captain

    def get_star_power(self) -> bool:
        return self.star_power

    def get_innings(self) -> int:
        return self.innings

    def get_mercy_rule(self) -> bool:
        return self.mercy_rule

    def get_items(self) -> bool:
        return self.items

    def format_summary(self) -> str:
        on_off = lambda v: "On" if v else "Off"
        return "\n".join(
            [
                "=== Game Setup ===",
                "",
                f"Stadium: {self.stadium}",
                f"Team 1 Captain: {self.team_1_captain.get_player()}",
                f"Team 2 Captain: {self.team_2_captain.get_player()}",
                f"Star Power: {on_off(self.star_power)}",
                f"Innings: {self.innings}",
                f"Mercy Rule: {on_off(self.mercy_rule)}",
                f"Items: {on_off(self.items)}",
            ]
        )


def _lookup_player(name: str) -> RosterPlayer | None:
    key = name.strip()
    if not key:
        return None
    if key in PLAYERS:
        return PLAYERS[key]
    by_folded = {n.casefold(): p for n, p in PLAYERS.items()}
    return by_folded.get(key.casefold())


def _find_lineup_player(team: Team, name: str) -> TeamPlayer | None:
    key = name.strip().casefold()
    for player in team.get_all_players():
        if player.get_player().casefold() == key:
            return player
    return None


def _prompt_yes_no(prompt: str) -> bool:
    while True:
        answer = input(prompt).strip().lower()
        if answer in ("y", "yes", "on"):
            return True
        if answer in ("n", "no", "off"):
            return False
        print("  Enter y/yes/on or n/no/off.")


def _prompt_stadium() -> str:
    print("\nSelect stadium:")
    for i, stadium in enumerate(STADIUMS, start=1):
        print(f"  {i}. {stadium}")
    while True:
        choice = input("Stadium (number or name): ").strip()
        if choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(STADIUMS):
                return STADIUMS[index]
        for stadium in STADIUMS:
            if choice.casefold() == stadium.casefold():
                return stadium
        print("  Invalid stadium. Try again.")


def _prompt_captain(team_label: str, team: Team | None = None) -> TeamPlayer:
    hint = " (must be on this team's lineup)" if team else ""
    team_number = 1 if team_label == TEAM_NAMES[0] else 2
    while True:
        name = input(f"{team_label} captain{hint}: ").strip()
        if team is not None:
            player = _find_lineup_player(team, name)
            if player is None:
                print(f"  {name!r} is not on {team_label}. Try again.")
                continue
            return player
        roster_player = _lookup_player(name)
        if roster_player is None:
            print(f"  Player not found: {name!r}. Try again.")
            continue
        return TeamPlayer.from_roster(Team(number=team_number), roster_player)


def _prompt_innings() -> int:
    options = ", ".join(str(n) for n in INNING_OPTIONS)
    while True:
        answer = input(f"Innings ({options}): ").strip()
        if answer.isdigit() and int(answer) in INNING_OPTIONS:
            return int(answer)
        print(f"  Choose one of: {options}")


def setup_game(teams: list[tuple[str, Team]] | None = None) -> Game:
    """Prompt for match settings. Optionally validate captains against team rosters."""
    print("--- Game Setup ---")

    stadium = _prompt_stadium()

    team_1 = teams[0][1] if teams and len(teams) >= 1 else None
    team_2 = teams[1][1] if teams and len(teams) >= 2 else None

    team_1_captain = _prompt_captain(TEAM_NAMES[0], team_1)
    team_2_captain = _prompt_captain(TEAM_NAMES[1], team_2)

    star_power = _prompt_yes_no("Star Power (on/off): ")
    innings = _prompt_innings()
    mercy_rule = _prompt_yes_no("Mercy Rule (on/off): ")
    items = _prompt_yes_no("Items (on/off): ")

    return Game(
        stadium=stadium,
        team_1_captain=team_1_captain,
        team_2_captain=team_2_captain,
        star_power=star_power,
        innings=innings,
        mercy_rule=mercy_rule,
        items=items,
    )


def print_game_verification(game: Game) -> None:
    print()
    print(game.format_summary())


if __name__ == "__main__":
    match = setup_game()
    print_game_verification(match)
