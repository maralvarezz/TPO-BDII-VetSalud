from __future__ import annotations

from datetime import datetime

from src.utils.mongo import get_mongo_database


VIEW_NAME = "vista_ingresos_veterinario_mensual"


def parse_periodo(periodo: str) -> datetime:
    try:
        return datetime.strptime(periodo, "%m/%Y")
    except ValueError as exc:
        raise ValueError("El periodo debe tener formato MM/YYYY. Ejemplo: 05/2026") from exc


# Ingresos totales por veterinario por periodo mensual desde una vista agregada
def obtener_ingresos_totales_por_veterinario_mes_actual(
    periodo: str | None = None,
) -> dict:
    db = get_mongo_database()
    fecha_periodo = parse_periodo(periodo) if periodo is not None else None
    fecha_base = fecha_periodo or datetime.now()
    periodo_normalizado = fecha_base.strftime("%m/%Y")

    cursor = db[VIEW_NAME].find(
        {"anio": fecha_base.year, "mes": fecha_base.month},
        {"_id": 0, "anio": 0, "mes": 0, "periodo": 0},
    ).sort([("ingresos_totales", -1), ("veterinario.id_vet", 1)])

    return {
        "periodo": periodo_normalizado,
        "ingresos_por_veterinario": list(cursor),
    }
