from fastapi import APIRouter, Depends

from backend.schemas import dto as s
from backend.services.tienda_service import TiendaService
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.services.tienda_service import TiendaService
from fastapi import File, UploadFile
#from backend.repositories.memory import MemoryStore


router = APIRouter(prefix="/api", tags=["Tienda"])

# Una única instancia compartida en memoria
#store = MemoryStore()
#def get_service():
#    return TiendaService(store)

def get_service(db: Session = Depends(get_db)):
    return TiendaService(db)


# CLIENTES
@router.get("/clientes", response_model=list[s.ClienteOut])
def listar_clientes(
    service: TiendaService = Depends(get_service)
):
    return service.listar_clientes()


@router.get("/clientes/{cliente_id}", response_model=s.ClienteOut)
def obtener_cliente(
    cliente_id: int,
    service: TiendaService = Depends(get_service)
):
    return service.obtener_cliente(cliente_id)


@router.post(
    "/clientes",
    response_model=s.ClienteOut,
    status_code=201
)
def crear_cliente(
    data: s.ClienteCreate,
    service: TiendaService = Depends(get_service)
):
    return service.crear_cliente(data)


# DIRECCIONES

@router.post(
    "/clientes/{cliente_id}/direcciones",
    response_model=s.DireccionOut,
    status_code=201
)
def crear_direccion(
    cliente_id: int,
    data: s.DireccionCreate,
    service: TiendaService = Depends(get_service)
):
    return service.crear_direccion(cliente_id, data)


@router.get(
    "/clientes/{cliente_id}/direcciones",
    response_model=list[s.DireccionOut]
)
def listar_direcciones(
    cliente_id: int,
    service: TiendaService = Depends(get_service)
):
    return service.listar_direcciones(cliente_id)


# PRODUCTOS

@router.get("/productos", response_model=list[s.ProductoOut])
def listar_productos(
    service: TiendaService = Depends(get_service)
):
    return service.listar_productos()


@router.get("/productos/{producto_id}", response_model=s.ProductoOut)
def obtener_producto(
    producto_id: int,
    service: TiendaService = Depends(get_service)
):
    return service.obtener_producto(producto_id)


@router.post(
    "/productos",
    response_model=s.ProductoOut,
    status_code=201
)
def crear_producto(
    data: s.ProductoCreate,
    service: TiendaService = Depends(get_service)
):
    return service.crear_producto(data)


@router.put(
    "/productos/{producto_id}",
    response_model=s.ProductoOut
)
def actualizar_producto(
    producto_id: int,
    data: s.ProductoCreate,
    service: TiendaService = Depends(get_service)
):
    return service.actualizar_producto(producto_id, data)


# CARRITO

@router.get(
    "/clientes/{cliente_id}/carrito",
    response_model=s.CarritoOut
)
def ver_carrito(
    cliente_id: int,
    service: TiendaService = Depends(get_service)
):
    return service.ver_carrito(cliente_id)


@router.post(
    "/clientes/{cliente_id}/carrito/items",
    response_model=s.CarritoOut
)
def agregar_producto_carrito(
    cliente_id: int,
    data: s.AgregarCarritoIn,
    service: TiendaService = Depends(get_service)
):
    return service.agregar_al_carrito(cliente_id, data)


@router.delete(
    "/clientes/{cliente_id}/carrito/items/{producto_id}",
    response_model=s.CarritoOut
)
def quitar_producto_carrito(
    cliente_id: int,
    producto_id: int,
    service: TiendaService = Depends(get_service)
):
    return service.quitar_del_carrito(cliente_id, producto_id)


# PEDIDOS

@router.post(
    "/clientes/{cliente_id}/pedidos",
    response_model=s.PedidoOut,
    status_code=201
)
def crear_pedido(
    cliente_id: int,
    data: s.CrearPedidoIn,
    service: TiendaService = Depends(get_service)
):
    return service.crear_pedido(cliente_id, data)


@router.get(
    "/clientes/{cliente_id}/pedidos",
    response_model=list[s.PedidoOut]
)
def listar_pedidos(
    cliente_id: int,
    service: TiendaService = Depends(get_service)
):
    return service.listar_pedidos(cliente_id)


@router.get("/pedidos/{pedido_id}", response_model=s.PedidoOut)
def obtener_pedido(
    pedido_id: int,
    service: TiendaService = Depends(get_service)
):
    return service.obtener_pedido(pedido_id)

@router.post(
    "/productos/{producto_id}/imagen",
    response_model=s.ProductoOut
)
async def subir_imagen_producto(
    producto_id: int,
    archivo: UploadFile = File(...),
    service: TiendaService = Depends(get_service)
):
    return await service.subir_imagen_producto(
        producto_id,
        archivo
    )