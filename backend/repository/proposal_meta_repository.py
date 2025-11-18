#  Standard Library
import uuid
from typing import List, Dict, Any, Optional

#  Third-Party Libraries
from sqlalchemy import text
from sqlalchemy.orm import Session

#  Internal Modules
from backend.core.db import get_engine

class ProposalMetaRepository:
    def __init__(self):
        self.engine = get_engine()

    def get_donors(self) -> List[Dict[str, Any]]:
        with self.engine.connect() as connection:
            result = connection.execute(text("SELECT id, name FROM donors ORDER BY id"))
            return [{"id": str(row[0]), "name": row[1]} for row in result.fetchall()]

    def get_outcomes(self) -> List[Dict[str, Any]]:
        with self.engine.connect() as connection:
            result = connection.execute(text("SELECT id, name FROM outcomes ORDER BY id"))
            return [{"id": str(row[0]), "name": row[1]} for row in result.fetchall()]

    def get_field_contexts(self, geographic_coverage: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.engine.connect() as connection:
            if geographic_coverage:
                query = text("SELECT id, name, geographic_coverage FROM field_contexts WHERE geographic_coverage = :geo ORDER BY id")
                result = connection.execute(query, {"geo": geographic_coverage})
            else:
                query = text("SELECT id, name, geographic_coverage FROM field_contexts ORDER BY id")
                result = connection.execute(query)
            return [{"id": str(row[0]), "name": row[1], "geographic_coverage": row[2]} for row in result.fetchall()]

    def create_donor(self, name: str, user_id: uuid.UUID) -> uuid.UUID:
        new_id = uuid.uuid4()
        with self.engine.begin() as connection:
            connection.execute(
                text("INSERT INTO donors (id, name, created_by) VALUES (:id, :name, :user_id)"),
                {"id": new_id, "name": name, "user_id": user_id}
            )
        return new_id

    def create_outcome(self, name: str, user_id: uuid.UUID) -> uuid.UUID:
        new_id = uuid.uuid4()
        with self.engine.begin() as connection:
            connection.execute(
                text("INSERT INTO outcomes (id, name, created_by) VALUES (:id, :name, :user_id)"),
                {"id": new_id, "name": name, "user_id": user_id}
            )
        return new_id

    def create_field_context(self, name: str, category: str, geographic_coverage: str, user_id: uuid.UUID) -> uuid.UUID:
        new_id = uuid.uuid4()
        with self.engine.begin() as connection:
            connection.execute(
                text("INSERT INTO field_contexts (id, title, name, category, geographic_coverage, created_by) VALUES (:id, :title, :name, :category, :geo, :user_id)"),
                {
                    "id": new_id,
                    "title": name,
                    "name": name,
                    "category": category,
                    "geo": geographic_coverage,
                    "user_id": user_id
                }
            )
        return new_id
