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


class EnterpriseDetail(EnterpriseBase):
    addresses: list[Address] = []
    contacts: list[Contact] = []
    denominations: list[Denomination] = []
    establishments: list[Establishment] = []
