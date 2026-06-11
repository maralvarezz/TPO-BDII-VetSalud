from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from src.utils.mongo import get_mongo_database


ESTADOS_CONSULTA = {"Cerrada", "Seguimiento"}


def _parse_payload(payload_json: str | None) -> dict[str, Any]:
    if payload_json is None:
        raise ValueError("Debe informar un payload JSON con los datos de la consulta.")

    try:
        payload = json.loads(payload_json)
    except json.JSONDecodeError as exc:
        raise ValueError("El payload debe ser un JSON valido.") from exc

    if not isinstance(payload, dict):
        raise ValueError("El payload JSON debe ser un objeto.")

    return payload


def _require_non_empty(payload: dict[str, Any], fields: set[str]) -> None:
    empty_fields = sorted(
        field
        for field in fields
        if isinstance(payload.get(field), str) and not payload[field].strip()
    )
    if empty_fields:
        raise ValueError(f"Los campos no pueden estar vacios: {', '.join(empty_fields)}")


def _parse_fecha(value: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("La fecha debe tener formato YYYY-MM-DD.") from exc


def _parse_costo(value: Any) -> float:
    try:
        costo = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("El costo debe ser numerico.") from exc

    if costo < 0:
        raise ValueError("El costo no puede ser negativo.")

    return costo


def registrar_nueva_consulta(payload: dict[str, Any]) -> dict[str, Any]:
    required_fields = {
        "id_consulta",
        "id_paciente",
        "id_vet",
        "fecha",
        "motivo",
        "diagnostico",
        "costo",
        "estado",
    }
    missing_fields = sorted(required_fields - payload.keys())
    if missing_fields:
        raise ValueError(f"Faltan campos obligatorios: {', '.join(missing_fields)}")
    _require_non_empty(payload, required_fields)

    id_consulta = str(payload["id_consulta"]).strip()
    id_paciente = str(payload["id_paciente"]).strip()
    id_vet = str(payload["id_vet"]).strip()
    estado = str(payload["estado"]).strip()
    if estado not in ESTADOS_CONSULTA:
        estados_validos = ", ".join(sorted(ESTADOS_CONSULTA))
        raise ValueError(f"Estado invalido. Use: {estados_validos}.")

    db = get_mongo_database()
    if db.consultas.find_one({"id_consulta": id_consulta}):
        raise ValueError(f"Ya existe la consulta {id_consulta}.")

    paciente = db.pacientes.find_one({"id_paciente": id_paciente, "activo": True})
    if paciente is None:
        raise ValueError(f"No existe un paciente activo con id {id_paciente}.")

    veterinario = db.veterinarios.find_one({"id_vet": id_vet, "activo": True})
    if veterinario is None:
        raise ValueError(f"No existe un veterinario activo con id {id_vet}.")

    consulta = {
        "id_consulta": id_consulta,
        "id_paciente": id_paciente,
        "id_vet": id_vet,
        "fecha": _parse_fecha(str(payload["fecha"])),
        "motivo": str(payload["motivo"]).strip(),
        "diagnostico": str(payload["diagnostico"]).strip(),
        "costo": _parse_costo(payload["costo"]),
        "estado": estado,
    }
    db.consultas.insert_one(consulta)

    consulta_salida = {key: value for key, value in consulta.items() if key != "_id"}
    return {
        "operacion": "registro_consulta",
        "consulta": consulta_salida,
        "paciente_validado": {
            "id_paciente": paciente["id_paciente"],
            "nombre": paciente["nombre"],
            "activo": paciente.get("activo", True),
        },
        "veterinario_validado": {
            "id_vet": veterinario["id_vet"],
            "nombre": veterinario["nombre"],
            "apellido": veterinario["apellido"],
            "activo": veterinario.get("activo", True),
        },
    }


# Registro de nueva consulta medica con validacion de paciente y veterinario existentes
def registrar_nueva_consulta_desde_json(payload_json: str | None = None) -> dict[str, Any]:
    return registrar_nueva_consulta(_parse_payload(payload_json))
