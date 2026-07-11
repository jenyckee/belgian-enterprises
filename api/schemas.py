from __future__ import annotations

from pydantic import BaseModel


class EnterpriseBase(BaseModel):
    enterprise_number: str
    status: str | None = None
    juridical_situation: str | None = None
    type_of_enterprise: str | None = None
    juridical_form: str | None = None
    juridical_form_cac: str | None = None
    start_date: str | None = None

    class Config:
        orm_mode = True


class Address(BaseModel):
    entity_number: str | None = None
    type_of_address: str | None = None
    country_nl: str | None = None
    country_fr: str | None = None
    zipcode: str | None = None
    municipality_nl: str | None = None
    municipality_fr: str | None = None
    street_nl: str | None = None
    street_fr: str | None = None
    house_number: str | None = None
    box: str | None = None
    extra_address_info: str | None = None
    date_striking_off: str | None = None

    class Config:
        orm_mode = True


class Contact(BaseModel):
    entity_number: str | None = None
    entity_contact: str | None = None
    contact_type: str | None = None
    value: str | None = None

    class Config:
        orm_mode = True


class Denomination(BaseModel):
    entity_number: str | None = None
    language: str | None = None
    type_of_denomination: str | None = None
    denomination: str | None = None

    class Config:
        orm_mode = True


class Establishment(BaseModel):
    establishment_number: str
    start_date: str | None = None
    enterprise_number: str | None = None

    class Config:
        orm_mode = True


class EnterpriseWithDenomination(BaseModel):
    enterprise_number: str
    status: str | None = None
    start_date: str | None = None
    nace_code: str | None = None
    nace_version: str | None = None
    denomination: str | None = None

    class Config:
        orm_mode = True


class EnterpriseDetail(EnterpriseBase):
    addresses: list[Address] = []
    contacts: list[Contact] = []
    denominations: list[Denomination] = []
    establishments: list[Establishment] = []


class ExercisePeriod(BaseModel):
    start_date: str
    end_date: str

    class Config:
        orm_mode = True
        populate_by_name = True


class NBBAddress(BaseModel):
    street: str | None = None
    number: str | None = None
    box: str | None = None
    postal_code: str | None = None
    city: str | None = None
    country_code: str | None = None

    class Config:
        orm_mode = True
        populate_by_name = True


class Reference(BaseModel):
    reference_number: str
    deposit_date: str
    exercise_dates: ExercisePeriod
    model_type: str
    deposit_type: str
    language: str
    currency: str
    enterprise_number: str
    enterprise_name: str
    address: NBBAddress | None = None
    legal_form: str | None = None
    legal_situation: str | None = None
    full_fill_legal_validation: bool | None = None
    activity_code: str | None = None
    general_assembly_date: str | None = None
    accounting_data_url: str | None = None
    data_version: str | None = None
    corrected_data: str | None = None

    class Config:
        orm_mode = True
        populate_by_name = True


class Rubric(BaseModel):
    code: str
    value: str
    period: str
    data_type: str
    type_amount: str

    class Config:
        orm_mode = True
        populate_by_name = True


class LegalFormInfo(BaseModel):
    legal_form_code: str | None = None
    legal_form: str | None = None

    class Config:
        orm_mode = True
        populate_by_name = True


class AccountingAddress(BaseModel):
    street: str | None = None
    number: str | None = None
    box: str | None = None
    city: str | None = None
    other_postal_code: str | None = None
    other_city: str | None = None
    country: str | None = None
    other_country: str | None = None

    class Config:
        orm_mode = True
        populate_by_name = True


class Administrators(BaseModel):
    legal_persons: list = []
    natural_persons: list = []

    class Config:
        orm_mode = True
        populate_by_name = True


class Shareholders(BaseModel):
    entity_share_holders: list = []
    individual_share_holders: list = []

    class Config:
        orm_mode = True
        populate_by_name = True


class AccountingData(BaseModel):
    reference_number: str
    enterprise_name: str
    address: AccountingAddress | None = None
    legal_form: LegalFormInfo | None = None
    rubrics: list[Rubric] = []
    administrators: Administrators | None = None
    participating_interests: list = []
    shareholders: Shareholders | None = None

    class Config:
        orm_mode = True
        populate_by_name = True
