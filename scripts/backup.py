import shutil
import logging
from datetime import datetime
from pathlib import Path
from utils import config

logger = logging.getLogger(__name__)

def backup_system():
    """
    Full system backup (Phase 12).
    Backs up ChromaDB + SQLite to dated folder.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    backup_dir = Path(f"data/backups/{timestamp}")
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting backup to {backup_dir}...")
    
    try:
        # 1. Backup ChromaDB
        chroma_src = Path(config.CHROMA_PERSIST_DIRECTORY)
        chroma_dst = backup_dir / "chroma"
        shutil.copytree(chroma_src, chroma_dst)
        logger.info("✅ ChromaDB backed up")
        
        # 2. Backup SQLite
        sqlite_src = Path(config.METADATA_DB_PATH)
        sqlite_dst = backup_dir / "metadata.db"
        shutil.copy2(sqlite_src, sqlite_dst)
        logger.info("✅ SQLite backed up")
        
        # 3. Create manifest
        manifest = {
            "timestamp": timestamp,
            "chroma_path": str(chroma_dst),
            "sqlite_path": str(sqlite_dst)
        }
        
        manifest_path = backup_dir / "manifest.json"
        import json
        manifest_path.write_text(json.dumps(manifest, indent=2))
        
        logger.info(f"🎉 Backup complete: {backup_dir}")
        return str(backup_dir)
        
    except Exception as e:
        logger.error(f"❌ Backup failed: {e}")
        return None

def restore_from_backup(backup_path: str):
    """
    Restore system from backup.
    WARNING: Overwrites current data!
    """
    backup_dir = Path(backup_path)
    if not backup_dir.exists():
        logger.error(f"Backup not found: {backup_path}")
        return False
        
    logger.info(f"Restoring from {backup_path}...")
    
    try:
        # 1. Restore ChromaDB
        chroma_src = backup_dir / "chroma"
        chroma_dst = Path(config.CHROMA_PERSIST_DIRECTORY)
        
        if chroma_dst.exists():
            shutil.rmtree(chroma_dst)
        shutil.copytree(chroma_src, chroma_dst)
        logger.info("✅ ChromaDB restored")
        
        # 2. Restore SQLite
        sqlite_src = backup_dir / "metadata.db"
        sqlite_dst = Path(config.METADATA_DB_PATH)
        shutil.copy2(sqlite_src, sqlite_dst)
        logger.info("✅ SQLite restored")
        
        logger.info(f"🎉 Restore complete!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Restore failed: {e}")
        return False

if __name__ == "__main__":
    # CLI usage
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "restore":
        restore_from_backup(sys.argv[2])
    else:
        backup_system()
