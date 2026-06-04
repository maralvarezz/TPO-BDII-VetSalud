from __future__ import annotations

from src.utils.mongo import get_mongo_database


# Stock de productos activos con menos de 50 unidades y su proveedor
def obtener_stock_productos_menos_de_50_unidades() -> list[dict]:
    db = get_mongo_database()

    projection = {
        "_id": 0,
        "id_producto": 1,
        "nombre": 1,
        "categoria": 1,
        "unidades": 1,
        "precio_unit": 1,
        "vencimiento": 1,
        "proveedor": 1,
        "activo": 1,
    }

    cursor = db.stock_farmaceutico.find(
        {"activo": True, "unidades": {"$lt": 50}},
        projection,
    ).sort([("unidades", 1), ("id_producto", 1)])

    return list(cursor)
