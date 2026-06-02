from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from neo4j.exceptions import Neo4jError
from pymongo.errors import PyMongoError


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.services.query_01_pacientes_activos import (  # noqa: E402
    obtener_pacientes_activos_con_propietario,
)
from src.services.query_02_consultas_abiertas import (  # noqa: E402
    obtener_consultas_abiertas_con_veterinario_y_costo,
)
from src.services.query_04_propietarios_mas_de_un_paciente import (  # noqa: E402
    obtener_propietarios_con_mas_de_un_paciente,
)


@dataclass(frozen=True)
class QuerySpec:
    name: str
    engine: str
    handler: callable


def json_default(value):
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    raise TypeError(f"Tipo no serializable: {type(value)!r}")


QUERY_SPECS = {
    "1": QuerySpec(
        name="query_01",
        engine="mongodb",
        handler=obtener_pacientes_activos_con_propietario,
    ),
    "2": QuerySpec(
        name="query_02",
        engine="mongodb",
        handler=obtener_consultas_abiertas_con_veterinario_y_costo,
    ),
    "4": QuerySpec(
        name="query_04",
        engine="neo4j",
        handler=obtener_propietarios_con_mas_de_un_paciente,
    ),
}


def print_available_queries() -> None:
    for key, spec in QUERY_SPECS.items():
        print(f"- {key} [{spec.engine}]")


def main() -> None:
    if len(sys.argv) != 2:
        print("Uso: python3 scripts/run_query.py <numero_query>", file=sys.stderr)
        print("Ejemplos: 1 | 2 | 4", file=sys.stderr)
        print("Queries disponibles:", file=sys.stderr)
        print_available_queries()
        sys.exit(1)

    query_id = sys.argv[1]
    spec = QUERY_SPECS.get(query_id)

    if spec is None:
        print(f"Query no implementada: {query_id}", file=sys.stderr)
        print("Queries disponibles:", file=sys.stderr)
        print_available_queries()
        sys.exit(1)

    try:
        resultados = spec.handler()
    except PyMongoError as exc:
        print(f"Error al consultar MongoDB: {exc}", file=sys.stderr)
        sys.exit(1)
    except Neo4jError as exc:
        print(f"Error al consultar Neo4j: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Error al ejecutar {spec.name} sobre {spec.engine}: {exc}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(resultados, indent=2, ensure_ascii=False, default=json_default))


if __name__ == "__main__":
    main()
