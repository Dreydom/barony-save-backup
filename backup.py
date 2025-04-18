#!/usr/bin/env python3
"""
Barony Save Auto-Backup & Restore

Place this script inside your Barony save directory and run it.
It will poll every POLL_INTERVAL seconds for new or modified `.baronysave` files,
keeping one backup per "lobbykey": new backups replace old ones.
Deleted saves (on death) are automatically restored.
"""
import json
import logging
import shutil
import sys
import time
from pathlib import Path

# === Configuration ===
if getattr(sys, 'frozen', False):
    # running as PyInstaller exe
    SAVE_DIR = Path(sys.executable).parent
else:
    # running as a normal .py
    SAVE_DIR = Path(__file__).parent
BACKUP_DIR = SAVE_DIR / "backups"
LOG_LEVEL = logging.INFO
POLL_INTERVAL = 5.0  # seconds between checks
# ========================

# Character mappings
def load_class_and_race_mappings():
    return {
        0: 'barbarian', 1: 'warrior', 2: 'healer', 3: 'rogue', 4: 'wanderer',
        5: 'cleric', 6: 'merchant', 7: 'wizard', 8: 'arcanist', 9: 'joker',
        10: 'sexton', 11: 'ninja', 12: 'monk', 13: 'conjurer', 14: 'accursed',
        15: 'mesmer', 16: 'brewer', 17: 'mechanist', 18: 'punisher', 19: 'shaman',
        20: 'hunter'
    }, {
        0: 'human', 1: 'skeleton', 2: 'vampire', 3: 'succubus', 4: 'goatman',
        5: 'automaton', 6: 'incubus', 7: 'goblin', 8: 'insectoid'
    }

CLASSES, RACES = load_class_and_race_mappings()

# Logging setup
logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('barony_backup')

# Ensure backup directory exists
try:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
except Exception as e:
    logger.error("Cannot create backup directory %s: %s", BACKUP_DIR, e)


def make_backup_filename(save_data: dict) -> str:
    """Generate a filename for backup based on save metadata."""
    game_name = save_data.get('game_name', 'unknown').replace(' ', '-')
    lobby_key = save_data.get('lobbykey', save_data.get('gamekey', '0'))
    dungeon_level = save_data.get('dungeon_lvl', 0)
    level_track = save_data.get('level_track', 0)
    player_data = save_data.get('players', [{}])[0]
    player_level = player_data.get('stats', {}).get('LVL', 0)
    race_name = RACES.get(player_data.get('race', -1), 'unknown')
    class_name = CLASSES.get(player_data.get('char_class', -1), 'unknown')
    timestamp_field = save_data.get('timestamp', '').replace(' ', '_')
    return f"{game_name}-{lobby_key}-{race_name}-{class_name}-lvl{player_level}-floor{dungeon_level}-{level_track}-{timestamp_field}.baronysave"


def backup_save_file(file_path: Path, lobbykey_map: dict):
    """Remove old backup for this lobbykey and copy new backup."""
    try:
        save_data = json.loads(file_path.read_text())
    except Exception as e:
        logger.error("Failed to read JSON from %s: %s", file_path.name, e)
        return

    backup_name = make_backup_filename(save_data)
    lobby_key = save_data.get('lobbykey', save_data.get('gamekey', None))

    # Remove existing backup for this lobbykey
    if lobby_key is not None:
        for old_backup in BACKUP_DIR.glob(f"*-{lobby_key}-*.baronysave"):
            try:
                old_backup.unlink()
            except Exception:
                pass

    destination_path = BACKUP_DIR / backup_name
    try:
        shutil.copy2(file_path, destination_path)
        logger.info("Backed up %s → %s", file_path.name, backup_name)
        lobbykey_map[file_path.name] = lobby_key
    except Exception as e:
        logger.error("Failed to back up %s: %s", file_path.name, e)


def restore_save_file(original_filename: str, lobbykey_map: dict) -> bool:
    """Restore latest backup for given lobbykey into SAVE_DIR."""
    lobby_key = lobbykey_map.get(original_filename)
    if lobby_key is None:
        return False

    backup_candidates = list(BACKUP_DIR.glob(f"*-{lobby_key}-*.baronysave"))
    if not backup_candidates:
        return False

    latest_backup = sorted(backup_candidates)[-1]
    target_path = SAVE_DIR / original_filename
    try:
        shutil.copy2(latest_backup, target_path)
        logger.info("Restored %s from %s", original_filename, latest_backup.name)
        return True
    except Exception as e:
        logger.error("Failed to restore %s: %s", original_filename, e)
        return False


def monitor_saves():
    """Poll SAVE_DIR for .baronysave changes and handle backups/restores."""
    previous_mod_times = {f.name: f.stat().st_mtime for f in SAVE_DIR.glob('*.baronysave')}
    lobbykey_map = {}

    # Initial backup
    for filename in previous_mod_times:
        backup_save_file(SAVE_DIR / filename, lobbykey_map)

    logger.info("Monitoring %s every %.1fs. Press Ctrl+C to exit.", SAVE_DIR, POLL_INTERVAL)

    try:
        while True:
            time.sleep(POLL_INTERVAL)
            current_mod_times = {f.name: f.stat().st_mtime for f in SAVE_DIR.glob('*.baronysave')}

            # Handle new or modified saves
            for filename, mtime in current_mod_times.items():
                if filename not in previous_mod_times or mtime > previous_mod_times[filename]:
                    logger.info("Detected save update %s", filename)
                    backup_save_file(SAVE_DIR / filename, lobbykey_map)

            # Handle deleted saves (death)
            deleted_saves = set(previous_mod_times) - set(current_mod_times)
            for filename in deleted_saves:
                logger.info("Save %s deleted (death), restoring...", filename)
                if restore_save_file(filename, lobbykey_map):
                    current_mod_times[filename] = time.time()
                else:
                    logger.info("No backup available for %s", filename)

            previous_mod_times = current_mod_times
    except KeyboardInterrupt:
        logger.info("Shutting down monitor.")


def main():
    if not SAVE_DIR.is_dir():
        logger.error("SAVE_DIR %s does not exist.", SAVE_DIR)
        return
    monitor_saves()


if __name__ == "__main__":
    main()