from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.core.db import engine
from backend.models import knowledge_schemas
from typing import List
import uuid

router = APIRouter()

# Dependency to get a DB session
def get_db():
    with engine.connect() as connection:
        yield connection

@router.post("/donors", response_model=knowledge_schemas.Donor)
def create_donor(donor: knowledge_schemas.Donor, db: Session = Depends(get_db)):
    query = text("INSERT INTO donors (id, name) VALUES (:id, :name) RETURNING id, name")
    result = db.execute(query, {"id": donor.id, "name": donor.name}).fetchone()
    return result

@router.get("/donors", response_model=List[knowledge_schemas.Donor])
def read_donors(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    query = text("SELECT id, name FROM donors ORDER BY name OFFSET :skip LIMIT :limit")
    results = db.execute(query, {"skip": skip, "limit": limit}).fetchall()
    return results

@router.post("/outcomes", response_model=knowledge_schemas.Outcome)
def create_outcome(outcome: knowledge_schemas.Outcome, db: Session = Depends(get_db)):
    query = text("INSERT INTO outcomes (id, name) VALUES (:id, :name) RETURNING id, name")
    result = db.execute(query, {"id": outcome.id, "name": outcome.name}).fetchone()
    return result

@router.get("/outcomes", response_model=List[knowledge_schemas.Outcome])
def read_outcomes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    query = text("SELECT id, name FROM outcomes ORDER BY name OFFSET :skip LIMIT :limit")
    results = db.execute(query, {"skip": skip, "limit": limit}).fetchall()
    return results

@router.post("/field_contexts", response_model=knowledge_schemas.FieldContext)
def create_field_context(field_context: knowledge_schemas.FieldContext, db: Session = Depends(get_db)):
    query = text("INSERT INTO field_contexts (id, name) VALUES (:id, :name) RETURNING id, name")
    result = db.execute(query, {"id": field_context.id, "name": field_context.name}).fetchone()
    return result

@router.get("/field_contexts", response_model=List[knowledge_schemas.FieldContext])
def read_field_contexts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    query = text("SELECT id, name FROM field_contexts ORDER BY name OFFSET :skip LIMIT :limit")
    results = db.execute(query, {"skip": skip, "limit": limit}).fetchall()
    return results

@router.post("/knowledge_cards", response_model=knowledge_schemas.KnowledgeCard)
def create_knowledge_card(card: knowledge_schemas.KnowledgeCardCreate, db: Session = Depends(get_db)):
    # The CHECK constraint in the DB will ensure only one of the foreign keys is set.
    card_id = uuid.uuid4()
    query = text(
        """
        INSERT INTO knowledge_cards (id, title, summary, status, donor_id, outcome_id, field_context_id)
        VALUES (:id, :title, :summary, :status, :donor_id, :outcome_id, :field_context_id)
        """
    )
    db.execute(
        query,
        {
            "id": card_id,
            "title": card.title,
            "summary": card.summary,
            "status": card.status,
            "donor_id": card.donor_id,
            "outcome_id": card.outcome_id,
            "field_context_id": card.field_context_id,
        },
    )

    for url in card.reference_urls:
        ref_query = text(
            """
            INSERT INTO knowledge_card_references (id, knowledge_card_id, url)
            VALUES (:id, :knowledge_card_id, :url)
            """
        )
        db.execute(ref_query, {"id": uuid.uuid4(), "knowledge_card_id": card_id, "url": url})

    db.commit()

    return get_knowledge_card(card_id, db)


@router.get("/knowledge_cards", response_model=List[knowledge_schemas.KnowledgeCard])
def read_knowledge_cards(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    query = text("SELECT * FROM knowledge_cards ORDER BY updated_at DESC OFFSET :skip LIMIT :limit")
    results = db.execute(query, {"skip": skip, "limit": limit}).fetchall()

    cards = []
    for row in results:
        card = dict(row)
        ref_query = text("SELECT id, url FROM knowledge_card_references WHERE knowledge_card_id = :card_id")
        refs = db.execute(ref_query, {"card_id": card['id']}).fetchall()
        card['references'] = refs
        cards.append(card)

    return cards


@router.get("/knowledge_cards/{card_id}", response_model=knowledge_schemas.KnowledgeCard)
def get_knowledge_card(card_id: uuid.UUID, db: Session = Depends(get_db)):
    query = text("SELECT * FROM knowledge_cards WHERE id = :card_id")
    result = db.execute(query, {"card_id": card_id}).fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Knowledge card not found")

    card = dict(result)
    ref_query = text("SELECT id, url FROM knowledge_card_references WHERE knowledge_card_id = :card_id")
    refs = db.execute(ref_query, {"card_id": card['id']}).fetchall()
    card['references'] = refs

    return card
