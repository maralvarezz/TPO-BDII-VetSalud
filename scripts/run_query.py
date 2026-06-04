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
from src.services.query_03_historial_paciente import (  # noqa: E402
    DEFAULT_ID_PACIENTE,
    obtener_historial_completo_paciente,
)
from src.services.query_04_propietarios_mas_de_un_paciente import (  # noqa: E402
    obtener_propietarios_con_mas_de_un_paciente,
)
from src.services.query_05_veterinarios_activos_ultimos_60_dias import (  # noqa: E402
    obtener_veterinarios_activos_con_consultas_ultimos_60_dias,
)
from src.services.query_06_pacientes_vacunas_vencidas import (  # noqa: E402
    obtener_pacientes_con_vacunas_vencidas,
)
from src.services.query_07_top_diagnosticos import (  # noqa: E402
    obtener_top_5_diagnosticos_mas_frecuentes,
)
from src.services.query_08_stock_bajo import (  # noqa: E402
    obtener_stock_productos_menos_de_50_unidades,
)
from src.services.query_09_consultas_control_bajo_costo import (  # noqa: E402
    obtener_consultas_control_con_costo_menor_a_5000,
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
    "3": QuerySpec(
        name="query_03",
        engine="neo4j",
        handler=obtener_historial_completo_paciente,
    ),
    "4": QuerySpec(
        name="query_04",
        engine="neo4j",
        handler=obtener_propietarios_con_mas_de_un_paciente,
    ),
    "5": QuerySpec(
        name="query_05",
        engine="mongodb",
        handler=obtener_veterinarios_activos_con_consultas_ultimos_60_dias,
    ),
    "6": QuerySpec(
        name="query_06",
        engine="mongodb",
        handler=obtener_pacientes_con_vacunas_vencidas,
    ),
    "7": QuerySpec(
        name="query_07",
        engine="mongodb",
        handler=obtener_top_5_diagnosticos_mas_frecuentes,
    ),
    "8": QuerySpec(
        name="query_08",
        engine="mongodb",
        handler=obtener_stock_productos_menos_de_50_unidades,
    ),
    "9": QuerySpec(
        name="query_09",
        engine="mongodb",
        handler=obtener_consultas_control_con_costo_menor_a_5000,
    ),
}


def print_available_queries() -> None:
    for key, spec in QUERY_SPECS.items():
        print(f"- {key} [{spec.engine}]")


def main() -> None:
    if len(sys.argv) not in (2, 3):
        print("Uso: python3 scripts/run_query.py <numero_query> [id_paciente]", file=sys.stderr)
        print("Ejemplos: 1 | 2 | 3 P001 | 4 | 5 | 6 | 7 | 8 | 9", file=sys.stderr)
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

    if len(sys.argv) == 3 and query_id != "3":
        print("El parametro id_paciente solo aplica a la query 3.", file=sys.stderr)
        sys.exit(1)

    try:
        if query_id == "3":
            id_paciente = sys.argv[2] if len(sys.argv) == 3 else DEFAULT_ID_PACIENTE
            resultados = spec.handler(id_paciente)
        else:
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
