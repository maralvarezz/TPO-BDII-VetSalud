from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

from neo4j.exceptions import Neo4jError
from pymongo.errors import PyMongoError


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.query_registry import QUERY_SPECS, execute_query  # noqa: E402


def json_default(value):
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    raise TypeError(f"Tipo no serializable: {type(value)!r}")


def print_available_queries() -> None:
    for key, spec in QUERY_SPECS.items():
        print(f"- {key} [{spec.engine}]")


def main() -> None:
    if len(sys.argv) not in (2, 3):
        print("Uso: python3 scripts/run_query.py <numero_query> [argumento]", file=sys.stderr)
        print("Ejemplos: 1 | 3 P001 | 10 Palermo | 11 05/2026 | 12", file=sys.stderr)
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

    if len(sys.argv) == 3 and spec.parameter_name is None:
        print("Esta query no recibe argumentos adicionales.", file=sys.stderr)
        sys.exit(1)

    try:
        argument = sys.argv[2] if len(sys.argv) == 3 else None
        resultados = execute_query(query_id, argument)
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
