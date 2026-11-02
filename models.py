from datetime import datetime, timezone
from decimal import Decimal
from database import db


class Cliente(db.Model):
    __tablename__ = "clientes"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    telefono = db.Column(db.String(30), nullable=False, default="")
    direcciones = db.relationship("Direccion", backref="cliente", lazy=True)
    pedidos = db.relationship("Pedido", backref="cliente", lazy=True)


class Direccion(db.Model):
    __tablename__ = "direcciones"
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=False)
    calle = db.Column(db.String(200), nullable=False)
    ciudad = db.Column(db.String(100), nullable=False)
    provincia = db.Column(db.String(100), nullable=False)
    codigo_postal = db.Column(db.String(20), nullable=False)
    pais = db.Column(db.String(100), nullable=False)


class Producto(db.Model):
    __tablename__ = "productos"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.String(1000), nullable=False, default="")
    precio = db.Column(db.Numeric(12, 2), nullable=False)
    activo = db.Column(db.Boolean, nullable=False, default=True)


class CarritoCompra(db.Model):
    __tablename__ = "carritos"
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), unique=True, nullable=False)
    detalles = db.relationship("DetalleCarrito", backref="carrito", cascade="all, delete-orphan", lazy=True)


class DetalleCarrito(db.Model):
    __tablename__ = "detalles_carrito"
    id = db.Column(db.Integer, primary_key=True)
    carrito_id = db.Column(db.Integer, db.ForeignKey("carritos.id"), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id"), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    producto = db.relationship("Producto")
    __table_args__ = (db.UniqueConstraint("carrito_id", "producto_id", name="uq_carrito_producto"),)


class Pedido(db.Model):
    __tablename__ = "pedidos"
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=False)
    direccion_id = db.Column(db.Integer, db.ForeignKey("direcciones.id"), nullable=False)
    fecha = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    estado = db.Column(db.String(30), nullable=False, default="CREADO")
    direccion = db.relationship("Direccion")
    detalles = db.relationship("DetallePedido", backref="pedido", cascade="all, delete-orphan", lazy=True)

    @property
    def total(self):
        return sum((d.precio_unitario * d.cantidad for d in self.detalles), Decimal("0.00"))


class DetallePedido(db.Model):
    __tablename__ = "detalles_pedido"
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey("pedidos.id"), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id"), nullable=False)
    nombre_producto = db.Column(db.String(150), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric(12, 2), nullable=False)
