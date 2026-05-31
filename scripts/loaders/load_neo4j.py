from __future__ import annotations

import csv
import os
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "datasets_enriquecidos"


def parse_bool(value: str) -> bool:
    return value.strip().lower() == "true"


def read_csv(name: str) -> list[dict[str, str]]:
    path = DATA_DIR / name
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def reset_graph(tx) -> None:
    tx.run("MATCH (n) DETACH DELETE n")


def create_constraints(tx) -> None:
    statements = [
        "CREATE CONSTRAINT propietario_id IF NOT EXISTS FOR (n:Propietario) REQUIRE n.id_propietario IS UNIQUE",
        "CREATE CONSTRAINT paciente_id IF NOT EXISTS FOR (n:Paciente) REQUIRE n.id_paciente IS UNIQUE",
        "CREATE CONSTRAINT veterinario_id IF NOT EXISTS FOR (n:Veterinario) REQUIRE n.id_vet IS UNIQUE",
        "CREATE CONSTRAINT consulta_id IF NOT EXISTS FOR (n:Consulta) REQUIRE n.id_consulta IS UNIQUE",
        "CREATE CONSTRAINT vacuna_id IF NOT EXISTS FOR (n:Vacuna) REQUIRE n.id_vacuna IS UNIQUE",
        "CREATE CONSTRAINT sucursal_nombre IF NOT EXISTS FOR (n:Sucursal) REQUIRE n.nombre IS UNIQUE",
    ]
    for statement in statements:
        tx.run(statement)


def load_propietarios(tx, rows: list[dict[str, str]]) -> None:
    for row in rows:
        tx.run(
            """
            MERGE (p:Propietario {id_propietario: $id_propietario})
            SET p.nombre = $nombre,
                p.apellido = $apellido,
                p.dni = $dni,
                p.email = $email,
                p.telefono = $telefono,
                p.ciudad = $ciudad,
                p.provincia = $provincia,
                p.activo = true
            """,
            **row,
        )


def load_pacientes(tx, rows: list[dict[str, str]]) -> None:
    for row in rows:
        tx.run(
            """
            MATCH (o:Propietario {id_propietario: $id_propietario})
            MERGE (p:Paciente {id_paciente: $id_paciente})
            SET p.nombre = $nombre,
                p.especie = $especie,
                p.raza = $raza,
                p.fecha_nac = date($fecha_nac),
                p.activo = $activo
            MERGE (o)-[:POSEE]->(p)
            """,
            id_propietario=row["id_propietario"],
            id_paciente=row["id_paciente"],
            nombre=row["nombre"],
            especie=row["especie"],
            raza=row["raza"],
            fecha_nac=row["fecha_nac"],
            activo=parse_bool(row["activo"]),
        )


def load_veterinarios(tx, rows: list[dict[str, str]]) -> None:
    for row in rows:
        tx.run(
            """
            MERGE (v:Veterinario {id_vet: $id_vet})
            SET v.nombre = $nombre,
                v.apellido = $apellido,
                v.matricula = $matricula,
                v.especialidad = $especialidad,
                v.activo = $activo
            MERGE (s:Sucursal {nombre: $sucursal})
            MERGE (v)-[:TRABAJA_EN]->(s)
            """,
            id_vet=row["id_vet"],
            nombre=row["nombre"],
            apellido=row["apellido"],
            matricula=row["matricula"],
            especialidad=row["especialidad"],
            sucursal=row["sucursal"],
            activo=parse_bool(row["activo"]),
        )


def load_consultas(tx, rows: list[dict[str, str]]) -> None:
    for row in rows:
        tx.run(
            """
            MATCH (p:Paciente {id_paciente: $id_paciente})
            MATCH (v:Veterinario {id_vet: $id_vet})
            MERGE (c:Consulta {id_consulta: $id_consulta})
            SET c.fecha = date($fecha),
                c.motivo = $motivo,
                c.diagnostico = $diagnostico,
                c.costo = toFloat($costo),
                c.estado = $estado
            MERGE (p)-[:TUVO_CONSULTA]->(c)
            MERGE (v)-[:ATENDIO]->(c)
            """,
            **row,
        )


def load_vacunaciones(tx, rows: list[dict[str, str]]) -> None:
    for row in rows:
        tx.run(
            """
            MATCH (p:Paciente {id_paciente: $id_paciente})
            MATCH (v:Veterinario {id_vet: $id_vet})
            MERGE (vac:Vacuna {id_vacuna: $id_vacuna})
            SET vac.fecha_aplicacion = date($fecha_aplicacion),
                vac.nombre_vacuna = $nombre_vacuna,
                vac.proxima_dosis = date($proxima_dosis)
            MERGE (p)-[:RECIBIO_VACUNA]->(vac)
            MERGE (v)-[:APLICO_VACUNA]->(vac)
            """,
            **row,
        )


def main() -> None:
    load_dotenv()
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "neo4j")

    driver = GraphDatabase.driver(uri, auth=(user, password))
    propietarios = read_csv("propietarios.csv")
    pacientes = read_csv("pacientes.csv")
    veterinarios = read_csv("veterinarios.csv")
    consultas = read_csv("consultas.csv")
    vacunaciones = read_csv("vacunaciones.csv")

    with driver.session() as session:
        session.execute_write(create_constraints)
        session.execute_write(reset_graph)
        session.execute_write(load_propietarios, propietarios)
        session.execute_write(load_pacientes, pacientes)
        session.execute_write(load_veterinarios, veterinarios)
        session.execute_write(load_consultas, consultas)
        session.execute_write(load_vacunaciones, vacunaciones)

    driver.close()
    print("Carga Neo4j completa.")


if __name__ == "__main__":
    main()
