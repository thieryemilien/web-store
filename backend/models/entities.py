from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    String, ForeignKey, Numeric, DateTime, Boolean
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.connection import Base


class Cliente(Base):

    
   
    #ForeignKey() representa una relación entre tablas.
    #relationship() permite navegar entre objetos relacionados.
    #Numeric(12, 2) almacena importes monetarios sin los errores de precisión habituales de float.
    #cascade="all, delete-orphan" permite gestionar los detalles como parte de su entidad principal.

    #__tablename__ indica la tabla MySQL.
    __tablename__ = "clientes"

     #mapped_column() define una columna o campo.
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150))
    email: Mapped[str] = mapped_column(
        String(200), unique=True, index=True
    )
    password: Mapped[str] = mapped_column(String(150))
    telefono: Mapped[str] = mapped_column(String(30))

    direcciones: Mapped[list["Direccion"]] = relationship(
        back_populates="cliente"
    )
    pedidos: Mapped[list["Pedido"]] = relationship(
        back_populates="cliente"
    )


class Direccion(Base):
    __tablename__ = "direcciones"

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(
        ForeignKey("clientes.id")
    )
    calle: Mapped[str] = mapped_column(String(200))
    ciudad: Mapped[str] = mapped_column(String(100))
    provincia: Mapped[str] = mapped_column(String(100))
    codigo_postal: Mapped[str] = mapped_column(String(20))
    pais: Mapped[str] = mapped_column(String(100))

    cliente: Mapped["Cliente"] = relationship(
        back_populates="direcciones"
    )


class Producto(Base):
    __tablename__ = "productos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150))
    descripcion: Mapped[str] = mapped_column(String(1000))
    precio: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    activo: Mapped[bool] = mapped_column(
        Boolean, default=True
    )
    
    # campo para guardar imagen
    imagen_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )


class CarritoCompra(Base):
    __tablename__ = "carritos"

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(
        ForeignKey("clientes.id"), unique=True
    )

    items: Mapped[list["DetalleCarrito"]] = relationship(
        back_populates="carrito",
        cascade="all, delete-orphan"
    )


class DetalleCarrito(Base):
    __tablename__ = "detalles_carrito"

    id: Mapped[int] = mapped_column(primary_key=True)
    carrito_id: Mapped[int] = mapped_column(
        ForeignKey("carritos.id")
    )
    producto_id: Mapped[int] = mapped_column(
        ForeignKey("productos.id")
    )
    cantidad: Mapped[int]

    carrito: Mapped["CarritoCompra"] = relationship(
        back_populates="items"
    )
    producto: Mapped["Producto"] = relationship()


class Pedido(Base):
    __tablename__ = "pedidos"

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(
        ForeignKey("clientes.id")
    )
    direccion_id: Mapped[int] = mapped_column(
        ForeignKey("direcciones.id")
    )
    fecha: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc).replace(
            tzinfo=None
        )
    )
    estado: Mapped[str] = mapped_column(
        String(30), default="CREADO"
    )

    cliente: Mapped["Cliente"] = relationship(
        back_populates="pedidos"
    )
    detalles: Mapped[list["DetallePedido"]] = relationship(
        back_populates="pedido",
        cascade="all, delete-orphan"
    )

    def calcular_total(self):
        return sum(
            (d.precio_unitario * d.cantidad for d in self.detalles),
            Decimal("0.00")
        )


class DetallePedido(Base):
    __tablename__ = "detalles_pedido"

    id: Mapped[int] = mapped_column(primary_key=True)
    pedido_id: Mapped[int] = mapped_column(
        ForeignKey("pedidos.id")
    )
    producto_id: Mapped[int] = mapped_column(
        ForeignKey("productos.id")
    )
    nombre_producto: Mapped[str] = mapped_column(String(150))
    cantidad: Mapped[int]
    precio_unitario: Mapped[Decimal] = mapped_column(
        Numeric(12, 2)
    )

    pedido: Mapped["Pedido"] = relationship(
        back_populates="detalles"
    )
    producto: Mapped["Producto"] = relationship()