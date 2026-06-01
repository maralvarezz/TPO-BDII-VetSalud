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
python3 scripts/run_query.py 1
```

Tambien acepta nombres como:

```bash
python3 scripts/run_query.py query_01
```

El runner queda preparado para consultas sobre:

- `MongoDB`
- `Neo4j`

Cada consulta se registra una sola vez en `scripts/run_query.py`, indicando que motor usa y que funcion ejecuta.

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
