from __future__ import annotations

from src.utils.neo4j import get_neo4j_driver


DEFAULT_ID_PACIENTE = "P001"


# Historial completo de un paciente: consultas y vacunaciones ordenadas por fecha
def obtener_historial_completo_paciente(
    id_paciente: str = DEFAULT_ID_PACIENTE,
) -> list[dict]:
    query = """
    MATCH (pac:Paciente {id_paciente: $id_paciente})
    OPTIONAL MATCH (prop:Propietario)-[:POSEE]->(pac)

    OPTIONAL MATCH (pac)-[:TUVO_CONSULTA]->(c:Consulta)
    OPTIONAL MATCH (v_consulta:Veterinario)-[:ATENDIO]->(c)
    WITH pac, prop,
      collect(
        CASE
          WHEN c IS NULL THEN NULL
          ELSE {
            fecha: c.fecha,
            tipo: "consulta",
            orden: c.id_consulta,
            detalle: {
              id_consulta: c.id_consulta,
              motivo: c.motivo,
              diagnostico: c.diagnostico,
              costo: c.costo,
              estado: c.estado,
              veterinario: {
                id_vet: v_consulta.id_vet,
                nombre: v_consulta.nombre,
                apellido: v_consulta.apellido,
                especialidad: v_consulta.especialidad
              }
            }
          }
        END
      ) AS consultas

    OPTIONAL MATCH (pac)-[:RECIBIO_VACUNA]->(vac:Vacuna)
    OPTIONAL MATCH (v_vacuna:Veterinario)-[:APLICO_VACUNA]->(vac)
    WITH pac, prop, consultas,
      collect(
        CASE
          WHEN vac IS NULL THEN NULL
          ELSE {
            fecha: vac.fecha_aplicacion,
            tipo: "vacunacion",
            orden: vac.id_vacuna,
            detalle: {
              id_vacuna: vac.id_vacuna,
              nombre_vacuna: vac.nombre_vacuna,
              proxima_dosis: toString(vac.proxima_dosis),
              veterinario: {
                id_vet: v_vacuna.id_vet,
                nombre: v_vacuna.nombre,
                apellido: v_vacuna.apellido,
                especialidad: v_vacuna.especialidad
              }
            }
          }
        END
      ) AS vacunaciones

    WITH pac, prop, consultas + vacunaciones AS historial
    WITH pac, prop, [evento IN historial WHERE evento IS NOT NULL] AS historial
    UNWIND CASE WHEN size(historial) = 0 THEN [NULL] ELSE historial END AS evento
    WITH pac, prop, evento
    ORDER BY evento.fecha ASC, evento.tipo ASC, evento.orden ASC
    WITH pac, prop, collect(evento) AS historial_ordenado

    RETURN {
      id_paciente: pac.id_paciente,
      nombre: pac.nombre,
      especie: pac.especie,
      raza: pac.raza,
      fecha_nac: toString(pac.fecha_nac),
      activo: pac.activo
    } AS paciente,
    {
      id_propietario: prop.id_propietario,
      nombre: prop.nombre,
      apellido: prop.apellido,
      email: prop.email,
      telefono: prop.telefono
    } AS propietario,
    [
      evento IN historial_ordenado
      WHERE evento IS NOT NULL
      | {
        fecha: toString(evento.fecha),
        tipo: evento.tipo,
        detalle: evento.detalle
      }
    ] AS historial
    """

    driver = get_neo4j_driver()
    try:
        with driver.session() as session:
            result = session.run(query, id_paciente=id_paciente)
            return [record.data() for record in result]
    finally:
        driver.close()
