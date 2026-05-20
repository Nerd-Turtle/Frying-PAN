from __future__ import annotations

import sqlite3

from frying_pan.sources.base import SourceConfig


class SourceRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def upsert(self, source: SourceConfig) -> None:
        self.connection.execute(
            """
            insert into sources (id, display_name, source_type, checksum_sha256, workspace_path)
            values (?, ?, ?, ?, ?)
            on conflict(id) do update set
              display_name = excluded.display_name,
              source_type = excluded.source_type,
              checksum_sha256 = excluded.checksum_sha256,
              workspace_path = excluded.workspace_path
            """,
            (
                source.id,
                source.display_name,
                source.source_type.value,
                source.checksum_sha256,
                str(source.workspace_path) if source.workspace_path else None,
            ),
        )
        self.connection.commit()
