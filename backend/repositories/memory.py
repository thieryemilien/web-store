from decimal import Decimal
from backend.models.entities import (
    Cliente, Direccion, Producto,
    CarritoCompra, Pedido
)


class MemoryStore:
    def __init__(self, seed: bool = True):
        self.clientes: dict[int, Cliente] = {}
        self.direcciones: dict[int, Direccion] = {}
        self.productos: dict[int, Producto] = {}
        self.carritos: dict[int, CarritoCompra] = {}
        self.pedidos: dict[int, Pedido] = {}

        self.secuencias = {
            "cliente": 0,
            "direccion": 0,
            "producto": 0,
            "carrito": 0,
            "pedido": 0
        }

        if seed:
            self.cargar_datos_iniciales()

    def siguiente_id(self, entidad: str) -> int:
        self.secuencias[entidad] += 1
        return self.secuencias[entidad]

    def cargar_datos_iniciales(self):
        cliente = Cliente(
            id=self.siguiente_id("cliente"),
            nombre="Ana García",
            email="ana@example.com",
            telefono="600123456",
            password="123456"

        )
        self.clientes[cliente.id] = cliente

        direccion = Direccion(
            id=self.siguiente_id("direccion"),
            cliente_id=cliente.id,
            calle="Calle Mayor 10",
            ciudad="Barcelona",
            provincia="Barcelona",
            codigo_postal="08001",
            pais="España"
        )
        self.direcciones[direccion.id] = direccion
        cliente.agregar_direccion(direccion)

        productos = [
            Producto(
                id=self.siguiente_id("producto"),
                nombre="Teclado mecánico",
                descripcion="Teclado RGB",
                precio=Decimal("79.90")
            ),
            Producto(
                id=self.siguiente_id("producto"),
                nombre="Ratón inalámbrico",
                descripcion="Ratón ergonómico",
                precio=Decimal("29.50")
            ),
            Producto(
                id=self.siguiente_id("producto"),
                nombre="Monitor 27 pulgadas",
                descripcion="Monitor Full HD",
                precio=Decimal("199.99")
            )
        ]

        for producto in productos:
            self.productos[producto.id] = producto


class ClienteRepository:
    def __init__(self, store: MemoryStore):
        self.store = store

    def find_all(self):
        return list(self.store.clientes.values())

    def find_by_id(self, cliente_id: int):
        return self.store.clientes.get(cliente_id)

    def find_by_email(self, email: str):
        return next(
            (
                c for c in self.store.clientes.values()
                if c.email.lower() == email.lower()
            ),
            None
        )

    def save(self, cliente: Cliente):
        self.store.clientes[cliente.id] = cliente
        return cliente


class DireccionRepository:
    def __init__(self, store: MemoryStore):
        self.store = store

    def find_by_id(self, direccion_id: int):
        return self.store.direcciones.get(direccion_id)

    def find_by_cliente(self, cliente_id: int):
        return [
            d for d in self.store.direcciones.values()
            if d.cliente_id == cliente_id
        ]

    def save(self, direccion: Direccion):
        self.store.direcciones[direccion.id] = direccion
        return direccion


class ProductoRepository:
    def __init__(self, store: MemoryStore):
        self.store = store

    def find_all(self):
        return list(self.store.productos.values())

    def find_by_id(self, producto_id: int):
        return self.store.productos.get(producto_id)

    def save(self, producto: Producto):
        self.store.productos[producto.id] = producto
        return producto


class CarritoRepository:
    def __init__(self, store: MemoryStore):
        self.store = store

    def find_by_cliente(self, cliente_id: int):
        return self.store.carritos.get(cliente_id)

    def save(self, carrito: CarritoCompra):
        self.store.carritos[carrito.cliente_id] = carrito
        return carrito


class PedidoRepository:
    def __init__(self, store: MemoryStore):
        self.store = store

    def find_by_id(self, pedido_id: int):
        return self.store.pedidos.get(pedido_id)

    def find_by_cliente(self, cliente_id: int):
        return [
            p for p in self.store.pedidos.values()
            if p.cliente_id == cliente_id
        ]

    def save(self, pedido: Pedido):
        self.store.pedidos[pedido.id] = pedido
        return pedido