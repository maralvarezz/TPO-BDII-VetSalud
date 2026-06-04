from __future__ import annotations

from src.utils.mongo import get_mongo_database


# Top 5 diagnosticos mas frecuentes en consultas medicas
def obtener_top_5_diagnosticos_mas_frecuentes() -> list[dict]:
    db = get_mongo_database()

    pipeline = [
        {
            "$group": {
                "_id": "$diagnostico",
                "cantidad": {"$sum": 1},
            }
        },
        {
            "$project": {
                "_id": 0,
                "diagnostico": "$_id",
                "cantidad": 1,
            }
        },
        {"$sort": {"cantidad": -1, "diagnostico": 1}},
        {"$limit": 5},
    ]

    return list(db.consultas.aggregate(pipeline))
