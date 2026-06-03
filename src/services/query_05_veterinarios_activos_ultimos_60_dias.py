from __future__ import annotations

from datetime import datetime, timedelta

from src.utils.mongo import get_mongo_database


# Veterinarios activos y cantidad de consultas realizadas en los ultimos 60 dias
def obtener_veterinarios_activos_con_consultas_ultimos_60_dias() -> list[dict]:
    db = get_mongo_database()
    fecha_desde = datetime.now() - timedelta(days=60)

    pipeline = [
        {"$match": {"activo": True}},
        {
            "$lookup": {
                "from": "consultas",
                "let": {"id_vet": "$id_vet"},
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {
                                "$and": [
                                    {"$eq": ["$id_vet", "$$id_vet"]},
                                    {"$gte": ["$fecha", fecha_desde]},
                                ]
                            }
                        }
                    }
                ],
                "as": "consultas_ultimos_60_dias",
            }
        },
        {
            "$project": {
                "_id": 0,
                "id_vet": 1,
                "nombre": 1,
                "apellido": 1,
                "matricula": 1,
                "especialidad": 1,
                "sucursal": 1,
                "activo": 1,
                "cantidad_consultas_ultimos_60_dias": {
                    "$size": "$consultas_ultimos_60_dias"
                },
            }
        },
        {"$sort": {"cantidad_consultas_ultimos_60_dias": -1, "id_vet": 1}},
    ]

    return list(db.veterinarios.aggregate(pipeline))
