from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ClienteCreate(BaseModel):
    nombre: str = Field(min_length=1)
    email: str = Field(min_length=3)
    telefono: str


class ClienteOut(ClienteCreate):
    id: int


class DireccionCreate(BaseModel):
    calle: str
    ciudad: str
    provincia: str
    codigo_postal: str
    pais: str


class DireccionOut(DireccionCreate):
    id: int
    cliente_id: int


class ProductoCreate(BaseModel):
    nombre: str = Field(min_length=1)
    descripcion: str = ""
    precio: Decimal = Field(gt=0)
    activo: bool = True


class ProductoOut(ProductoCreate):
    id: int


class AgregarCarritoIn(BaseModel):
    producto_id: int
    cantidad: int = Field(gt=0)


class DetalleCarritoOut(BaseModel):
    producto_id: int
    nombre: str
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal


class CarritoOut(BaseModel):
    id: int
    cliente_id: int
    items: list[DetalleCarritoOut]
    total: Decimal


class CrearPedidoIn(BaseModel):
    direccion_id: int


class DetallePedidoOut(BaseModel):
    producto_id: int
    nombre_producto: str
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal


class PedidoOut(BaseModel):
    id: int
    cliente_id: int
    direccion_id: int
    fecha: datetime
    estado: str
    detalles: list[DetallePedidoOut]
    total: Decimal