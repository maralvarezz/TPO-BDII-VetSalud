# TPO-BDII-VetSalud

## Levantar MongoDB y Neo4j con Docker

1. Copiar el archivo de ejemplo de variables de entorno:

```bash
cp .env.example .env
```

2. Levantar los contenedores:

```bash
docker compose up -d
```

3. Instalar dependencias de Python:

```bash
python3 -m pip install -r requirements.txt
```

Si usas un entorno virtual, activalo antes de instalar las dependencias y de ejecutar el proyecto.

4. Cargar datos en MongoDB:

```bash
python3 scripts/loaders/load_mongo.py
```

5. Cargar datos en Neo4j:

```bash
python3 scripts/loaders/load_neo4j.py
```

## Ejecutar consultas

La idea es tener una funcion por consulta dentro de `src/services/` y un runner unico:

```bash
python3 scripts/run_query.py <query_num> [argumentos]
```

Ejemplo query 10, pacientes de una sucursal a traves de veterinarios:

```bash
python3 scripts/run_query.py 10 Palermo
```

Ejemplo query 11, ingresos por veterinario en un mes:

```bash
python3 scripts/run_query.py 11 05/2026
```

Ejemplo query 12, propietarios sin consultas en el ultimo anio:

```bash
python3 scripts/run_query.py 12
```

Ejemplo query 13, ABM de propietarios:

```bash
python3 scripts/run_query.py 13 alta '{"id_propietario":"C999","nombre":"Lucia","apellido":"Perez","dni":"40111222","email":"lucia@gmail.com","telefono":"1155554444","ciudad":"Buenos Aires","provincia":"Buenos Aires"}'
python3 scripts/run_query.py 13 modificacion '{"id_propietario":"C999","telefono":"1166667777","ciudad":"La Plata"}'
python3 scripts/run_query.py 13 baja '{"id_propietario":"C999"}'
```

Ejemplo query 14, registro de consulta con validacion de paciente y veterinario:

```bash
python3 scripts/run_query.py 14 '{"id_consulta":"CON999","id_paciente":"P001","id_vet":"V001","fecha":"2026-06-08","motivo":"Control","diagnostico":"Sano","costo":5000,"estado":"Cerrada"}'
```

Ejemplo query 15, decremento de stock de producto:

```bash
python3 scripts/run_query.py 15 PRD001 2
python3 scripts/run_query.py 15 '[{"id_producto":"PRD001","cantidad":2},{"id_producto":"PRD004","cantidad":1}]'
```

El runner queda preparado para consultas sobre:

- `MongoDB`
- `Neo4j`

Cada consulta se registra una sola vez en `scripts/run_query.py`, indicando que motor usa y que funcion ejecuta.

## Interfaz web

Tambien hay una interfaz web inicial sobre FastAPI:

```bash
python3 -m uvicorn app.main:app --reload
```

Si queres usar el comando `uvicorn` directo, primero tenes que tener las dependencias instaladas en el entorno activo.

Luego se puede abrir:

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/docs`

## Variables de entorno

El proyecto usa estas variables:

- `MONGO_URI`
- `MONGO_DB`
- `NEO4J_URI`
- `NEO4J_USER`
- `NEO4J_PASSWORD`

## URLs utiles

- Neo4j Browser: [http://localhost:7474](http://localhost:7474)
- MongoDB: `mongodb://localhost:27017/`
