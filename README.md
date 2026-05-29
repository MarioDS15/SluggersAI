# SluggersAI

Mario Super Sluggers lineup builder — load player stats, build batting orders and defensive lineups interactively.

## Setup

1. Clone this repo:
   ```bash
   git clone https://github.com/MarioDS15/SluggersAI.git
   cd SluggersAI
   ```

2. Add your stats CSV locally (not included in the repo):
   - Place your file at `sluggers_chemistry - Modded Stats.csv` in the project root.
   - This file is gitignored so your sheet stays private.

3. Run:
   ```bash
   python3 startup.py
   ```

## Project layout

| File | Purpose |
|------|---------|
| `player.py` | `Player` model |
| `startup.py` | CSV loading + interactive team setup |
| `team.py` | `Team` batting order and defensive lineup |
| `sluggers_chemistry - Modded Stats.csv` | **Local only** — your modded stats sheet |
