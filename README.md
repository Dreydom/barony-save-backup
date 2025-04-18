# Barony Save Auto-Backup & Restore

A Python script to automatically back up and restore Barony `.baronysave` files.

## Features

- **Automatic Backup**: Detects new and modified saves and creates a timestamped backup.
- **One Backup per Run**: Keeps a single backup per unique `lobbykey`, replacing older backups.
- **Auto-Restore on Death**: When the game deletes a save file (on character death), the script restores it immediately.
- **Polling-Based**: Works without extra dependencies by polling the save directory at a fixed interval (default 5 seconds).
- **Readable Filenames**: Backup filenames include game name, lobby key, character race, class, level, floor, track, and in-game timestamp.
- **Graceful Shutdown**: Press `Ctrl+C` to stop the monitor cleanly.

## Requirements

Knowing how to:
1. Read.
2. Run Python (optional, .exe file in Releases).

## Installation

1. Copy `backup.py` into your Barony **savegames** folder (where `.baronysave` files appear).
2. Ensure you have write permissions to create a subfolder called `backups`.
3. (Optional) Adjust configuration at the top of `backup.py` if needed.

## Configuration

At the top of `backup.py`, you can customize:

```python
SAVE_DIR = Path(__file__).resolve().parent  # where .baronysave files are
BACKUP_DIR = SAVE_DIR / "backups"           # where backups are stored
POLL_INTERVAL = 5.0                         # seconds between directory checks
LOG_LEVEL = logging.INFO                    # logging verbosity
```

No command-line arguments are required; the script uses its file location as the save directory by default.

## Backup Filename Format

Backups are named:

```
<GameName>-<lobbykey>-<race>-<class>-lvl<playerLevel>-floor<dungeon>-<track>-<inGameTimestamp>.baronysave
```

Example:

```
Mystic-Mungus-2206257080-skeleton-conjurer-lvl1-floor1-0-2025-04-18_11-27-35.baronysave
```

## Usage

1. Navigate to your save directory (usually `c:\Program Files (x86)\Steam\steamapps\common\Barony\savegames\`)
2. Run the script:
   ```bash
   python backup.py
   ```
3. The script will print logs for each backup and restore action.
4. To stop, press `Ctrl+C`.

## How It Works

1. **Initial Scan**: On launch, the script scans existing `.baronysave` files and creates backups.
2. **Polling Loop**: Every `POLL_INTERVAL` seconds it checks for:
   - **New or Modified Saves**: Triggers a new backup (replacing the old one for that run).
   - **Deleted Saves**: Assumes death, restores the backup for that run.
3. **Backup Management**: Only one backup is kept per `lobbykey`, so disk usage stays limited.

## Known Issues

1. If you hit "Restart" in-game after dying, it will rewrite a `savegame[N].baronysave` file that got restored. To fix that, manually fetch the backup with your old character and save it as `savegame[N+1].baronysave` in the save folder.
