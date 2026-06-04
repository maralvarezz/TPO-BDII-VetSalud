from __future__ import annotations

from src.utils.neo4j import get_neo4j_driver


# Propietarios sin consultas registradas en el ultimo anio
def obtener_propietarios_sin_consultas_ultimo_anio() -> list[dict]:
    query = """
    WITH date() - duration({years: 1}) AS fecha_desde
    MATCH (prop:Propietario)-[:POSEE]->(pac:Paciente)
    WITH DISTINCT prop, fecha_desde
    WHERE NOT EXISTS {
      MATCH (prop)-[:POSEE]->(:Paciente)-[:TUVO_CONSULTA]->(c:Consulta)
      WHERE c.fecha >= fecha_desde
    }
    OPTIONAL MATCH (prop)-[:POSEE]->(pac_ultima:Paciente)-[:TUVO_CONSULTA]->(ultima:Consulta)
    WITH prop, pac_ultima, ultima
    ORDER BY ultima.fecha DESC
    WITH prop, collect({paciente: pac_ultima, consulta: ultima})[0] AS ultima_atencion
    WITH
      prop,
      ultima_atencion.consulta.fecha AS ultima_consulta,
      ultima_atencion.paciente AS paciente_ultima_consulta
    RETURN
      {
        id_propietario: prop.id_propietario,
        nombre: prop.nombre,
        apellido: prop.apellido,
        dni: prop.dni,
        email: prop.email,
        telefono: prop.telefono,
        ciudad: prop.ciudad,
        provincia: prop.provincia,
        activo: prop.activo
      } AS propietario,
      CASE
        WHEN ultima_consulta IS NULL THEN NULL
        ELSE right("0" + toString(ultima_consulta.day), 2) + "/" +
          right("0" + toString(ultima_consulta.month), 2) + "/" +
          toString(ultima_consulta.year)
      END AS ultima_consulta,
      CASE
        WHEN ultima_consulta IS NULL THEN "Sin consultas registradas"
        ELSE "Sin consultas en el ultimo anio"
      END AS estado_consultas,
      CASE
        WHEN paciente_ultima_consulta IS NULL THEN NULL
        ELSE {
          id_paciente: paciente_ultima_consulta.id_paciente,
          nombre: paciente_ultima_consulta.nombre,
          especie: paciente_ultima_consulta.especie,
          raza: paciente_ultima_consulta.raza,
          activo: paciente_ultima_consulta.activo
        }
      END AS paciente_ultima_consulta
    ORDER BY propietario.id_propietario ASC
    """

    driver = get_neo4j_driver()
    try:
        with driver.session() as session:
            result = session.run(query)
            return [record.data() for record in result]
    finally:
        driver.close()
