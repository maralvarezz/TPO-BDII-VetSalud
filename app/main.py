from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from neo4j.exceptions import Neo4jError
from pymongo.errors import PyMongoError
from starlette.templating import Jinja2Templates

from src.query_registry import QUERY_SPECS, execute_query


BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(
    title="VetSalud Backoffice",
    description="Backoffice interactivo para consultas MongoDB y Neo4j.",
)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


def json_default(value):
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    raise TypeError(f"Tipo no serializable: {type(value)!r}")


def serialize_for_ui(value):
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, dict):
        return {key: serialize_for_ui(item) for key, item in value.items()}
    if isinstance(value, list):
        return [serialize_for_ui(item) for item in value]
    return value


def infer_table_columns(resultados):
    if not isinstance(resultados, list) or not resultados:
        return []
    first = resultados[0]
    if not isinstance(first, dict):
        return []
    return list(first.keys())


def build_graph_data(query_id: str, resultados_ui):
    if not isinstance(resultados_ui, list):
        return None

    nodes = []
    edges = []
    seen_nodes = set()
    seen_edges = set()

    def add_node(node_id: str, label: str, node_type: str, subtitle: str | None = None):
        if node_id in seen_nodes:
            return
        seen_nodes.add(node_id)
        nodes.append(
            {
                "data": {
                    "id": node_id,
                    "label": label,
                    "type": node_type,
                    "subtitle": subtitle or "",
                }
            }
        )

    def add_edge(source: str, target: str, label: str):
        edge_id = f"{source}->{target}:{label}"
        if edge_id in seen_edges:
            return
        seen_edges.add(edge_id)
        edges.append(
            {
                "data": {
                    "id": edge_id,
                    "source": source,
                    "target": target,
                    "label": label,
                }
            }
        )

    if query_id == "3":
        for resultado in resultados_ui:
            paciente = resultado.get("paciente")
            propietario = resultado.get("propietario")
            historial = resultado.get("historial", [])

            if not paciente:
                continue

            patient_node_id = f'paciente:{paciente["id_paciente"]}'
            add_node(patient_node_id, paciente["nombre"], "paciente", paciente["id_paciente"])

            if propietario and propietario.get("id_propietario"):
                owner_node_id = f'propietario:{propietario["id_propietario"]}'
                add_node(
                    owner_node_id,
                    f'{propietario["nombre"]} {propietario["apellido"]}',
                    "propietario",
                    propietario["id_propietario"],
                )
                add_edge(owner_node_id, patient_node_id, "POSEE")

            for evento in historial:
                detalle = evento.get("detalle", {})
                veterinario = detalle.get("veterinario")
                if evento.get("tipo") == "consulta":
                    event_id = detalle.get("id_consulta", f"consulta:{evento.get('fecha')}")
                    event_node_id = f"consulta:{event_id}"
                    add_node(event_node_id, detalle.get("motivo", "Consulta"), "consulta", event_id)
                    add_edge(patient_node_id, event_node_id, "TUVO_CONSULTA")
                    if veterinario and veterinario.get("id_vet"):
                        vet_node_id = f'veterinario:{veterinario["id_vet"]}'
                        add_node(
                            vet_node_id,
                            f'{veterinario["nombre"]} {veterinario["apellido"]}',
                            "veterinario",
                            veterinario["id_vet"],
                        )
                        add_edge(vet_node_id, event_node_id, "ATENDIO")
                elif evento.get("tipo") == "vacunacion":
                    event_id = detalle.get("id_vacuna", f"vacuna:{evento.get('fecha')}")
                    event_node_id = f"vacuna:{event_id}"
                    add_node(event_node_id, detalle.get("nombre_vacuna", "Vacuna"), "vacuna", event_id)
                    add_edge(patient_node_id, event_node_id, "RECIBIO_VACUNA")
                    if veterinario and veterinario.get("id_vet"):
                        vet_node_id = f'veterinario:{veterinario["id_vet"]}'
                        add_node(
                            vet_node_id,
                            f'{veterinario["nombre"]} {veterinario["apellido"]}',
                            "veterinario",
                            veterinario["id_vet"],
                        )
                        add_edge(vet_node_id, event_node_id, "APLICO_VACUNA")

        return {"nodes": nodes, "edges": edges}

    if query_id == "4":
        for propietario in resultados_ui:
            owner_id = propietario["id_propietario"]
            owner_node_id = f"propietario:{owner_id}"
            add_node(
                owner_node_id,
                f'{propietario["nombre"]} {propietario["apellido"]}',
                "propietario",
                owner_id,
            )

            for paciente in propietario.get("pacientes", []):
                patient_node_id = f'paciente:{paciente["id_paciente"]}'
                add_node(patient_node_id, paciente["nombre"], "paciente", paciente["id_paciente"])
                add_edge(owner_node_id, patient_node_id, "POSEE")

        return {"nodes": nodes, "edges": edges}

    if query_id == "10":
        for resultado in resultados_ui:
            sucursal = resultado.get("sucursal")
            paciente = resultado.get("paciente")
            propietario = resultado.get("propietario")
            veterinarios = resultado.get("veterinarios", [])

            if not sucursal or not paciente:
                continue

            branch_node_id = f"sucursal:{sucursal}"
            patient_node_id = f'paciente:{paciente["id_paciente"]}'

            add_node(branch_node_id, sucursal, "sucursal", "Sucursal")
            add_node(patient_node_id, paciente["nombre"], "paciente", paciente["id_paciente"])

            if propietario and propietario.get("id_propietario"):
                owner_node_id = f'propietario:{propietario["id_propietario"]}'
                add_node(
                    owner_node_id,
                    f'{propietario["nombre"]} {propietario["apellido"]}',
                    "propietario",
                    propietario["id_propietario"],
                )
                add_edge(owner_node_id, patient_node_id, "POSEE")

            for veterinario in veterinarios:
                vet_node_id = f'veterinario:{veterinario["id_vet"]}'
                add_node(
                    vet_node_id,
                    f'{veterinario["nombre"]} {veterinario["apellido"]}',
                    "veterinario",
                    veterinario["id_vet"],
                )
                add_edge(vet_node_id, branch_node_id, "TRABAJA_EN")
                add_edge(vet_node_id, patient_node_id, "ATIENDE")

        return {"nodes": nodes, "edges": edges}

    if query_id == "12":
        for resultado in resultados_ui:
            propietario = resultado.get("propietario")
            paciente = resultado.get("paciente_ultima_consulta")
            estado_consultas = resultado.get("estado_consultas")
            ultima_consulta = resultado.get("ultima_consulta")

            if not propietario:
                continue

            owner_node_id = f'propietario:{propietario["id_propietario"]}'
            add_node(
                owner_node_id,
                f'{propietario["nombre"]} {propietario["apellido"]}',
                "propietario",
                propietario["id_propietario"],
            )

            status_node_id = f"estado:{propietario['id_propietario']}"
            add_node(status_node_id, estado_consultas or "Sin datos", "estado", ultima_consulta or "Sin fecha")
            add_edge(owner_node_id, status_node_id, "ESTADO")

            if paciente and paciente.get("id_paciente"):
                patient_node_id = f'paciente:{paciente["id_paciente"]}'
                add_node(patient_node_id, paciente["nombre"], "paciente", paciente["id_paciente"])
                add_edge(owner_node_id, patient_node_id, "POSEE")
                if ultima_consulta:
                    consulta_node_id = f"ultima_consulta:{propietario['id_propietario']}"
                    add_node(consulta_node_id, ultima_consulta, "consulta", "Última consulta")
                    add_edge(patient_node_id, consulta_node_id, "ULTIMA_CONSULTA")

        return {"nodes": nodes, "edges": edges}

    return None


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    query_specs = [QUERY_SPECS[key] for key in sorted(QUERY_SPECS, key=lambda value: int(value))]
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "query_specs": query_specs,
        },
    )


