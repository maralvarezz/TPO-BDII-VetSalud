from __future__ import annotations

from datetime import datetime

from src.utils.mongo import get_mongo_database


# Pacientes activos con vacunas vencidas segun la fecha de proxima dosis
def obtener_pacientes_con_vacunas_vencidas() -> list[dict]:
    db = get_mongo_database()
    fecha_actual = datetime.now()

    pipeline = [
        {"$match": {"proxima_dosis": {"$lt": fecha_actual}}},
        {
            "$lookup": {
                "from": "pacientes",
                "localField": "id_paciente",
                "foreignField": "id_paciente",
                "as": "paciente",
            }
        },
        {"$unwind": "$paciente"},
        {"$match": {"paciente.activo": True}},
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
                "paciente": {
                    "id_paciente": "$paciente.id_paciente",
                    "nombre": "$paciente.nombre",
                    "especie": "$paciente.especie",
                    "raza": "$paciente.raza",
                    "activo": "$paciente.activo",
                },
                "vacuna": {
                    "id_vacuna": "$id_vacuna",
                    "nombre_vacuna": "$nombre_vacuna",
                    "fecha_aplicacion": "$fecha_aplicacion",
                    "proxima_dosis": "$proxima_dosis",
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
        {"$sort": {"vacuna.proxima_dosis": 1, "paciente.id_paciente": 1}},
    ]

    return list(db.vacunaciones.aggregate(pipeline))
