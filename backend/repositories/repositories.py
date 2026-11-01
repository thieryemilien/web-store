from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.entities import (
    Cliente, Direccion, Producto, CarritoCompra, Pedido
)


class ClienteRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_all(self):
        return self.db.scalars(select(Cliente)).all()

    def find_by_id(self, cliente_id):
        return self.db.get(Cliente, cliente_id)

    def find_by_email(self, email):
        return self.db.scalar(
            select(Cliente).where(Cliente.email == email)
        )

    def save(self, cliente):
        self.db.add(cliente)
        self.db.flush()
        return cliente


class DireccionRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_by_id(self, direccion_id):
        return self.db.get(Direccion, direccion_id)

    def find_by_cliente(self, cliente_id):
        return self.db.scalars(
            select(Direccion).where(
                Direccion.cliente_id == cliente_id
            )
        ).all()

    def save(self, direccion):
        self.db.add(direccion)
        self.db.flush()
        return direccion


class ProductoRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_all(self):
        return self.db.scalars(select(Producto)).all()

    def find_by_id(self, producto_id):
        return self.db.get(Producto, producto_id)

    def save(self, producto):
        self.db.add(producto)
        self.db.flush()
        return producto


class CarritoRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_by_cliente(self, cliente_id):
        return self.db.scalar(
            select(CarritoCompra).where(
                CarritoCompra.cliente_id == cliente_id
            )
        )

    def save(self, carrito):
        self.db.add(carrito)
        self.db.flush()
        return carrito


class PedidoRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_by_id(self, pedido_id):
        return self.db.get(Pedido, pedido_id)

    def find_by_cliente(self, cliente_id):
        return self.db.scalars(
            select(Pedido).where(
                Pedido.cliente_id == cliente_id
            )
        ).all()

    def save(self, pedido):
        self.db.add(pedido)
        
        #flush() para enviar las operaciones pendientes a MySQL y obtener los IDs generados, pero sin confirmar todavía la transacción.
        #La confirmación definitiva se realizará desde el servicio mediante commit().

        self.db.flush()
        return pedido