from __future__ import annotations

from src.utils.mongo import get_mongo_database

# Pacientes activos con todos sus datos de propietario
def obtener_pacientes_activos_con_propietario() -> list[dict]:
    db = get_mongo_database()

    pipeline = [
        {"$match": {"activo": True}},
        {
            "$lookup": {
                "from": "propietarios",
                "localField": "id_propietario",
                "foreignField": "id_propietario",
                "as": "propietario",
            }
        },
        {"$unwind": "$propietario"},
        {
            "$project": {
                "_id": 0,
                "paciente": {
                    "id_paciente": "$id_paciente",
                    "nombre": "$nombre",
                    "especie": "$especie",
                    "raza": "$raza",
                    "fecha_nac": "$fecha_nac",
                    "activo": "$activo",
                },
                "propietario": {
                    "id_propietario": "$propietario.id_propietario",
                    "nombre": "$propietario.nombre",
                    "apellido": "$propietario.apellido",
                    "dni": "$propietario.dni",
                    "email": "$propietario.email",
                    "telefono": "$propietario.telefono",
                    "ciudad": "$propietario.ciudad",
                    "provincia": "$propietario.provincia",
                    "activo": "$propietario.activo",
                },
            }
        },
        {"$sort": {"paciente.id_paciente": 1}},
    ]

    return list(db.pacientes.aggregate(pipeline))
