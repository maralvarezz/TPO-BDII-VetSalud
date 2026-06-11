from __future__ import annotations

import json
from typing import Any

from pymongo import UpdateOne

from src.utils.mongo import get_mongo_database


def _parse_cantidad(value: Any) -> int:
    try:
        cantidad = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("La cantidad debe ser un numero entero.") from exc

    if cantidad <= 0:
        raise ValueError("La cantidad a decrementar debe ser mayor a 0.")

    return cantidad


def _normalizar_movimientos(movimientos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cantidades_por_producto: dict[str, int] = {}

    for movimiento in movimientos:
        if not isinstance(movimiento, dict):
            raise ValueError("Cada movimiento de stock debe ser un objeto.")

        id_producto = str(movimiento.get("id_producto", "")).strip()
        if not id_producto:
            raise ValueError("Cada movimiento debe informar id_producto.")

        cantidad = _parse_cantidad(movimiento.get("cantidad"))
        cantidades_por_producto[id_producto] = (
            cantidades_por_producto.get(id_producto, 0) + cantidad
        )

    if not cantidades_por_producto:
        raise ValueError("Debe informar al menos un movimiento de stock.")

    return [
        {"id_producto": id_producto, "cantidad": cantidad}
        for id_producto, cantidad in sorted(cantidades_por_producto.items())
    ]


def _parse_movimientos_json(payload_json: str | None) -> list[dict[str, Any]]:
    if payload_json is None:
        raise ValueError("Debe informar un payload JSON con movimientos de stock.")

    try:
        payload = json.loads(payload_json)
    except json.JSONDecodeError as exc:
        raise ValueError("El payload debe ser un JSON valido.") from exc

    if isinstance(payload, dict):
        payload = [payload]

    if not isinstance(payload, list):
        raise ValueError("El payload debe ser un objeto o una lista de objetos.")

    return _normalizar_movimientos(payload)


def actualizar_stock_productos(movimientos: list[dict[str, Any]]) -> dict[str, Any]:
    movimientos_normalizados = _normalizar_movimientos(movimientos)
    ids_producto = [movimiento["id_producto"] for movimiento in movimientos_normalizados]
    cantidad_por_producto = {
        movimiento["id_producto"]: movimiento["cantidad"]
        for movimiento in movimientos_normalizados
    }

    db = get_mongo_database()
    productos = list(
        db.stock_farmaceutico.find(
            {"id_producto": {"$in": ids_producto}, "activo": True}
        )
    )
    productos_por_id = {producto["id_producto"]: producto for producto in productos}

    ids_inexistentes = sorted(set(ids_producto) - set(productos_por_id))
    if ids_inexistentes:
        raise ValueError(
            "No existen productos activos con id: " + ", ".join(ids_inexistentes)
        )

    stock_insuficiente = []
    for id_producto, cantidad in cantidad_por_producto.items():
        unidades = int(productos_por_id[id_producto]["unidades"])
        if unidades < cantidad:
            stock_insuficiente.append(
                f"{id_producto} requiere {cantidad} y hay {unidades}"
            )

    if stock_insuficiente:
        raise ValueError("Stock insuficiente: " + "; ".join(stock_insuficiente))

    operaciones = [
        UpdateOne(
            {
                "id_producto": id_producto,
                "activo": True,
                "unidades": {"$gte": cantidad},
            },
            {"$inc": {"unidades": -cantidad}},
        )
        for id_producto, cantidad in cantidad_por_producto.items()
    ]
    resultado = db.stock_farmaceutico.bulk_write(operaciones, ordered=True)

    if resultado.modified_count != len(operaciones):
        raise ValueError("No se pudieron actualizar todos los productos solicitados.")

    productos_actualizados = []
    for id_producto in ids_producto:
        producto_anterior = productos_por_id[id_producto]
        cantidad = cantidad_por_producto[id_producto]
        updated = db.stock_farmaceutico.find_one({"id_producto": id_producto})
        if updated is None:
            raise ValueError(f"No se pudo leer el producto actualizado {id_producto}.")
        productos_actualizados.append(
            {
                "id_producto": updated["id_producto"],
                "nombre": updated["nombre"],
                "categoria": updated["categoria"],
                "proveedor": updated["proveedor"],
                "activo": updated.get("activo", True),
                "unidades_previas": int(producto_anterior["unidades"]),
                "unidades_decrementadas": cantidad,
                "unidades_actuales": int(updated["unidades"]),
            }
        )

    return {
        "operacion": "actualizacion_stock",
        "cantidad_productos_actualizados": len(productos_actualizados),
        "productos": productos_actualizados,
    }


def decrementar_stock_producto(id_producto: str, cantidad: int) -> dict[str, Any]:
    return actualizar_stock_productos(
        [{"id_producto": id_producto, "cantidad": cantidad}]
    )


# Actualizacion de stock: decrementa unidades de uno o varios productos utilizados
def actualizar_stock_productos_desde_json(
    payload_json: str | None = None,
) -> dict[str, Any]:
    return actualizar_stock_productos(_parse_movimientos_json(payload_json))


def decrementar_stock_producto_desde_args(
    id_producto: str,
    cantidad: str | int,
) -> dict[str, Any]:
    return decrementar_stock_producto(id_producto, _parse_cantidad(cantidad))
