from decimal import Decimal

from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select

from backend.models.entities import (
    Cliente, Direccion, Producto, CarritoCompra,
    DetalleCarrito, Pedido, DetallePedido
)
from backend.repositories.repositories import (
    ClienteRepository, DireccionRepository,
    ProductoRepository, CarritoRepository,
    PedidoRepository
)
from backend.schemas import dto as s

from fastapi import UploadFile
from backend.services.image_service import ImageService


class TiendaService:
    def __init__(self, db: Session):
        self.db = db
        self.clientes = ClienteRepository(db)
        self.direcciones = DireccionRepository(db)
        self.productos = ProductoRepository(db)
        self.carritos = CarritoRepository(db)
        self.pedidos = PedidoRepository(db)

    #¿Qué cambia en las transacciones?
    #Cuando el usuario confirma una compra, se ejecutan dos operaciones sobre MySQL:
    #1. Insertar el pedido y sus detalles.
    #2. Eliminar los artículos del carrito.
    #Ambas se confirman con un único commit().
    #Si el commit() falla, hacemos rollback() y MySQL revierte las operaciones pendientes de esa transacción.
    #El bloqueo with_for_update() ayuda a coordinar compras concurrentes sobre el mismo carrito, aunque para producción también tendríamos 
    #que revisar todas las operaciones de modificación del carrito y aplicar una estrategia coherente de concurrencia.
    def confirmar(self):
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    # CLIENTES

    def obtener_cliente(self, cliente_id):
        cliente = self.clientes.find_by_id(cliente_id)
        if cliente is None:
            raise LookupError("Cliente no encontrado")
        return cliente

    def listar_clientes(self):
        return self.clientes.find_all()

    def crear_cliente(self, data: s.ClienteCreate):
        if self.clientes.find_by_email(data.email):
            raise ValueError("El email ya está registrado")

        cliente = Cliente(**data.model_dump())
        self.clientes.save(cliente)
        self.confirmar()
        return cliente

    # DIRECCIONES

    def crear_direccion(self, cliente_id, data):
        self.obtener_cliente(cliente_id)

        direccion = Direccion(
            cliente_id=cliente_id,
            **data.model_dump()
        )
        self.direcciones.save(direccion)
        self.confirmar()
        return direccion

    def listar_direcciones(self, cliente_id):
        self.obtener_cliente(cliente_id)
        return self.direcciones.find_by_cliente(cliente_id)

    # PRODUCTOS

    def listar_productos(self):
        return self.productos.find_all()

    def obtener_producto(self, producto_id):
        producto = self.productos.find_by_id(producto_id)
        if producto is None:
            raise LookupError("Producto no encontrado")
        return producto

    def crear_producto(self, data):
        producto = Producto(**data.model_dump())
        self.productos.save(producto)
        self.confirmar()
        return producto

    def actualizar_producto(self, producto_id, data):
        producto = self.obtener_producto(producto_id)

        for campo, valor in data.model_dump().items():
            setattr(producto, campo, valor)

        self.confirmar()
        return producto

    # CARRITO

    def obtener_carrito(self, cliente_id):
        self.obtener_cliente(cliente_id)
        carrito = self.carritos.find_by_cliente(cliente_id)

        if carrito is None:
            carrito = CarritoCompra(cliente_id=cliente_id)
            self.carritos.save(carrito)
            self.confirmar()

        return carrito

    def agregar_al_carrito(self, cliente_id, data):
        producto = self.obtener_producto(data.producto_id)

        if not producto.activo:
            raise ValueError("Producto no disponible")

        carrito = self.obtener_carrito(cliente_id)

        detalle = next(
            (
                item for item in carrito.items
                if item.producto_id == data.producto_id
            ),
            None
        )

        if detalle:
            detalle.cantidad += data.cantidad
        else:
            carrito.items.append(
                DetalleCarrito(
                    producto_id=data.producto_id,
                    cantidad=data.cantidad
                )
            )

        self.confirmar()
        return self.ver_carrito(cliente_id)

    def quitar_del_carrito(self, cliente_id, producto_id):
        carrito = self.obtener_carrito(cliente_id)

        detalle = next(
            (
                item for item in carrito.items
                if item.producto_id == producto_id
            ),
            None
        )

        if detalle is None:
            raise LookupError("Producto no encontrado en carrito")

        carrito.items.remove(detalle)
        self.confirmar()
        return self.ver_carrito(cliente_id)

    def ver_carrito(self, cliente_id):
        carrito = self.obtener_carrito(cliente_id)
        items = []

        for detalle in carrito.items:
            producto = detalle.producto

            items.append(
                s.DetalleCarritoOut(
                    producto_id=producto.id,
                    nombre=producto.nombre,
                    cantidad=detalle.cantidad,
                    precio_unitario=producto.precio,
                    subtotal=producto.precio * detalle.cantidad
                )
            )

        return s.CarritoOut(
            id=carrito.id,
            cliente_id=cliente_id,
            items=items,
            total=sum(
                (item.subtotal for item in items),
                Decimal("0.00")
            )
        )

    # PEDIDOS

    def crear_pedido(self, cliente_id, data):
        cliente = self.obtener_cliente(cliente_id)

        direccion = self.direcciones.find_by_id(
            data.direccion_id
        )

        if direccion is None or direccion.cliente_id != cliente_id:
            raise ValueError("Dirección de entrega no válida")

        # Bloqueamos el carrito durante la compra
        carrito = self.db.scalar(
            select(CarritoCompra)
            .where(CarritoCompra.cliente_id == cliente_id)
            .with_for_update()
        )

        if carrito is None or not carrito.items:
            raise ValueError("El carrito está vacío")

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
            cliente_id=cliente.id,
            direccion_id=direccion.id,
            detalles=detalles
        )

        self.pedidos.save(pedido)
        carrito.items.clear()

        # Pedido y vaciado del carrito en una transacción
        self.confirmar()

        return self.serializar_pedido(pedido)

    def serializar_pedido(self, pedido):
        detalles = [
            s.DetallePedidoOut(
                producto_id=d.producto_id,
                nombre_producto=d.nombre_producto,
                cantidad=d.cantidad,
                precio_unitario=d.precio_unitario,
                subtotal=d.precio_unitario * d.cantidad
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

    def listar_pedidos(self, cliente_id):
        self.obtener_cliente(cliente_id)
        pedidos = self.db.scalars(
            select(Pedido)
            .options(selectinload(Pedido.detalles))
            .where(Pedido.cliente_id == cliente_id)
        ).all()
        return [self.serializar_pedido(p) for p in pedidos]

    def obtener_pedido(self, pedido_id):
        pedido = self.db.scalar(
            select(Pedido)
            .options(selectinload(Pedido.detalles))
            .where(Pedido.id == pedido_id)
        )

        if pedido is None:
            raise LookupError("Pedido no encontrado")

        return self.serializar_pedido(pedido)

    async def subir_imagen_producto(self,producto_id: int,archivo: UploadFile):
        producto = self.obtener_producto(producto_id)

        imagen_anterior = producto.imagen_url

        # Guardar primero el archivo nuevo
        nueva_url = await ImageService.guardar_imagen(archivo)

        try:
            producto.imagen_url = nueva_url
            self.confirmar()

        except Exception:
            self.db.rollback()

            # Si MySQL falla, eliminamos el archivo nuevo
            ImageService.eliminar_imagen(nueva_url)
            raise

        # Solo eliminamos la imagen anterior después del commit
        # No debe fallar la petición si falla esta limpieza
        try:
            ImageService.eliminar_imagen(imagen_anterior)
        except OSError:
            pass

        return producto