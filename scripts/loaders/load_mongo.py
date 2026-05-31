from __future__ import annotations

import csv
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "datasets_enriquecidos"


def parse_bool(value: str) -> bool:
    return value.strip().lower() == "true"


def parse_date(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d")


def read_csv(name: str) -> list[dict[str, object]]:
    path = DATA_DIR / name
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def transform_propietarios(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    docs = []
    for row in rows:
        docs.append(
            {
                "id_propietario": row["id_propietario"],
                "nombre": row["nombre"],
                "apellido": row["apellido"],
                "dni": row["dni"],
                "email": row["email"],
                "telefono": row["telefono"],
                "ciudad": row["ciudad"],
                "provincia": row["provincia"],
                "activo": True,
                "fecha_alta": None,
                "fecha_baja": None,
            }
        )
    return docs


def transform_pacientes(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    docs = []
    for row in rows:
        docs.append(
            {
                "id_paciente": row["id_paciente"],
                "nombre": row["nombre"],
                "especie": row["especie"],
                "raza": row["raza"],
                "fecha_nac": parse_date(str(row["fecha_nac"])),
                "id_propietario": row["id_propietario"],
                "activo": parse_bool(str(row["activo"])),
            }
        )
    return docs


def transform_veterinarios(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    docs = []
    for row in rows:
        docs.append(
            {
                "id_vet": row["id_vet"],
                "nombre": row["nombre"],
                "apellido": row["apellido"],
                "matricula": row["matricula"],
                "especialidad": row["especialidad"],
                "sucursal": row["sucursal"],
                "activo": parse_bool(str(row["activo"])),
            }
        )
    return docs


def transform_consultas(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    docs = []
    for row in rows:
        docs.append(
            {
                "id_consulta": row["id_consulta"],
                "id_paciente": row["id_paciente"],
                "id_vet": row["id_vet"],
                "fecha": parse_date(str(row["fecha"])),
                "motivo": row["motivo"],
                "diagnostico": row["diagnostico"],
                "costo": float(row["costo"]),
                "estado": row["estado"],
            }
        )
    return docs


def transform_vacunaciones(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    docs = []
    for row in rows:
        docs.append(
            {
                "id_vacuna": row["id_vacuna"],
                "id_paciente": row["id_paciente"],
                "id_vet": row["id_vet"],
                "fecha_aplicacion": parse_date(str(row["fecha_aplicacion"])),
                "nombre_vacuna": row["nombre_vacuna"],
                "proxima_dosis": parse_date(str(row["proxima_dosis"])),
            }
        )
    return docs


def transform_stock(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    docs = []
    for row in rows:
        docs.append(
            {
                "id_producto": row["id_producto"],
                "nombre": row["nombre"],
                "categoria": row["categoria"],
                "unidades": int(row["unidades"]),
                "precio_unit": float(row["precio_unit"]),
                "vencimiento": parse_date(str(row["vencimiento"])),
                "proveedor": row["proveedor"],
                "activo": True,
            }
        )
    return docs


def recreate_collection(db, name: str, docs: list[dict[str, object]]) -> None:
    collection = db[name]
    collection.delete_many({})
    if docs:
        collection.insert_many(docs)


def main() -> None:
    load_dotenv()
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    mongo_db = os.getenv("MONGO_DB", "vetsalud")

    client = MongoClient(mongo_uri)
    db = client[mongo_db]

    recreate_collection(db, "propietarios", transform_propietarios(read_csv("propietarios.csv")))
    recreate_collection(db, "pacientes", transform_pacientes(read_csv("pacientes.csv")))
    recreate_collection(db, "veterinarios", transform_veterinarios(read_csv("veterinarios.csv")))
    recreate_collection(db, "consultas", transform_consultas(read_csv("consultas.csv")))
    recreate_collection(db, "vacunaciones", transform_vacunaciones(read_csv("vacunaciones.csv")))
    recreate_collection(db, "stock_farmaceutico", transform_stock(read_csv("stock_farmaceutico.csv")))

    print(f"Carga MongoDB completa en base '{mongo_db}'.")


if __name__ == "__main__":
    main()
