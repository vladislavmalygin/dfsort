import os
import shutil
import zipfile
import tarfile
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger('file_sorter')

def ensure_directory(path):
    Path(path).mkdir(parents=True, exist_ok=True)

def resolve_conflict(dest_path, conflict_mode):
    if not os.path.exists(dest_path):
        return dest_path

    if conflict_mode == 'overwrite':
        return dest_path
    elif conflict_mode == 'skip':
        return None
    elif conflict_mode == 'rename':
        base, ext = os.path.splitext(dest_path)
        counter = 1
        new_path = f"{base}_{counter}{ext}"
        while os.path.exists(new_path):
            counter += 1
            new_path = f"{base}_{counter}{ext}"
        return new_path
    else:
        raise ValueError(f"Unknown conflict mode: {conflict_mode}")

def move_file(src, dest_dir, conflict='rename', subfolder_by_date=None):
    if subfolder_by_date:
        mtime = os.path.getmtime(src)
        date_part = datetime.fromtimestamp(mtime).strftime(subfolder_by_date)
        dest_dir = os.path.join(dest_dir, date_part)

    ensure_directory(dest_dir)
    dest_path = os.path.join(dest_dir, os.path.basename(src))
    final_path = resolve_conflict(dest_path, conflict)

    if final_path is None:
        logger.info(f"Skip {src} (file exists, conflict policy 'skip')")
        return False

    shutil.move(src, final_path)
    logger.info(f"Moved {src} -> {final_path}")
    return True

def extract_archive(src, dest_dir, conflict='rename'):
    ensure_directory(dest_dir)

    try:
        if zipfile.is_zipfile(src):
            with zipfile.ZipFile(src, 'r') as zip_ref:
                zip_ref.extractall(dest_dir)
            logger.info(f"Extracted ZIP {src} -> {dest_dir}")
        elif tarfile.is_tarfile(src):
            with tarfile.open(src, 'r') as tar_ref:
                tar_ref.extractall(dest_dir)
            logger.info(f"Extracted TAR {src} -> {dest_dir}")
        else:
            logger.error(f"Unsupported archive type: {src}")
            return False
    except Exception as e:
        logger.error(f"Failed to extract {src}: {e}")
        return False

    try:
        os.remove(src)
        logger.info(f"Removed archive: {src}")
    except Exception as e:
        logger.warning(f"Could not remove archive {src}: {e}")

    return True

def delete_file(src, **kwargs):
    """
    Удаляет файл.
    """
    try:
        os.remove(src)
        logger.info(f"Deleted file: {src}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete {src}: {e}")
        return False