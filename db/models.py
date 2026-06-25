from __future__ import annotations

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.database import Base


class Enterprise(Base):
    __tablename__ = "enterprises"

    enterprise_number: Mapped[str] = mapped_column("enterprise_number", String(20), primary_key=True)
    status: Mapped[str | None] = mapped_column("status", String(50), nullable=True)
    juridical_situation: Mapped[str | None] = mapped_column("juridical_situation", String(100), nullable=True)
    type_of_enterprise: Mapped[str | None] = mapped_column("type_of_enterprise", String(50), nullable=True)
    juridical_form: Mapped[str | None] = mapped_column("juridical_form", String(100), nullable=True)
    juridical_form_cac: Mapped[str | None] = mapped_column("juridical_form_cac", String(100), nullable=True)
    start_date: Mapped[str | None] = mapped_column("start_date", String(20), nullable=True)

    establishments: Mapped[list["Establishment"]] = relationship("Establishment", back_populates="enterprise")
    branches: Mapped[list["Branch"]] = relationship("Branch", back_populates="enterprise")


class Establishment(Base):
    __tablename__ = "establishments"

    establishment_number: Mapped[str] = mapped_column("establishment_number", String(20), primary_key=True)
    start_date: Mapped[str | None] = mapped_column("start_date", String(20), nullable=True)
    enterprise_number: Mapped[str | None] = mapped_column("enterprise_number", String(20), ForeignKey("enterprises.enterprise_number"), nullable=True)

    enterprise: Mapped[Enterprise | None] = relationship("Enterprise", back_populates="establishments")


class Address(Base):
    __tablename__ = "addresses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_number: Mapped[str | None] = mapped_column("entity_number", String(20), nullable=True)
    type_of_address: Mapped[str | None] = mapped_column("type_of_address", String(50), nullable=True)
    country_nl: Mapped[str | None] = mapped_column("country_nl", String(100), nullable=True)
    country_fr: Mapped[str | None] = mapped_column("country_fr", String(100), nullable=True)
    zipcode: Mapped[str | None] = mapped_column("zipcode", String(20), nullable=True)
    municipality_nl: Mapped[str | None] = mapped_column("municipality_nl", String(200), nullable=True)
    municipality_fr: Mapped[str | None] = mapped_column("municipality_fr", String(200), nullable=True)
    street_nl: Mapped[str | None] = mapped_column("street_nl", String(200), nullable=True)
    street_fr: Mapped[str | None] = mapped_column("street_fr", String(200), nullable=True)
    house_number: Mapped[str | None] = mapped_column("house_number", String(50), nullable=True)
    box: Mapped[str | None] = mapped_column("box", String(50), nullable=True)
    extra_address_info: Mapped[str | None] = mapped_column("extra_address_info", Text, nullable=True)
    date_striking_off: Mapped[str | None] = mapped_column("date_striking_off", String(20), nullable=True)


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_number: Mapped[str | None] = mapped_column("entity_number", String(20), nullable=True)
    entity_contact: Mapped[str | None] = mapped_column("entity_contact", String(100), nullable=True)
    contact_type: Mapped[str | None] = mapped_column("contact_type", String(50), nullable=True)
    value: Mapped[str | None] = mapped_column("value", Text, nullable=True)


class Denomination(Base):
    __tablename__ = "denominations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_number: Mapped[str | None] = mapped_column("entity_number", String(20), nullable=True)
    language: Mapped[str | None] = mapped_column("language", String(10), nullable=True)
    type_of_denomination: Mapped[str | None] = mapped_column("type_of_denomination", String(100), nullable=True)
    denomination: Mapped[str | None] = mapped_column("denomination", Text, nullable=True)


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_number: Mapped[str | None] = mapped_column("entity_number", String(20), nullable=True)
    activity_group: Mapped[str | None] = mapped_column("activity_group", String(100), nullable=True)
    nace_version: Mapped[str | None] = mapped_column("nace_version", String(10), nullable=True)
    nace_code: Mapped[str | None] = mapped_column("nace_code", String(50), nullable=True)
    classification: Mapped[str | None] = mapped_column("classification", String(100), nullable=True)


class Branch(Base):
    __tablename__ = "branches"

    id: Mapped[str] = mapped_column("id", String(20), primary_key=True)
    start_date: Mapped[str | None] = mapped_column("start_date", String(20), nullable=True)
    enterprise_number: Mapped[str | None] = mapped_column("enterprise_number", String(20), ForeignKey("enterprises.enterprise_number"), nullable=True)

    enterprise: Mapped[Enterprise | None] = relationship("Enterprise", back_populates="branches")
