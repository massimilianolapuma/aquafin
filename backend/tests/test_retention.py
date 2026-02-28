"""Tests for the retention cleanup service."""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import patch

import pytest

from app.services.retention import cleanup_expired_files


@pytest.fixture()
def temp_upload_dir(tmp_path: Path) -> Path:
    """Create and return a temporary upload directory."""
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    return upload_dir


class TestCleanupExpiredFiles:
    """Tests for cleanup_expired_files()."""

    def test_empty_directory(self, temp_upload_dir: Path) -> None:
        """No crash when the directory is empty."""
        with patch("app.services.retention.settings") as mock_settings:
            mock_settings.UPLOAD_TEMP_DIR = str(temp_upload_dir)
            mock_settings.UPLOAD_RETENTION_HOURS = 24
            deleted = cleanup_expired_files()
        assert deleted == 0

    def test_directory_does_not_exist(self, tmp_path: Path) -> None:
        """Return 0 when the upload directory doesn't exist yet."""
        nonexistent = tmp_path / "nonexistent"
        with patch("app.services.retention.settings") as mock_settings:
            mock_settings.UPLOAD_TEMP_DIR = str(nonexistent)
            mock_settings.UPLOAD_RETENTION_HOURS = 24
            deleted = cleanup_expired_files()
        assert deleted == 0

    def test_fresh_files_are_kept(self, temp_upload_dir: Path) -> None:
        """Files newer than retention period should not be removed."""
        # Create a fresh file
        (temp_upload_dir / "recent.json").write_text("{}")
        (temp_upload_dir / "recent.csv").write_text("a,b")

        with patch("app.services.retention.settings") as mock_settings:
            mock_settings.UPLOAD_TEMP_DIR = str(temp_upload_dir)
            mock_settings.UPLOAD_RETENTION_HOURS = 24
            deleted = cleanup_expired_files()

        assert deleted == 0
        assert (temp_upload_dir / "recent.json").exists()
        assert (temp_upload_dir / "recent.csv").exists()

    def test_expired_files_are_deleted(self, temp_upload_dir: Path) -> None:
        """Files older than retention period should be removed."""
        # Create files and make them appear old
        old_file = temp_upload_dir / "old-preview.json"
        old_file.write_text("{}")
        old_uploaded = temp_upload_dir / "old-upload.csv"
        old_uploaded.write_text("header\ndata")

        # Set mtime to 25 hours ago
        old_time = time.time() - (25 * 3600)
        import os

        os.utime(old_file, (old_time, old_time))
        os.utime(old_uploaded, (old_time, old_time))

        with patch("app.services.retention.settings") as mock_settings:
            mock_settings.UPLOAD_TEMP_DIR = str(temp_upload_dir)
            mock_settings.UPLOAD_RETENTION_HOURS = 24
            deleted = cleanup_expired_files()

        assert deleted == 2
        assert not old_file.exists()
        assert not old_uploaded.exists()

    def test_mixed_files_only_old_deleted(self, temp_upload_dir: Path) -> None:
        """Only expired files are removed; fresh ones remain."""
        import os

        fresh = temp_upload_dir / "fresh.json"
        fresh.write_text("{}")

        expired = temp_upload_dir / "expired.json"
        expired.write_text("{}")
        old_time = time.time() - (25 * 3600)
        os.utime(expired, (old_time, old_time))

        with patch("app.services.retention.settings") as mock_settings:
            mock_settings.UPLOAD_TEMP_DIR = str(temp_upload_dir)
            mock_settings.UPLOAD_RETENTION_HOURS = 24
            deleted = cleanup_expired_files()

        assert deleted == 1
        assert fresh.exists()
        assert not expired.exists()

    def test_subdirectories_are_ignored(self, temp_upload_dir: Path) -> None:
        """Subdirectories should not be deleted, only files."""
        import os

        subdir = temp_upload_dir / "subdir"
        subdir.mkdir()
        # Make the subdir look old
        old_time = time.time() - (25 * 3600)
        os.utime(subdir, (old_time, old_time))

        with patch("app.services.retention.settings") as mock_settings:
            mock_settings.UPLOAD_TEMP_DIR = str(temp_upload_dir)
            mock_settings.UPLOAD_RETENTION_HOURS = 24
            deleted = cleanup_expired_files()

        assert deleted == 0
        assert subdir.exists()

    def test_custom_retention_hours(self, temp_upload_dir: Path) -> None:
        """Respect custom UPLOAD_RETENTION_HOURS value."""
        import os

        # File is 2 hours old
        f = temp_upload_dir / "two_hours_old.json"
        f.write_text("{}")
        os.utime(f, (time.time() - 7200, time.time() - 7200))

        # With 1-hour retention → should be deleted
        with patch("app.services.retention.settings") as mock_settings:
            mock_settings.UPLOAD_TEMP_DIR = str(temp_upload_dir)
            mock_settings.UPLOAD_RETENTION_HOURS = 1
            deleted = cleanup_expired_files()

        assert deleted == 1
        assert not f.exists()
