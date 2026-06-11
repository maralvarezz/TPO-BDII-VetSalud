from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from pymongo import ReturnDocument

from src.utils.mongo import get_mongo_database


ALLOWED_UPDATE_FIELDS = {
    "nombre",
    "apellido",
    "dni",
    "email",
    "telefono",
    "ciudad",
    "provincia",
}


def _require_non_empty(payload: dict[str, Any], fields: set[str]) -> None:
    empty_fields = sorted(
        field
        for field in fields
        if isinstance(payload.get(field), str) and not payload[field].strip()
    )
    if empty_fields:
        raise ValueError(f"Los campos no pueden estar vacios: {', '.join(empty_fields)}")


def _parse_payload(payload_json: str | None) -> dict[str, Any]:
    if payload_json is None:
        raise ValueError("Debe informar un payload JSON.")

    try:
        payload = json.loads(payload_json)
    except json.JSONDecodeError as exc:
        raise ValueError("El payload debe ser un JSON valido.") from exc

    if not isinstance(payload, dict):
        raise ValueError("El payload JSON debe ser un objeto.")

    return payload


def _project_propietario(doc: dict[str, Any]) -> dict[str, Any]:
    return {
        "id_propietario": doc["id_propietario"],
        "nombre": doc["nombre"],
        "apellido": doc["apellido"],
        "dni": doc["dni"],
        "email": doc["email"],
        "telefono": doc["telefono"],
        "ciudad": doc["ciudad"],
        "provincia": doc["provincia"],
        "activo": doc.get("activo", True),
        "fecha_alta": doc.get("fecha_alta"),
        "fecha_baja": doc.get("fecha_baja"),
    }


def alta_propietario(payload: dict[str, Any]) -> dict[str, Any]:
    required_fields = {
        "id_propietario",
        "nombre",
        "apellido",
        "dni",
        "email",
        "telefono",
        "ciudad",
        "provincia",
    }
    missing_fields = sorted(required_fields - payload.keys())
    if missing_fields:
        raise ValueError(f"Faltan campos obligatorios: {', '.join(missing_fields)}")
    _require_non_empty(payload, required_fields)

    db = get_mongo_database()
    if db.propietarios.find_one({"id_propietario": payload["id_propietario"]}):
        raise ValueError(f"Ya existe el propietario {payload['id_propietario']}.")
    if db.propietarios.find_one({"dni": payload["dni"]}):
        raise ValueError(f"Ya existe un propietario con DNI {payload['dni']}.")

    propietario = {
        "id_propietario": payload["id_propietario"],
        "nombre": payload["nombre"],
        "apellido": payload["apellido"],
        "dni": payload["dni"],
        "email": payload["email"],
        "telefono": payload["telefono"],
        "ciudad": payload["ciudad"],
        "provincia": payload["provincia"],
        "activo": True,
        "fecha_alta": datetime.now(),
        "fecha_baja": None,
    }
    db.propietarios.insert_one(propietario)

    return {"operacion": "alta", "propietario": _project_propietario(propietario)}


def modificar_propietario(payload: dict[str, Any]) -> dict[str, Any]:
    id_propietario = payload.get("id_propietario")
    if not id_propietario:
        raise ValueError("Debe informar id_propietario.")

    updates = {
        key: value
        for key, value in payload.items()
        if key in ALLOWED_UPDATE_FIELDS and key != "id_propietario"
    }
    if not updates:
        raise ValueError("Debe informar al menos un campo modificable.")
    _require_non_empty(updates, set(updates.keys()))

    db = get_mongo_database()
    if "dni" in updates:
        duplicated = db.propietarios.find_one(
            {"dni": updates["dni"], "id_propietario": {"$ne": id_propietario}}
        )
        if duplicated is not None:
            raise ValueError(f"Ya existe otro propietario con DNI {updates['dni']}.")

    updated = db.propietarios.find_one_and_update(
        {"id_propietario": id_propietario},
        {"$set": updates},
        return_document=ReturnDocument.AFTER,
    )
    if updated is None:
        raise ValueError(f"No existe el propietario {id_propietario}.")

    return {"operacion": "modificacion", "propietario": _project_propietario(updated)}


def baja_logica_propietario(payload: dict[str, Any]) -> dict[str, Any]:
    id_propietario = payload.get("id_propietario")
    if not id_propietario:
        raise ValueError("Debe informar id_propietario.")

    db = get_mongo_database()
    updated = db.propietarios.find_one_and_update(
        {"id_propietario": id_propietario, "activo": {"$ne": False}},
        {"$set": {"activo": False, "fecha_baja": datetime.now()}},
        return_document=ReturnDocument.AFTER,
    )
    if updated is None:
        existing = db.propietarios.find_one({"id_propietario": id_propietario})
        if existing is None:
            raise ValueError(f"No existe el propietario {id_propietario}.")
        raise ValueError(f"El propietario {id_propietario} ya esta dado de baja.")

    return {"operacion": "baja_logica", "propietario": _project_propietario(updated)}


# ABM completo de propietarios: alta, modificacion de datos y baja logica
def ejecutar_abm_propietario(accion: str, payload_json: str | None = None) -> dict[str, Any]:
    payload = _parse_payload(payload_json)
    accion_normalizada = accion.strip().lower()

    if accion_normalizada == "alta":
        return alta_propietario(payload)
    if accion_normalizada in {"modificacion", "modificar"}:
        return modificar_propietario(payload)
    if accion_normalizada in {"baja", "baja_logica"}:
        return baja_logica_propietario(payload)

    raise ValueError("Accion invalida. Use: alta, modificacion o baja.")
