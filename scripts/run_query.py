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
from src.services.query_10_pacientes_por_sucursal import (  # noqa: E402
    DEFAULT_SUCURSAL,
    obtener_pacientes_de_sucursal,
)
from src.services.query_11_ingresos_veterinario_mes_actual import (  # noqa: E402
    obtener_ingresos_totales_por_veterinario_mes_actual,
)
from src.services.query_12_propietarios_sin_consultas_ultimo_anio import (  # noqa: E402
    obtener_propietarios_sin_consultas_ultimo_anio,
)
from src.services.query_13_abm_propietarios import (  # noqa: E402
    ejecutar_abm_propietario,
)
from src.services.query_14_registrar_consulta import (  # noqa: E402
    registrar_nueva_consulta_desde_json,
)
from src.services.query_15_actualizar_stock import (  # noqa: E402
    actualizar_stock_productos_desde_json,
    decrementar_stock_producto_desde_args,
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
    "10": QuerySpec(
        name="query_10",
        engine="neo4j",
        handler=obtener_pacientes_de_sucursal,
    ),
    "11": QuerySpec(
        name="query_11",
        engine="mongodb",
        handler=obtener_ingresos_totales_por_veterinario_mes_actual,
    ),
    "12": QuerySpec(
        name="query_12",
        engine="neo4j",
        handler=obtener_propietarios_sin_consultas_ultimo_anio,
    ),
    "13": QuerySpec(
        name="query_13",
        engine="mongodb",
        handler=ejecutar_abm_propietario,
    ),
    "14": QuerySpec(
        name="query_14",
        engine="mongodb",
        handler=registrar_nueva_consulta_desde_json,
    ),
    "15": QuerySpec(
        name="query_15",
        engine="mongodb",
        handler=decrementar_stock_producto_desde_args,
    ),
}


def print_available_queries() -> None:
    for key, spec in QUERY_SPECS.items():
        print(f"- {key} [{spec.engine}]")


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python3 scripts/run_query.py <numero_query> [argumentos]", file=sys.stderr)
        print(
            "Ejemplos: 1 | 3 P001 | 10 Palermo | 11 05/2026 | 12 | "
            "13 alta '{...}' | 14 '{...}' | 15 PRD001 2 | 15 '[...]'",
            file=sys.stderr,
        )
        print("Queries disponibles:", file=sys.stderr)
        print_available_queries()
        sys.exit(1)

    query_id = sys.argv[1]
    args = sys.argv[2:]
    spec = QUERY_SPECS.get(query_id)

    if spec is None:
        print(f"Query no implementada: {query_id}", file=sys.stderr)
        print("Queries disponibles:", file=sys.stderr)
        print_available_queries()
        sys.exit(1)

    queries_con_argumento = {"3", "10", "11", "13", "14", "15"}
    if args and query_id not in queries_con_argumento:
        print("Esta query no recibe argumentos adicionales.", file=sys.stderr)
        sys.exit(1)

    try:
        if query_id == "3":
            if len(args) > 1:
                raise ValueError("La query 3 recibe como maximo un id de paciente.")
            id_paciente = args[0] if args else DEFAULT_ID_PACIENTE
            resultados = spec.handler(id_paciente)
        elif query_id == "10":
            if len(args) > 1:
                raise ValueError("La query 10 recibe como maximo una sucursal.")
            sucursal = args[0] if args else DEFAULT_SUCURSAL
            resultados = spec.handler(sucursal)
        elif query_id == "11":
            if len(args) > 1:
                raise ValueError("La query 11 recibe como maximo un periodo MM/YYYY.")
            periodo = args[0] if args else None
            resultados = spec.handler(periodo)
        elif query_id == "13":
            if len(args) != 2:
                raise ValueError("Uso query 13: 13 <alta|modificacion|baja> '<payload_json>'")
            resultados = spec.handler(args[0], args[1])
        elif query_id == "14":
            if len(args) != 1:
                raise ValueError("Uso query 14: 14 '<payload_json>'")
            resultados = spec.handler(args[0])
        elif query_id == "15":
            if len(args) == 1:
                resultados = actualizar_stock_productos_desde_json(args[0])
            elif len(args) == 2:
                resultados = spec.handler(args[0], args[1])
            else:
                raise ValueError(
                    "Uso query 15: 15 <id_producto> <cantidad> | 15 '<payload_json>'"
                )
        else:
            if args:
                raise ValueError("Esta query no recibe argumentos adicionales.")
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
