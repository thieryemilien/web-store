from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

# @dataclass es un decorador de Python que genera automáticamente métodos como __init__() y __repr__()
@dataclass
class Direccion:
    id: int
    cliente_id: int
    calle: str
    ciudad: str
    provincia: str
    codigo_postal: str
    pais: str

@dataclass
class Producto:
    id: int
    nombre: int
    descripcion: int
    precio: Decimal
    activo: bool = True

#Clase que contiene cada producto agregado al carrito
@dataclass
class DetalleCarrito:
    producto_id: int
    cantidad: int

    def aumentar_cantidad(self, unidad: int):
        if unidad <= 0:
            raise ValueError("La cantidad debe ser mayor a cero") 

        self.cantidad += unidad;

@dataclass
class CarritoCompra:
    id: int
    cliente_id: int
    #se crea un  campo para listar el detalle del carrito
    items: list[DetalleCarrito] = field(default_factory=list) 

    def agregar_producto(self, producto_id: int, cantidad: int):
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser positiva")

        for item in self.items:
            if item.producto_id == producto_id:
                item.aumentar_cantidad(cantidad)
                return

        self.items.append(
            DetalleCarrito(
                producto_id=producto_id,
                cantidad=cantidad
            )
        )

    def quitar_producto(self, producto_id: int):
        self.items = [
            item for item in self.items
            if item.producto_id != producto_id
        ]

    def vaciar(self):
        self.items.clear()


@dataclass 
class DetallePedido:
    id: int
    producto_id: int
    cantidad: int 
    precio_unidad: Decimal

    def calcular_subtotal(self) -> Decimal:
        return self.precio_unidad * self.cantidad        


@dataclass
class Pedido:
   id: int
   cliente_id: int
   direccion_id: int
   detalles: list[DetallePedido]
   fecha: datetime = field(
       default_factory = lambda: datetime.now(timezone.utc)
   )
   estado: str = "CREADO"

   def calcular_total(self) -> Decimal:
       return sum(
           (detalle.calcular_subtotal() for detalle in self.detalles), Decimal("0.00")
       )

@dataclass
class Cliente:
   id: int
   nombre: str
   email: str
   telefono: str
   password: str
   direcciones: list[Direccion] = field(default_factory=list)
   pedidos: list[Pedido] = field(default_factory=list) 


   def agregar_direccion(self, direccion: Direccion):
       if direccion.cliente_id != self.id:
           raise ValueError("la direccion pertenece a otro cliente")
       
       self.direcciones.append(direccion)

   def agregar_pedido(self, pedido: Pedido):
       if pedido.cliente_id != self.id: 
           raise ValueError("El pedido pertenece a otro cliente")

       self.pedidos.append(pedido)
