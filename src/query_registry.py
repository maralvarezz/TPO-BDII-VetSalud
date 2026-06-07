from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from src.services.query_01_pacientes_activos import (
    obtener_pacientes_activos_con_propietario,
)
from src.services.query_02_consultas_abiertas import (
    obtener_consultas_abiertas_con_veterinario_y_costo,
)
from src.services.query_03_historial_paciente import (
    DEFAULT_ID_PACIENTE,
    obtener_historial_completo_paciente,
)
from src.services.query_04_propietarios_mas_de_un_paciente import (
    obtener_propietarios_con_mas_de_un_paciente,
)
from src.services.query_05_veterinarios_activos_ultimos_60_dias import (
    obtener_veterinarios_activos_con_consultas_ultimos_60_dias,
)
from src.services.query_06_pacientes_vacunas_vencidas import (
    obtener_pacientes_con_vacunas_vencidas,
)
from src.services.query_07_top_diagnosticos import (
    obtener_top_5_diagnosticos_mas_frecuentes,
)
from src.services.query_08_stock_bajo import (
    obtener_stock_productos_menos_de_50_unidades,
)
from src.services.query_09_consultas_control_bajo_costo import (
    obtener_consultas_control_con_costo_menor_a_5000,
)
from src.services.query_10_pacientes_por_sucursal import (
    DEFAULT_SUCURSAL,
    obtener_pacientes_de_sucursal,
)
from src.services.query_11_ingresos_veterinario_mes_actual import (
    obtener_ingresos_totales_por_veterinario_mes_actual,
)
from src.services.query_12_propietarios_sin_consultas_ultimo_anio import (
    obtener_propietarios_sin_consultas_ultimo_anio,
)


@dataclass(frozen=True)
class QuerySpec:
    id: str
    name: str
    title: str
    description: str
    engine: str
    language: str
    handler: Callable[..., Any]
    parameter_name: str | None = None
    parameter_label: str | None = None
    parameter_placeholder: str | None = None
    parameter_default: str | None = None


QUERY_SPECS: dict[str, QuerySpec] = {
    "1": QuerySpec(
        id="1",
        name="query_01",
        title="Pacientes activos con propietario",
        description="Lista pacientes activos junto con todos los datos de su propietario.",
        engine="mongodb",
        language="Aggregation Pipeline",
        handler=obtener_pacientes_activos_con_propietario,
    ),
    "2": QuerySpec(
        id="2",
        name="query_02",
        title="Consultas abiertas en seguimiento",
        description="Muestra consultas médicas abiertas con veterinario asignado y costo.",
        engine="mongodb",
        language="Aggregation Pipeline",
        handler=obtener_consultas_abiertas_con_veterinario_y_costo,
    ),
    "3": QuerySpec(
        id="3",
        name="query_03",
        title="Historial completo de paciente",
        description="Combina consultas y vacunaciones de un paciente ordenadas por fecha.",
        engine="neo4j",
        language="Cypher",
        handler=obtener_historial_completo_paciente,
        parameter_name="id_paciente",
        parameter_label="ID del paciente",
        parameter_placeholder="P001",
        parameter_default=DEFAULT_ID_PACIENTE,
    ),
    "4": QuerySpec(
        id="4",
        name="query_04",
        title="Propietarios con más de un paciente",
        description="Detecta propietarios vinculados a dos o más pacientes.",
        engine="neo4j",
        language="Cypher",
        handler=obtener_propietarios_con_mas_de_un_paciente,
    ),
    "5": QuerySpec(
        id="5",
        name="query_05",
        title="Veterinarios activos con consultas en 60 días",
        description="Cuenta consultas recientes por veterinario activo.",
        engine="mongodb",
        language="Aggregation Pipeline",
        handler=obtener_veterinarios_activos_con_consultas_ultimos_60_dias,
    ),
    "6": QuerySpec(
        id="6",
        name="query_06",
        title="Pacientes con vacunas vencidas",
        description="Muestra vacunas vencidas y el paciente asociado.",
        engine="mongodb",
        language="Aggregation Pipeline",
        handler=obtener_pacientes_con_vacunas_vencidas,
    ),
    "7": QuerySpec(
        id="7",
        name="query_07",
        title="Top 5 diagnósticos",
        description="Ranking de diagnósticos más frecuentes.",
        engine="mongodb",
        language="Aggregation Pipeline",
        handler=obtener_top_5_diagnosticos_mas_frecuentes,
    ),
    "8": QuerySpec(
        id="8",
        name="query_08",
        title="Stock bajo",
        description="Productos con menos de 50 unidades y su proveedor.",
        engine="mongodb",
        language="find / Aggregation Pipeline",
        handler=obtener_stock_productos_menos_de_50_unidades,
    ),
    "9": QuerySpec(
        id="9",
        name="query_09",
        title="Controles de bajo costo",
        description="Consultas de control con costo menor a 5000.",
        engine="mongodb",
        language="find / Aggregation Pipeline",
        handler=obtener_consultas_control_con_costo_menor_a_5000,
    ),
    "10": QuerySpec(
        id="10",
        name="query_10",
        title="Pacientes por sucursal",
        description="Lista pacientes de una sucursal a través del veterinario.",
        engine="neo4j",
        language="Cypher",
        handler=obtener_pacientes_de_sucursal,
        parameter_name="sucursal",
        parameter_label="Sucursal",
        parameter_placeholder="Palermo",
        parameter_default=DEFAULT_SUCURSAL,
    ),
    "11": QuerySpec(
        id="11",
        name="query_11",
        title="Ingresos mensuales por veterinario",
        description="Vista agregada de ingresos totales por veterinario en un período mensual.",
        engine="mongodb",
        language="Aggregation Pipeline / vista materializada",
        handler=obtener_ingresos_totales_por_veterinario_mes_actual,
        parameter_name="periodo",
        parameter_label="Período",
        parameter_placeholder="05/2026",
        parameter_default="05/2026",
    ),
    "12": QuerySpec(
        id="12",
        name="query_12",
        title="Propietarios sin consultas en el último año",
        description="Propietarios cuyos pacientes no registran consultas en los últimos 12 meses.",
        engine="neo4j",
        language="Cypher",
        handler=obtener_propietarios_sin_consultas_ultimo_anio,
    ),
}


def execute_query(query_id: str, argument: str | None = None) -> Any:
    spec = QUERY_SPECS[query_id]
    if spec.parameter_name is None:
        return spec.handler()
    if argument is None or argument == "":
        return spec.handler(spec.parameter_default)
    return spec.handler(argument)
