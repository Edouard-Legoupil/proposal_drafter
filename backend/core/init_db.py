import logging
from sqlalchemy import (
    create_engine,
    Table,
    Column,
    Integer,
    String,
    Boolean,
    JSON,
    Text,
    TIMESTAMP,
    ForeignKey,
    MetaData,
    CheckConstraint,
    event,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from backend.core.db import engine

logger = logging.getLogger(__name__)

metadata = MetaData()

def gen_uuid():
    return str(uuid.uuid4())

users = Table(
    'users', metadata,
    Column('id', String, primary_key=True, default=gen_uuid),
    Column('email', String, unique=True, nullable=False),
    Column('password', String, nullable=False),
    Column('name', String),
    Column('security_questions', JSON),
    Column('session_active', Boolean, default=False),
    Column('created_at', TIMESTAMP, server_default=func.now()),
    Column('updated_at', TIMESTAMP, server_default=func.now(), onupdate=func.now())
)

proposals = Table(
    'proposals', metadata,
    Column('id', String, primary_key=True, default=gen_uuid),
    Column('user_id', String, ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
    Column('form_data', JSON, nullable=False),
    Column('project_description', Text, nullable=False),
    Column('generated_sections', JSON),
    Column('is_accepted', Boolean, default=False),
    Column('status', String(255), default='draft'),
    Column('field_contexts', Text), # Storing list as a comma-separated string
    Column('created_at', TIMESTAMP, server_default=func.now()),
    Column('updated_at', TIMESTAMP, server_default=func.now(), onupdate=func.now())
)

donors = Table(
    'donors', metadata,
    Column('id', String, primary_key=True, default=gen_uuid),
    Column('name', String, nullable=False, unique=True)
)

outcomes = Table(
    'outcomes', metadata,
    Column('id', String, primary_key=True, default=gen_uuid),
    Column('name', String, nullable=False, unique=True)
)

field_contexts = Table(
    'field_contexts', metadata,
    Column('id', String, primary_key=True, default=gen_uuid),
    Column('name', String, nullable=False, unique=True)
)

knowledge_cards = Table(
    'knowledge_cards', metadata,
    Column('id', String, primary_key=True, default=gen_uuid),
    Column('title', String, nullable=False),
    Column('summary', Text),
    Column('generated_sections', JSON),
    Column('is_accepted', Boolean, default=False),
    Column('status', String(255), default='draft'),
    Column('donor_id', String, ForeignKey('donors.id', ondelete='SET NULL')),
    Column('outcome_id', String, ForeignKey('outcomes.id', ondelete='SET NULL')),
    Column('field_context_id', String, ForeignKey('field_contexts.id', ondelete='SET NULL')),
    Column('created_at', TIMESTAMP, server_default=func.now()),
    Column('updated_at', TIMESTAMP, server_default=func.now(), onupdate=func.now()),
    CheckConstraint(
        "(CASE WHEN donor_id IS NOT NULL THEN 1 ELSE 0 END + "
        "CASE WHEN outcome_id IS NOT NULL THEN 1 ELSE 0 END + "
        "CASE WHEN field_context_id IS NOT NULL THEN 1 ELSE 0 END) = 1",
        name="one_link_only"
    )
)

knowledge_card_references = Table(
    'knowledge_card_references', metadata,
    Column('id', String, primary_key=True, default=gen_uuid),
    Column('knowledge_card_id', String, ForeignKey('knowledge_cards.id', ondelete='CASCADE'), nullable=False),
    Column('url', String, nullable=False)
)

proposal_donors = Table(
    'proposal_donors', metadata,
    Column('proposal_id', String, ForeignKey('proposals.id', ondelete='CASCADE'), primary_key=True),
    Column('donor_id', String, ForeignKey('donors.id', ondelete='CASCADE'), primary_key=True)
)

proposal_outcomes = Table(
    'proposal_outcomes', metadata,
    Column('proposal_id', String, ForeignKey('proposals.id', ondelete='CASCADE'), primary_key=True),
    Column('outcome_id', String, ForeignKey('outcomes.id', ondelete='CASCADE'), primary_key=True)
)

def initialize_database():
    logger.info("Initializing database and creating tables if they don't exist...")
    metadata.create_all(engine)
    logger.info("Database initialization complete.")

if __name__ == "__main__":
    initialize_database()
