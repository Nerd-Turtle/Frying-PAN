from __future__ import annotations

import sqlite3
from pathlib import Path


def connect_cache(cache_path: Path) -> sqlite3.Connection:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(cache_path)
    connection.row_factory = sqlite3.Row
    initialize_cache(connection)
    return connection


def initialize_cache(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        create table if not exists cache_metadata (
            key text primary key,
            value text not null
        );

        create table if not exists sources (
            id text primary key,
            display_name text not null,
            source_type text not null,
            checksum_sha256 text,
            workspace_path text
        );
        """
    )
    connection.commit()
