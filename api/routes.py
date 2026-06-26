from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, text

from api.schemas import Contact, Denomination, EnterpriseDetail, EnterpriseWithDenomination, Establishment
from db.database import get_session
from db.models import Address, Contact as ContactModel, Denomination as DenominationModel, Enterprise, Establishment as EstablishmentModel

router = APIRouter()


@router.get("/enterprise/{enterprise_number}", response_model=EnterpriseDetail)
def get_enterprise(enterprise_number: str, session=Depends(get_session)) -> EnterpriseDetail:
    stmt = select(Enterprise).where(Enterprise.enterprise_number == enterprise_number)
    enterprise = session.scalars(stmt).one_or_none()
    if not enterprise:
        raise HTTPException(status_code=404, detail="Enterprise not found")

    enterprise.addresses = session.scalars(select(Address).where(Address.entity_number == enterprise_number)).all()
    enterprise.contacts = session.scalars(select(ContactModel).where(ContactModel.entity_number == enterprise_number)).all()
    enterprise.denominations = session.scalars(select(DenominationModel).where(DenominationModel.entity_number == enterprise_number)).all()
    enterprise.establishments = session.scalars(
        select(EstablishmentModel).where(EstablishmentModel.enterprise_number == enterprise_number)
    ).all()

    return enterprise


@router.get("/enterprise/{enterprise_number}/establishments", response_model=list[Establishment])
def get_enterprise_establishments(enterprise_number: str, session=Depends(get_session)) -> list[Establishment]:
    stmt = select(EstablishmentModel).where(EstablishmentModel.enterprise_number == enterprise_number)
    establishments = session.scalars(stmt).all()
    return establishments


@router.get("/enterprise/{enterprise_number}/contact", response_model=list[Contact])
def get_enterprise_contact(enterprise_number: str, session=Depends(get_session)) -> list[Contact]:
    stmt = select(ContactModel).where(ContactModel.entity_number == enterprise_number)
    return session.scalars(stmt).all()


@router.get("/enterprise/{enterprise_number}/denominations", response_model=list[Denomination])
def get_enterprise_denominations(enterprise_number: str, session=Depends(get_session)) -> list[Denomination]:
    stmt = select(DenominationModel).where(DenominationModel.entity_number == enterprise_number)
    return session.scalars(stmt).all()


@router.get("/enterprises", response_model=list[EnterpriseWithDenomination])
def get_enterprises_by_nace(nace: str, session=Depends(get_session)) -> list[EnterpriseWithDenomination]:
    stmt = text("""
        SELECT r.*, d.denomination
        FROM (
            SELECT DISTINCT
                COALESCE(e_ent.enterprise_number, e2.enterprise_number) AS enterprise_number,
                COALESCE(e_ent.status, e2.status) AS status,
                COALESCE(e_ent.start_date, e2.start_date) AS start_date,
                a.nace_code,
                a.nace_version
            FROM activities a
            LEFT JOIN enterprises e_ent
                ON e_ent.enterprise_number = a.entity_number
            LEFT JOIN establishments est
                ON est.establishment_number = a.entity_number
            LEFT JOIN enterprises e2
                ON e2.enterprise_number = est.enterprise_number
            WHERE a.nace_code LIKE :nace_pattern
              AND a.classification = 'MAIN'
              AND (e_ent.status = 'AC' OR (e_ent.status IS NULL AND e2.status = 'AC'))
            ORDER BY 1, nace_version DESC
            LIMIT 100
        ) r
        LEFT JOIN denominations d ON d.entity_number = r.enterprise_number
        ORDER BY r.enterprise_number, r.nace_version DESC
        LIMIT 100
    """)
    rows = session.execute(stmt, {"nace_pattern": f"{nace}%"}).mappings().all()
    return rows


@router.get("/establishment/{establishment_number}", response_model=Establishment)
def get_establishment(establishment_number: str, session=Depends(get_session)) -> Establishment:
    stmt = select(EstablishmentModel).where(EstablishmentModel.establishment_number == establishment_number)
    establishment = session.scalars(stmt).one_or_none()
    if not establishment:
        raise HTTPException(status_code=404, detail="Establishment not found")
    return establishment
