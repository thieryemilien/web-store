from decimal import Decimal
from sqlalchemy import select

from backend.database.connection import SessionLocal
from backend.models.entities import Cliente, Direccion, Producto


def seed():
    with SessionLocal() as db:
        cliente = db.scalar(
            select(Cliente).where(
                Cliente.email == "ana@example.com"
            )
        )

        if cliente is None:
            cliente = Cliente(
                nombre="Ana García",
                email="ana@example.com",
                telefono="600123456",
                password="123456"
            )
            db.add(cliente)
            db.flush()

            db.add(
                Direccion(
                    cliente_id=cliente.id,
                    calle="Calle Mayor 10",
                    ciudad="Barcelona",
                    provincia="Barcelona",
                    codigo_postal="08001",
                    pais="España"
                )
            )

        productos = [
            ("Teclado mecánico", "Teclado RGB", "79.90"),
            ("Ratón inalámbrico", "Ratón ergonómico", "29.50"),
            ("Monitor 27 pulgadas", "Full HD", "199.99")
        ]

        for nombre, descripcion, precio in productos:
            existente = db.scalar(
                select(Producto).where(
                    Producto.nombre == nombre
                )
            )

            if existente is None:
                db.add(
                    Producto(
                        nombre=nombre,
                        descripcion=descripcion,
                        precio=Decimal(precio),
                        activo=True
                    )
                )

        db.commit()
        print("Datos iniciales cargados correctamente")


if __name__ == "__main__":
    seed()