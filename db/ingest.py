from __future__ import annotations

import csv
import sys
from pathlib import Path

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from db.database import Base, engine
from db.models import Activity, Address, Branch, Contact, Denomination, Enterprise, Establishment

DATA_DIR = PROJECT_ROOT / "data"
BATCH_SIZE = 5000

CSV_MAP = [
    ("enterprise.csv", Enterprise, ["EnterpriseNumber", "Status", "JuridicalSituation", "TypeOfEnterprise", "JuridicalForm", "JuridicalFormCAC", "StartDate"]),
    ("establishment.csv", Establishment, ["EstablishmentNumber", "StartDate", "EnterpriseNumber"]),
    ("address.csv", Address, ["EntityNumber", "TypeOfAddress", "CountryNL", "CountryFR", "Zipcode", "MunicipalityNL", "MunicipalityFR", "StreetNL", "StreetFR", "HouseNumber", "Box", "ExtraAddressInfo", "DateStrikingOff"]),
    ("contact.csv", Contact, ["EntityNumber", "EntityContact", "ContactType", "Value"]),
    ("denomination.csv", Denomination, ["EntityNumber", "Language", "TypeOfDenomination", "Denomination"]),
    ("activity.csv", Activity, ["EntityNumber", "ActivityGroup", "NaceVersion", "NaceCode", "Classification"]),
    ("branch.csv", Branch, ["Id", "StartDate", "EnterpriseNumber"]),
]

KEY_MAPPING = {
    "EnterpriseNumber": "enterprise_number",
    "Status": "status",
    "JuridicalSituation": "juridical_situation",
    "TypeOfEnterprise": "type_of_enterprise",
    "JuridicalForm": "juridical_form",
    "JuridicalFormCAC": "juridical_form_cac",
    "StartDate": "start_date",
    "EstablishmentNumber": "establishment_number",
    "EntityNumber": "entity_number",
    "TypeOfAddress": "type_of_address",
    "CountryNL": "country_nl",
    "CountryFR": "country_fr",
    "Zipcode": "zipcode",
    "MunicipalityNL": "municipality_nl",
    "MunicipalityFR": "municipality_fr",
    "StreetNL": "street_nl",
    "StreetFR": "street_fr",
    "HouseNumber": "house_number",
    "Box": "box",
    "ExtraAddressInfo": "extra_address_info",
    "DateStrikingOff": "date_striking_off",
    "EntityContact": "entity_contact",
    "ContactType": "contact_type",
    "Value": "value",
    "Language": "language",
    "TypeOfDenomination": "type_of_denomination",
    "Denomination": "denomination",
    "ActivityGroup": "activity_group",
    "NaceVersion": "nace_version",
    "NaceCode": "nace_code",
    "Classification": "classification",
    "Id": "id",
    "EnterpriseNumber": "enterprise_number",
}


def normalize_record(record: dict[str, str]) -> dict[str, str | None]:
    result: dict[str, str | None] = {}
    for key, value in record.items():
        normalized_key = KEY_MAPPING.get(key, key.lower())
        if value is not None:
            value = value.strip()
        result[normalized_key] = value or None
    return result


def flush_batch(conn, model: type[Base], batch: list[dict[str, str | None]], conflict_columns: list) -> None:
    if not batch:
        return

    stmt = insert(model.__table__).on_conflict_do_nothing(index_elements=conflict_columns)
    try:
        with conn.begin():
            conn.execute(stmt, batch)
    except IntegrityError as exc:
        print(f"  Warning: skipped batch of {len(batch)} rows for {model.__tablename__}: {exc.orig}")
    batch.clear()


def ingest_table(file_name: str, model: type[Base], columns: list[str]) -> None:
    path = DATA_DIR / file_name
    print(f"Ingesting {file_name}", flush=True)

    with path.open(newline="", encoding="utf-8") as csvfile, engine.connect() as conn:
        reader = csv.DictReader(csvfile)
        batch: list[dict[str, str | None]] = []
        conflict_columns = [col for col in model.__table__.primary_key.columns]
        row_count = 0

        for row in reader:
            data = normalize_record(row)
            autoincrement_pk = next(iter(model.__table__.primary_key.columns)).autoincrement
            if autoincrement_pk is True and data.get("id") is None:
                data.pop("id", None)
            batch.append(data)
            row_count += 1
            if len(batch) >= BATCH_SIZE:
                flush_batch(conn, model, batch, conflict_columns)

        flush_batch(conn, model, batch, conflict_columns)
        print(f"  Processed {row_count} rows from {file_name}", flush=True)


def main() -> None:
    print(f"Creating database schema using {engine.url}...", flush=True)
    with engine.begin() as conn:
        Base.metadata.drop_all(bind=conn)
        Base.metadata.create_all(bind=conn)
    print("Database schema created:", [table.name for table in Base.metadata.sorted_tables], flush=True)

    for file_name, model, columns in CSV_MAP:
        ingest_table(file_name, model, columns)

    print("Ingestion complete.", flush=True)


if __name__ == "__main__":
    main()
