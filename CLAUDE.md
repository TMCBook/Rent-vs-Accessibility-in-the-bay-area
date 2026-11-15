# CLAUDE.md (repo root)

Project: **Rent vs. Reach**, 8th Annual Datathon for Social Good, Bay Area.

- Model and pipeline work happens in `model/`. Read **`model/CLAUDE.md`** before working there; it holds the team's integration rules (raw data is read-only, one time-based split, test set touched once, every number from a script).
- `housing_costs/` (Albert) and `essential_services/` (Anna) are teammates' work. `model/` reads their output tables; don't edit them without telling their owner.
- `rent_vs_reach_map/` is the standalone interactive map demo.
- Never commit raw data (shared-drive CSVs) or credentials.
