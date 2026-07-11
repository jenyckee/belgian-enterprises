from __future__ import annotations

import json
import os
import urllib.request
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, text

from api.schemas import (
    Contact,
    Denomination,
    EnterpriseDetail,
    EnterpriseWithDenomination,
    Establishment,
    Reference,
    AccountingData,
)
from db.database import get_session
from db.models import Address, Contact as ContactModel, Denomination as DenominationModel, Enterprise, Establishment as EstablishmentModel

router = APIRouter()

# NBB's Azure gateway returns 403 for the default "Python-urllib/x.y" User-Agent,
# so every request to the CBSO API must send an explicit User-Agent.
NBB_USER_AGENT = "kbo-local-api/0.1"


def _nbb_request(url: str, api_key: str, accept: str = "application/json") -> urllib.request.Request:
    request = urllib.request.Request(url)
    request.add_header("Accept", accept)
    request.add_header("X-Request-Id", str(uuid.uuid4()))
    request.add_header("Cache-Control", "no-cache")
    request.add_header("NBB-CBSO-Subscription-Key", api_key)
    request.add_header("User-Agent", NBB_USER_AGENT)
    return request


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


@router.get("/enterprise/{enterprise_number}/references", response_model=list[Reference])
def get_enterprise_references(enterprise_number: str, session=Depends(get_session)) -> list[Reference]:
    """
    Fetch annual account references (deposits) for a given enterprise number.
    Calls the NBB CBSO API: /legalEntity/{legalEntityId}/references
    """
    api_key = os.getenv("AUTHENTIC_DATA_PRIMARY_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="NBB API key not configured")

    url = f"https://ws.cbso.nbb.be/authentic/legalEntity/{enterprise_number}/references"

    request = _nbb_request(url, api_key)

    try:
        with urllib.request.urlopen(request) as response:
            data = json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        error_detail = e.read().decode() if e.fp else str(e)
        raise HTTPException(
            status_code=e.code,
            detail=f"NBB API error: {error_detail}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calling NBB API: {str(e)}"
        )
    
    # Parse response into Reference objects
    references: list[Reference] = []
    items = data if isinstance(data, list) else data.get("items", [])
    
    for item in items:
        # Map NBB API response to Reference model
        ref = Reference(
            reference_number=item.get("ReferenceNumber", ""),
            deposit_date=item.get("DepositDate", ""),
            exercise_dates={
                "start_date": item.get("ExerciseDates", {}).get("startDate", ""),
                "end_date": item.get("ExerciseDates", {}).get("endDate", ""),
            },
            model_type=item.get("ModelType", ""),
            deposit_type=item.get("DepositType", ""),
            language=item.get("Language", ""),
            currency=item.get("Currency", ""),
            enterprise_number=item.get("EnterpriseNumber", ""),
            enterprise_name=item.get("EnterpriseName", ""),
            address={
                "street": item.get("Address", {}).get("Street"),
                "number": item.get("Address", {}).get("Number"),
                "box": item.get("Address", {}).get("Box"),
                "postal_code": item.get("Address", {}).get("PostalCode"),
                "city": item.get("Address", {}).get("City"),
                "country_code": item.get("Address", {}).get("CountryCode"),
            } if item.get("Address") else None,
            legal_form=item.get("LegalForm"),
            legal_situation=item.get("LegalSituation"),
            full_fill_legal_validation=item.get("FullFillLegalValidation"),
            activity_code=item.get("ActivityCode"),
            general_assembly_date=item.get("GeneralAssemblyDate"),
            accounting_data_url=item.get("AccountingDataURL"),
            data_version=item.get("DataVersion"),
            improvement_date=item.get("ImprovementDate"),
            corrected_data=item.get("CorrectedData"),
        )
        references.append(ref)
    
    return references


@router.get("/enterprise/{enterprise_number}/accountingdata/{year}", response_model=AccountingData)
def get_enterprise_accounting_data(enterprise_number: str, year: int, session=Depends(get_session)) -> AccountingData:
    """
    Fetch accounting data for a given enterprise and fiscal year.
    Retrieves references, finds the matching year, and fetches detailed accounting data from NBB.
    """
    # Get all references for this enterprise
    api_key = os.getenv("AUTHENTIC_DATA_PRIMARY_KEY") or os.getenv("AUTHENTIC_DATA_SECONDARY_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="NBB API key not configured")

    url = f"https://ws.cbso.nbb.be/authentic/legalEntity/{enterprise_number}/references"

    request = _nbb_request(url, api_key)

    try:
        with urllib.request.urlopen(request) as response:
            references_data = json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        error_detail = e.read().decode() if e.fp else str(e)
        raise HTTPException(status_code=e.code, detail=f"NBB API error: {error_detail}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calling NBB API: {str(e)}")
    
    # Find reference matching the fiscal year
    items = references_data if isinstance(references_data, list) else references_data.get("items", [])
    matching_reference = None
    
    for item in items:
        exercise = item.get("ExerciseDates", {})
        if exercise.get("startDate"):
            year_from_date = int(exercise["startDate"][:4])
            if year_from_date == year:
                matching_reference = item
                break
    
    if not matching_reference:
        raise HTTPException(
            status_code=404,
            detail=f"No reference found for year {year}"
        )
    
    # Fetch accounting data for this reference
    reference_number = matching_reference.get("ReferenceNumber")
    accounting_url = f"https://ws.cbso.nbb.be/authentic/deposit/{reference_number}/accountingData"

    request = _nbb_request(accounting_url, api_key, accept="application/x.jsonxbrl")

    try:
        with urllib.request.urlopen(request) as response:
            accounting_json = json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        error_detail = e.read().decode() if e.fp else str(e)
        raise HTTPException(status_code=e.code, detail=f"NBB API error: {error_detail}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching accounting data: {str(e)}")
    
    # Parse accounting data into AccountingData model
    accounting_data = AccountingData(
        reference_number=accounting_json.get("ReferenceNumber", ""),
        enterprise_name=accounting_json.get("EnterpriseName", ""),
        address={
            "street": accounting_json.get("Address", {}).get("Street"),
            "number": accounting_json.get("Address", {}).get("Number"),
            "box": accounting_json.get("Address", {}).get("Box"),
            "city": accounting_json.get("Address", {}).get("City"),
            "other_postal_code": accounting_json.get("Address", {}).get("OtherPostalCode"),
            "other_city": accounting_json.get("Address", {}).get("OtherCity"),
            "country": accounting_json.get("Address", {}).get("Country"),
            "other_country": accounting_json.get("Address", {}).get("OtherCountry"),
        } if accounting_json.get("Address") else None,
        legal_form={
            "legal_form_code": accounting_json.get("LegalForm", {}).get("LegalFormCode"),
            "legal_form": accounting_json.get("LegalForm", {}).get("LegalForm"),
        } if accounting_json.get("LegalForm") else None,
        rubrics=[
            {
                "code": rubric.get("Code", ""),
                "value": rubric.get("Value", ""),
                "period": rubric.get("Period", ""),
                "data_type": rubric.get("DataType", ""),
                "type_amount": rubric.get("TypeAmount", ""),
            }
            for rubric in accounting_json.get("Rubrics", [])
        ],
        administrators={
            "legal_persons": accounting_json.get("Administrators", {}).get("LegalPersons", []),
            "natural_persons": accounting_json.get("Administrators", {}).get("NaturalPersons", []),
        } if accounting_json.get("Administrators") else None,
        participating_interests=accounting_json.get("ParticipatingInterests", []),
        shareholders={
            "entity_share_holders": accounting_json.get("Shareholders", {}).get("EntityShareHolders", []),
            "individual_share_holders": accounting_json.get("Shareholders", {}).get("IndividualShareHolders", []),
        } if accounting_json.get("Shareholders") else None,
    )
    
    return accounting_data


@router.get("/establishment/{establishment_number}", response_model=Establishment)
def get_establishment(establishment_number: str, session=Depends(get_session)) -> Establishment:
    stmt = select(EstablishmentModel).where(EstablishmentModel.establishment_number == establishment_number)
    establishment = session.scalars(stmt).one_or_none()
    if not establishment:
        raise HTTPException(status_code=404, detail="Establishment not found")
    return establishment

