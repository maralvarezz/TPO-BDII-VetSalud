from __future__ import annotations

from src.utils.mongo import get_mongo_database

# Consultas médicas abiertas (estado 'Seguimiento') con veterinario asignado y costo
def obtener_consultas_abiertas_con_veterinario_y_costo() -> list[dict]:
    db = get_mongo_database()

    pipeline = [
        {"$match": {"estado": "Seguimiento"}},
        {
            "$lookup": {
                "from": "veterinarios",
                "localField": "id_vet",
                "foreignField": "id_vet",
                "as": "veterinario",
            }
        },
        {"$unwind": "$veterinario"},
        {
            "$project": {
                "_id": 0,
                "consulta": {
                    "id_consulta": "$id_consulta",
                    "id_paciente": "$id_paciente",
                    "fecha": "$fecha",
                    "motivo": "$motivo",
                    "diagnostico": "$diagnostico",
                    "costo": "$costo",
                    "estado": "$estado",
                },
                "veterinario": {
                    "id_vet": "$veterinario.id_vet",
                    "nombre": "$veterinario.nombre",
                    "apellido": "$veterinario.apellido",
                    "matricula": "$veterinario.matricula",
                    "especialidad": "$veterinario.especialidad",
                    "sucursal": "$veterinario.sucursal",
                    "activo": "$veterinario.activo",
                },
            }
        },
        {"$sort": {"consulta.fecha": 1, "consulta.id_consulta": 1}},
    ]

    return list(db.consultas.aggregate(pipeline))
