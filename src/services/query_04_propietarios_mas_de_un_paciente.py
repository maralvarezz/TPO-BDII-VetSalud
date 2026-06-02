from __future__ import annotations

from src.utils.neo4j import get_neo4j_driver

# Propietarios con más de un paciente registrado
def obtener_propietarios_con_mas_de_un_paciente() -> list[dict]:
    query = """
    MATCH (p:Propietario)-[:POSEE]->(pac:Paciente)
    WITH p, count(pac) AS cantidad_pacientes, collect(pac.nombre) AS pacientes
    WHERE cantidad_pacientes > 1
    RETURN
      p.id_propietario AS id_propietario,
      p.nombre AS nombre,
      p.apellido AS apellido,
      p.email AS email,
      p.telefono AS telefono,
      cantidad_pacientes,
      pacientes
    ORDER BY cantidad_pacientes DESC, id_propietario ASC
    """

    driver = get_neo4j_driver()
    try:
        with driver.session() as session:
            result = session.run(query)
            return [record.data() for record in result]
    finally:
        driver.close()