@app.get("/api/queries")
def list_queries():
    return [
        {
            "id": spec.id,
            "name": spec.name,
            "title": spec.title,
            "description": spec.description,
            "engine": spec.engine,
            "language": spec.language,
            "parameter_name": spec.parameter_name,
            "parameter_default": spec.parameter_default,
        }
        for spec in [QUERY_SPECS[key] for key in sorted(QUERY_SPECS, key=lambda value: int(value))]
    ]


@app.get("/ui/query-shell/{query_id}", response_class=HTMLResponse)
def query_shell(request: Request, query_id: str):
    if query_id not in QUERY_SPECS:
        return HTMLResponse(
            "<div class='rounded-3xl border border-red-400/30 bg-red-500/10 p-6 text-red-100'>Query no implementada.</div>",
            status_code=404,
        )

    spec = QUERY_SPECS[query_id]
    return templates.TemplateResponse(
        "query_shell_fragment.html",
        {
            "request": request,
            "spec": spec,
        },
    )


@app.get("/api/queries/{query_id}")
def run_query_json(query_id: str, argument: Optional[str] = None):
    if query_id not in QUERY_SPECS:
        return JSONResponse({"error": f"Query no implementada: {query_id}"}, status_code=404)

    try:
        resultados = execute_query(query_id, argument)
    except (PyMongoError, Neo4jError, ValueError) as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)

    return JSONResponse(content=json.loads(json.dumps(resultados, default=json_default, ensure_ascii=False)))


@app.post("/ui/queries/{query_id}", response_class=HTMLResponse)
def run_query_card(
    request: Request,
    query_id: str,
    argument: Optional[str] = Form(default=None),
):
    if query_id not in QUERY_SPECS:
        return HTMLResponse(
            "<div class='rounded-3xl border border-red-400/30 bg-red-500/10 p-6 text-red-100'>Query no implementada.</div>",
            status_code=404,
        )

    spec = QUERY_SPECS[query_id]
    try:
        resultados = execute_query(query_id, argument)
        resultados_ui = serialize_for_ui(resultados)
        graph_data = build_graph_data(query_id, resultados_ui)
        payload_json = json.dumps(resultados, indent=2, ensure_ascii=False, default=json_default)
    except (PyMongoError, Neo4jError, ValueError) as exc:
        return templates.TemplateResponse(
            "result_fragment.html",
            {
                "request": request,
                "spec": spec,
                "error": str(exc),
                "resultados": None,
                "resultados_ui": None,
                "graph_data": None,
                "payload_json": None,
                "columns": [],
            },
        )

    return templates.TemplateResponse(
        "result_fragment.html",
        {
            "request": request,
            "spec": spec,
            "error": None,
            "resultados": resultados,
            "resultados_ui": resultados_ui,
            "graph_data": graph_data,
            "payload_json": payload_json,
            "columns": infer_table_columns(resultados),
        },
    )
