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
