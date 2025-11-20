"""Backup and recovery utilities."""

import shutil
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger("quantalpha.backup")


def backup_database(
    db_path: str,
    backup_dir: str = "backups",
    keep_backups: int = 7
) -> Optional[str]:
    """Backup SQLite database.
    
    Args:
        db_path: Path to database file
        backup_dir: Directory for backups
        keep_backups: Number of backups to keep
    
    Returns:
        Path to backup file or None on error
    """
    try:
        db_path_obj = Path(db_path)
        if not db_path_obj.exists():
            logger.warning(f"Database not found: {db_path}")
            return None
        
        # Create backup directory
        backup_path = Path(backup_dir)
        backup_path.mkdir(exist_ok=True)
        
        # Create backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_path / f"{db_path_obj.stem}_{timestamp}.db"
        
        # Copy database
        shutil.copy2(db_path, backup_file)
        
        logger.info(f"Database backed up to: {backup_file}")
        
        # Clean old backups
        cleanup_old_backups(backup_path, keep_backups)
        
        return str(backup_file)
    
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        return None


def cleanup_old_backups(backup_dir: Path, keep_backups: int):
    """Remove old backup files.
    
    Args:
        backup_dir: Backup directory
        keep_backups: Number of backups to keep
    """
    try:
        backups = sorted(
            backup_dir.glob("*.db"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        if len(backups) > keep_backups:
            for old_backup in backups[keep_backups:]:
                old_backup.unlink()
                logger.debug(f"Removed old backup: {old_backup}")
    
    except Exception as e:
        logger.warning(f"Failed to cleanup old backups: {e}")


def restore_database(
    backup_file: str,
    target_path: str
) -> bool:
    """Restore database from backup.
    
    Args:
        backup_file: Path to backup file
        target_path: Target path for restored database
    
    Returns:
        True if successful, False otherwise
    """
    try:
        backup_path = Path(backup_file)
        if not backup_path.exists():
            logger.error(f"Backup file not found: {backup_file}")
            return False
        
        # Copy backup to target
        shutil.copy2(backup_file, target_path)
        
        logger.info(f"Database restored from: {backup_file} to {target_path}")
        return True
    
    except Exception as e:
        logger.error(f"Restore failed: {e}")
        return False


def backup_knowledge_base(
    kb_dir: str,
    backup_dir: str = "backups/kb",
    keep_backups: int = 7
) -> Optional[str]:
    """Backup knowledge base directory.
    
    Args:
        kb_dir: Knowledge base directory
        backup_dir: Backup directory
        keep_backups: Number of backups to keep
    
    Returns:
        Path to backup directory or None on error
    """
    try:
        kb_path = Path(kb_dir)
        if not kb_path.exists():
            logger.warning(f"Knowledge base not found: {kb_dir}")
            return None
        
        # Create backup directory
        backup_path = Path(backup_dir)
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # Create backup subdirectory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_subdir = backup_path / f"kb_{timestamp}"
        
        # Copy knowledge base
        shutil.copytree(kb_dir, backup_subdir)
        
        logger.info(f"Knowledge base backed up to: {backup_subdir}")
        
        # Clean old backups
        cleanup_old_kb_backups(backup_path, keep_backups)
        
        return str(backup_subdir)
    
    except Exception as e:
        logger.error(f"Knowledge base backup failed: {e}")
        return None


def cleanup_old_kb_backups(backup_dir: Path, keep_backups: int):
    """Remove old knowledge base backups.
    
    Args:
        backup_dir: Backup directory
        keep_backups: Number of backups to keep
    """
    try:
        backups = sorted(
            [d for d in backup_dir.iterdir() if d.is_dir() and d.name.startswith("kb_")],
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        if len(backups) > keep_backups:
            for old_backup in backups[keep_backups:]:
                shutil.rmtree(old_backup)
                logger.debug(f"Removed old KB backup: {old_backup}")
    
    except Exception as e:
        logger.warning(f"Failed to cleanup old KB backups: {e}")

