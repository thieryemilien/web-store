from decimal import Decimal

from backend.models.entities import (
    Cliente, Direccion, Producto,
    CarritoCompra, Pedido, DetallePedido
)
from backend.repositories.memory import (
    MemoryStore,
    ClienteRepository,
    DireccionRepository,
    ProductoRepository,
    CarritoRepository,
    PedidoRepository
)
from backend.schemas import dto as s


class TiendaService:
    def __init__(self, store: MemoryStore):
        self.store = store
        self.clientes = ClienteRepository(store)
        self.direcciones = DireccionRepository(store)
        self.productos = ProductoRepository(store)
        self.carritos = CarritoRepository(store)
        self.pedidos = PedidoRepository(store)

    # -------- CLIENTES --------

    def obtener_cliente(self, cliente_id: int) -> Cliente:
        cliente = self.clientes.find_by_id(cliente_id)

        if cliente is None:
            raise LookupError("Cliente no encontrado")

        return cliente

    def listar_clientes(self):
        return self.clientes.find_all()

    def crear_cliente(self, data: s.ClienteCreate):
        if self.clientes.find_by_email(data.email):
            raise ValueError("El email ya está registrado")

        cliente = Cliente(
            id=self.store.siguiente_id("cliente"),
            **data.model_dump()
        )
        return self.clientes.save(cliente)

    # -------- DIRECCIONES --------

    def crear_direccion(
        self, cliente_id: int, data: s.DireccionCreate
    ):
        cliente = self.obtener_cliente(cliente_id)

        direccion = Direccion(
            id=self.store.siguiente_id("direccion"),
            cliente_id=cliente_id,
            **data.model_dump()
        )

        cliente.agregar_direccion(direccion)
        return self.direcciones.save(direccion)

    def listar_direcciones(self, cliente_id: int):
        self.obtener_cliente(cliente_id)
        return self.direcciones.find_by_cliente(cliente_id)

    # -------- PRODUCTOS --------

    def listar_productos(self):
        return self.productos.find_all()

    def obtener_producto(self, producto_id: int):
        producto = self.productos.find_by_id(producto_id)

        if producto is None:
            raise LookupError("Producto no encontrado")

        return producto

    def crear_producto(self, data: s.ProductoCreate):
        producto = Producto(
            id=self.store.siguiente_id("producto"),
            **data.model_dump()
        )
        return self.productos.save(producto)

    def actualizar_producto(
        self, producto_id: int, data: s.ProductoCreate
    ):
        producto = self.obtener_producto(producto_id)

        for atributo, valor in data.model_dump().items():
            setattr(producto, atributo, valor)

        return self.productos.save(producto)

    # -------- CARRITO --------

    def obtener_carrito(self, cliente_id: int):
        self.obtener_cliente(cliente_id)

        carrito = self.carritos.find_by_cliente(cliente_id)

        if carrito is None:
            carrito = CarritoCompra(
                id=self.store.siguiente_id("carrito"),
                cliente_id=cliente_id
            )
            self.carritos.save(carrito)

        return carrito

    def agregar_al_carrito(
        self, cliente_id: int, data: s.AgregarCarritoIn
    ):
        producto = self.obtener_producto(data.producto_id)

        if not producto.activo:
            raise ValueError("El producto no está disponible")

        carrito = self.obtener_carrito(cliente_id)
        carrito.agregar_producto(
            data.producto_id, data.cantidad
        )

        return self.ver_carrito(cliente_id)

    def quitar_del_carrito(
        self, cliente_id: int, producto_id: int
    ):
        carrito = self.obtener_carrito(cliente_id)

        if not any(
            i.producto_id == producto_id for i in carrito.items
        ):
            raise LookupError("Producto no encontrado en el carrito")

        carrito.quitar_producto(producto_id)
        return self.ver_carrito(cliente_id)

    def ver_carrito(self, cliente_id: int):
        carrito = self.obtener_carrito(cliente_id)
        items = []

        for item in carrito.items:
            producto = self.obtener_producto(item.producto_id)

            items.append(
                s.DetalleCarritoOut(
                    producto_id=producto.id,
                    nombre=producto.nombre,
                    cantidad=item.cantidad,
                    precio_unitario=producto.precio,
                    subtotal=producto.precio * item.cantidad
                )
            )

        total = sum(
            (i.subtotal for i in items),
            Decimal("0.00")
        )

        return s.CarritoOut(
            id=carrito.id,
            cliente_id=cliente_id,
            items=items,
            total=total
        )

    # -------- PEDIDOS --------

    def crear_pedido(
        self, cliente_id: int, data: s.CrearPedidoIn
    ):
        cliente = self.obtener_cliente(cliente_id)

        direccion = self.direcciones.find_by_id(
            data.direccion_id
        )

        if direccion is None or direccion.cliente_id != cliente_id:
            raise ValueError("Dirección de entrega no válida")

        carrito = self.obtener_carrito(cliente_id)

        if not carrito.items:
            raise ValueError("No se puede comprar un carrito vacío")

        detalles = []

        for item in carrito.items:
            producto = self.obtener_producto(item.producto_id)

            if not producto.activo:
                raise ValueError(
                    f"Producto no disponible: {producto.nombre}"
                )

            detalles.append(
                DetallePedido(
                    producto_id=producto.id,
                    nombre_producto=producto.nombre,
                    cantidad=item.cantidad,
                    precio_unitario=producto.precio
                )
            )

        pedido = Pedido(
            id=self.store.siguiente_id("pedido"),
            cliente_id=cliente_id,
            direccion_id=direccion.id,
            detalles=detalles
        )

        self.pedidos.save(pedido)
        cliente.agregar_pedido(pedido)
        carrito.vaciar()

        return self.serializar_pedido(pedido)

    def serializar_pedido(self, pedido: Pedido):
        detalles = [
            s.DetallePedidoOut(
                producto_id=d.producto_id,
                nombre_producto=d.nombre_producto,
                cantidad=d.cantidad,
                precio_unitario=d.precio_unitario,
                subtotal=d.calcular_subtotal()
            )
            for d in pedido.detalles
        ]

        return s.PedidoOut(
            id=pedido.id,
            cliente_id=pedido.cliente_id,
            direccion_id=pedido.direccion_id,
            fecha=pedido.fecha,
            estado=pedido.estado,
            detalles=detalles,
            total=pedido.calcular_total()
        )

    def listar_pedidos(self, cliente_id: int):
        self.obtener_cliente(cliente_id)

        return [
            self.serializar_pedido(p)
            for p in self.pedidos.find_by_cliente(cliente_id)
        ]

    def obtener_pedido(self, pedido_id: int):
        pedido = self.pedidos.find_by_id(pedido_id)

        if pedido is None:
            raise LookupError("Pedido no encontrado")

        return self.serializar_pedido(pedido)