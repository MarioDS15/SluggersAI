# SlugAI

Builds `Data/results.csv` from Mario Super Sluggers roster stats, team lineups, game settings, and chemistry/synergy.

**Run:** `python3 startup.py` (writes `Data/results.csv`). At startup, choose **y** to load teams and game settings from `config.json`, or **n** for interactive prompts.

**Config:** `config.json` — default lineups and game settings when you answer **y** at startup.

---

## Project layout

```
SlugAI/
├── startup.py          # Entry point (run this)
├── config.json         # Optional teams + game preset
├── Data/               # Data extraction from Input code + Player CSVs
│   ├── player.py
│   ├── team.py
│   ├── synergy.py
│   ├── game.py
│   ├── datasheet.py
│   ├── PlayerStats.csv # gitignored
│   └── results.csv     # gitignored
├── ML/                 # Model training (next phase)
└── GUI/                # UI (planned)
```

---

## Modules (in `Data/`)

### `player.py`
Roster character (stats from CSV, not tied to a team).

- `Player.from_row` — parse one CSV row into a `Player`

### `team.py`
Lineup for one side: batting order, defensive positions, relation slots.

- `Team` — holds `batting_players`, `positions`, `relations`, `batting_synergy`
- `Team.Player` — player on this team; wraps roster `Player` in `stats`
- `relation_key` — canonical key for a position pair (e.g. pitcher ↔ catcher)
- `Team.update_synergy` — refresh field relations and batting synergy (calls `synergy.py`)

### `synergy.py`
Chemistry between positions and adjacent batters.

- `link_value` — good / neutral / bad for two players at two positions
- `has_batting_synergy` — whether consecutive batters have batting chemistry
- `update_field_relations` — fill `team.relations` from defensive lineup
- `update_batting_synergy` — fill `team.batting_synergy` from batting order
- `update_team_synergy` — both of the above

### `game.py`
Match rules and stadium.

- `Game` — stadium, captains, innings, star power, mercy, items
- `setup_game` — interactive prompts for match settings
- `game_from_config` — build a `Game` from `config.json`
- `print_game_verification` — print game summary

### `startup.py` (repo root)
Load roster and teams; main entry point.

- `load_all_players` — read `PlayerStats.csv` into `PLAYERS`
- `load_setup_from_json` / `load_setup_interactive` — teams + game from JSON or prompts
- `run_results_export` — teams → game setup → write `results.csv`

### `datasheet.py`
One row per match for ML export.

- `register_encodings_from_roster` — set ability/star one-hot columns from roster
- `build_all_columns` — full CSV header
- `build_game_columns` / `build_team_columns` — one side of the row
- `build_match_row` — game + both teams
- `create_results_csv` — write `Data/results.csv`
