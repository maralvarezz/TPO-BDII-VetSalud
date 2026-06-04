from __future__ import annotations

from src.utils.neo4j import get_neo4j_driver


DEFAULT_SUCURSAL = "Palermo"


# Pacientes de una sucursal determinada a traves de sus veterinarios
def obtener_pacientes_de_sucursal(
    sucursal: str = DEFAULT_SUCURSAL,
) -> list[dict]:
    query = """
    MATCH (s:Sucursal {nombre: $sucursal})<-[:TRABAJA_EN]-(v:Veterinario)
    CALL (v) {
      MATCH (v)-[:ATENDIO]->(:Consulta)<-[:TUVO_CONSULTA]-(pac:Paciente)
      RETURN pac, "consulta" AS origen
      UNION
      MATCH (v)-[:APLICO_VACUNA]->(:Vacuna)<-[:RECIBIO_VACUNA]-(pac:Paciente)
      RETURN pac, "vacunacion" AS origen
    }
    OPTIONAL MATCH (prop:Propietario)-[:POSEE]->(pac)
    WITH s, pac, prop,
      collect(DISTINCT {
        id_vet: v.id_vet,
        nombre: v.nombre,
        apellido: v.apellido,
        especialidad: v.especialidad,
        activo: v.activo
      }) AS veterinarios,
      collect(DISTINCT origen) AS origenes
    ORDER BY pac.id_paciente ASC
    RETURN
      s.nombre AS sucursal,
      {
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
      veterinarios,
      origenes
    """

    driver = get_neo4j_driver()
    try:
        with driver.session() as session:
            result = session.run(query, sucursal=sucursal)
            return [record.data() for record in result]
    finally:
        driver.close()
