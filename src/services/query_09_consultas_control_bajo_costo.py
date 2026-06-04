from __future__ import annotations

from src.utils.mongo import get_mongo_database


# Consultas de tipo Control con costo menor a 5000
def obtener_consultas_control_con_costo_menor_a_5000() -> list[dict]:
    db = get_mongo_database()

    pipeline = [
        {
            "$match": {
                "motivo": {"$regex": "control", "$options": "i"},
                "costo": {"$lt": 5000},
            }
        },
        {
            "$lookup": {
                "from": "pacientes",
                "localField": "id_paciente",
                "foreignField": "id_paciente",
                "as": "paciente",
            }
        },
        {"$unwind": "$paciente"},
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
                    "fecha": "$fecha",
                    "motivo": "$motivo",
                    "diagnostico": "$diagnostico",
                    "costo": "$costo",
                    "estado": "$estado",
                },
                "paciente": {
                    "id_paciente": "$paciente.id_paciente",
                    "nombre": "$paciente.nombre",
                    "especie": "$paciente.especie",
                    "raza": "$paciente.raza",
                },
                "veterinario": {
                    "id_vet": "$veterinario.id_vet",
                    "nombre": "$veterinario.nombre",
                    "apellido": "$veterinario.apellido",
                    "especialidad": "$veterinario.especialidad",
                    "sucursal": "$veterinario.sucursal",
                },
            }
        },
        {"$sort": {"consulta.fecha": 1, "consulta.id_consulta": 1}},
    ]

    return list(db.consultas.aggregate(pipeline))
