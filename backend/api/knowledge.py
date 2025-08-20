from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, insert
from backend.core.db import engine
from backend.models import knowledge_schemas
from backend.core.init_db import donors, outcomes, field_contexts, knowledge_cards, knowledge_card_references
from typing import List
import uuid
import json

router = APIRouter()

def get_db():
    with engine.connect() as connection:
        yield connection

@router.post("/donors", response_model=knowledge_schemas.Donor)
def create_donor(donor_data: knowledge_schemas.DonorCreate, db: Session = Depends(get_db)):
    new_id = str(uuid.uuid4())
    stmt = insert(donors).values(id=new_id, name=donor_data.name)
    db.execute(stmt)
    db.commit()
    return {"id": new_id, **donor_data.dict()}

@router.get("/donors", response_model=List[knowledge_schemas.Donor])
def read_donors(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    query = select(donors).offset(skip).limit(limit)
    return db.execute(query).fetchall()

@router.post("/outcomes", response_model=knowledge_schemas.Outcome)
def create_outcome(outcome_data: knowledge_schemas.OutcomeCreate, db: Session = Depends(get_db)):
    new_id = str(uuid.uuid4())
    stmt = insert(outcomes).values(id=new_id, name=outcome_data.name)
    db.execute(stmt)
    db.commit()
    return {"id": new_id, **outcome_data.dict()}

@router.get("/outcomes", response_model=List[knowledge_schemas.Outcome])
def read_outcomes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    query = select(outcomes).offset(skip).limit(limit)
    return db.execute(query).fetchall()

@router.post("/field_contexts", response_model=knowledge_schemas.FieldContext)
def create_field_context(context_data: knowledge_schemas.FieldContextCreate, db: Session = Depends(get_db)):
    new_id = str(uuid.uuid4())
    stmt = insert(field_contexts).values(id=new_id, name=context_data.name)
    db.execute(stmt)
    db.commit()
    return {"id": new_id, **context_data.dict()}

@router.get("/field_contexts", response_model=List[knowledge_schemas.FieldContext])
def read_field_contexts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    query = select(field_contexts).offset(skip).limit(limit)
    return db.execute(query).fetchall()

@router.post("/knowledge_cards", response_model=knowledge_schemas.KnowledgeCard)
def create_knowledge_card(card: knowledge_schemas.KnowledgeCardCreate, db: Session = Depends(get_db)):
    card_id = str(uuid.uuid4())

    with db.begin():
        stmt = insert(knowledge_cards).values(
            id=card_id,
            title=card.title,
            summary=card.summary,
            status=card.status,
            donor_id=card.donor_id,
            outcome_id=card.outcome_id,
            field_context_id=card.field_context_id,
        )
        db.execute(stmt)

        for url in card.reference_urls:
            ref_stmt = insert(knowledge_card_references).values(
                id=str(uuid.uuid4()),
                knowledge_card_id=card_id,
                url=url
            )
            db.execute(ref_stmt)

    return get_knowledge_card(card_id, db=db)


@router.get("/knowledge_cards", response_model=List[knowledge_schemas.KnowledgeCard])
def read_knowledge_cards(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    query = select(knowledge_cards).order_by(knowledge_cards.c.updated_at.desc()).offset(skip).limit(limit)
    results = db.execute(query).fetchall()

    cards = []
    for row in results:
        card_dict = dict(row)
        ref_query = select(knowledge_card_references).where(knowledge_card_references.c.knowledge_card_id == card_dict['id'])
        refs = db.execute(ref_query).fetchall()
        card_dict['references'] = refs
        cards.append(card_dict)

    return cards

@router.get("/knowledge_cards/{card_id}", response_model=knowledge_schemas.KnowledgeCard)
def get_knowledge_card(card_id: str, db: Session = Depends(get_db)):
    query = select(knowledge_cards).where(knowledge_cards.c.id == card_id)
    result = db.execute(query).fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Knowledge card not found")

    card_dict = dict(result)
    ref_query = select(knowledge_card_references).where(knowledge_card_references.c.knowledge_card_id == card_dict['id'])
    refs = db.execute(ref_query).fetchall()
    card_dict['references'] = refs

    return card_dict
