import os
from decimal import Decimal, InvalidOperation
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, abort, flash, redirect, render_template, request, url_for
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from database import db
from models import Cliente, Direccion, Producto, CarritoCompra, DetalleCarrito, Pedido, DetallePedido

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "solo-desarrollo-cambiar")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///tienda.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)


@app.template_filter("euros")
def euros(valor):
    return f"{valor:.2f} €"


def entero_positivo(valor):
    try:
        numero = int(valor)
        return numero if numero > 0 else None
    except (TypeError, ValueError):
        return None



@app.route("/")
def inicio():
    productos = db.session.scalars(select(Producto).where(Producto.activo.is_(True)).order_by(Producto.id.desc())).all()
    return render_template("index.html", productos=productos)


@app.route("/productos")
def productos():
    todos = db.session.scalars(select(Producto).order_by(Producto.id.desc())).all()
    return render_template("productos.html", productos=todos)


@app.route("/productos/nuevo", methods=["GET", "POST"])
def producto_nuevo():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        try:
            precio = Decimal(request.form.get("precio", ""))
            if not precio.is_finite() or precio <= 0 or precio.as_tuple().exponent < -2:
                raise ValueError()
        except (InvalidOperation, ValueError):
            flash("El precio debe ser positivo y tener como máximo dos decimales.", "danger")
            return render_template("producto_form.html", producto=None), 400
        if not nombre:
            flash("El nombre es obligatorio.", "danger")
            return render_template("producto_form.html", producto=None), 400
        producto = Producto(nombre=nombre, descripcion=request.form.get("descripcion", "").strip(), precio=precio,
                            activo="activo" in request.form)
        db.session.add(producto)
        db.session.commit()
        flash("Producto creado.", "success")
        return redirect(url_for("productos"))
    return render_template("producto_form.html", producto=None)


@app.route("/productos/<int:producto_id>/editar", methods=["GET", "POST"])
def producto_editar(producto_id):
    producto = db.get_or_404(Producto, producto_id)
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        try:
            precio = Decimal(request.form.get("precio", ""))
            if not precio.is_finite() or precio <= 0 or precio.as_tuple().exponent < -2:
                raise ValueError()
        except (InvalidOperation, ValueError):
            flash("Precio inválido.", "danger")
            return render_template("producto_form.html", producto=producto), 400
        if not nombre:
            flash("El nombre es obligatorio.", "danger")
            return render_template("producto_form.html", producto=producto), 400
        producto.nombre = nombre
        producto.descripcion = request.form.get("descripcion", "").strip()
        producto.precio = precio
        producto.activo = "activo" in request.form
        db.session.commit()
        flash("Producto actualizado.", "success")
        return redirect(url_for("productos"))
    return render_template("producto_form.html", producto=producto)


@app.post("/productos/<int:producto_id>/eliminar")
def producto_eliminar(producto_id):
    producto = db.get_or_404(Producto, producto_id)
    # Desactivar en lugar de borrar para conservar el historial.
    producto.activo = False
    db.session.commit()
    flash("Producto desactivado (se conserva en los pedidos).", "success")
    return redirect(url_for("productos"))


@app.route("/clientes", methods=["GET", "POST"])
def clientes():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        email = request.form.get("email", "").strip().lower()
        if not nombre or "@" not in email:
            flash("Indica nombre y correo válido.", "danger")
        else:
            db.session.add(Cliente(nombre=nombre, email=email, telefono=request.form.get("telefono", "").strip()))
            try:
                db.session.commit()
                flash("Cliente registrado.", "success")
            except IntegrityError:
                db.session.rollback()
                flash("Ese correo ya está registrado.", "danger")
        return redirect(url_for("clientes"))
    todos = db.session.scalars(select(Cliente).order_by(Cliente.id.desc())).all()
    return render_template("clientes.html", clientes=todos)


@app.route("/clientes/<int:cliente_id>/direcciones", methods=["GET", "POST"])
def direcciones(cliente_id):
    cliente = db.get_or_404(Cliente, cliente_id)
    if request.method == "POST":
        campos = ["calle", "ciudad", "provincia", "codigo_postal", "pais"]
        datos = {campo: request.form.get(campo, "").strip() for campo in campos}
        if not all(datos.values()):
            flash("Completa todos los campos de la dirección.", "danger")
        else:
            db.session.add(Direccion(cliente_id=cliente.id, **datos))
            db.session.commit()
            flash("Dirección guardada.", "success")
        return redirect(url_for("direcciones", cliente_id=cliente.id))
    return render_template("direcciones.html", cliente=cliente)


@app.route("/carrito", methods=["GET"])
def carrito():
    clientes = db.session.scalars(select(Cliente).order_by(Cliente.nombre)).all()
    cliente_id = entero_positivo(request.args.get("cliente_id"))
    cliente = db.session.get(Cliente, cliente_id) if cliente_id else None
    carrito_actual = db.session.scalar(select(CarritoCompra).where(CarritoCompra.cliente_id == cliente_id)) if cliente else None
    total = sum((item.producto.precio * item.cantidad for item in carrito_actual.detalles), Decimal("0.00")) if carrito_actual else Decimal("0.00")
    direcciones_cliente = db.session.scalars(select(Direccion).where(Direccion.cliente_id == cliente_id)).all() if cliente else []
    productos_disponibles = db.session.scalars(select(Producto).where(Producto.activo.is_(True)).order_by(Producto.nombre)).all()
    return render_template("carrito.html", clientes=clientes, cliente=cliente, carrito=carrito_actual,
                           total=total, direcciones=direcciones_cliente, productos=productos_disponibles)


@app.post("/carrito/agregar")
def carrito_agregar():
    cliente_id = entero_positivo(request.form.get("cliente_id"))
    producto_id = entero_positivo(request.form.get("producto_id"))
    cantidad = entero_positivo(request.form.get("cantidad"))
    cliente = db.session.get(Cliente, cliente_id) if cliente_id else None
    producto = db.session.get(Producto, producto_id) if producto_id else None
    if not cliente or not producto or not producto.activo or not cantidad or cantidad > 1000:
        flash("Selecciona cliente, producto activo y cantidad válida (1-1000).", "danger")
        return redirect(url_for("carrito", cliente_id=cliente_id or ""))
    carro = db.session.scalar(select(CarritoCompra).where(CarritoCompra.cliente_id == cliente.id))
    if not carro:
        carro = CarritoCompra(cliente_id=cliente.id)
        db.session.add(carro)
        db.session.flush()
    detalle = db.session.scalar(select(DetalleCarrito).where(DetalleCarrito.carrito_id == carro.id, DetalleCarrito.producto_id == producto.id))
    if detalle:
        detalle.cantidad += cantidad
    else:
        db.session.add(DetalleCarrito(carrito_id=carro.id, producto_id=producto.id, cantidad=cantidad))
    db.session.commit()
    flash("Producto añadido al carrito.", "success")
    return redirect(url_for("carrito", cliente_id=cliente.id))


@app.post("/carrito/<int:detalle_id>/quitar")
def carrito_quitar(detalle_id):
    detalle = db.get_or_404(DetalleCarrito, detalle_id)
    cliente_id = detalle.carrito.cliente_id
    db.session.delete(detalle)
    db.session.commit()
    flash("Producto retirado.", "success")
    return redirect(url_for("carrito", cliente_id=cliente_id))


@app.post("/pedidos/crear")
def pedido_crear():
    cliente_id = entero_positivo(request.form.get("cliente_id"))
    direccion_id = entero_positivo(request.form.get("direccion_id"))
    if not cliente_id or not direccion_id:
        abort(400)
    # Bloqueo de carrito durante checkout (MySQL/InnoDB).
    carro = db.session.scalar(select(CarritoCompra).where(CarritoCompra.cliente_id == cliente_id).with_for_update())
    direccion = db.session.get(Direccion, direccion_id)
    if not carro or not carro.detalles or not direccion or direccion.cliente_id != cliente_id:
        db.session.rollback()
        flash("Carrito vacío o dirección no válida.", "danger")
        return redirect(url_for("carrito", cliente_id=cliente_id))
    if any(not item.producto.activo for item in carro.detalles):
        db.session.rollback()
        flash("Hay productos desactivados en el carrito.", "danger")
        return redirect(url_for("carrito", cliente_id=cliente_id))
    pedido = Pedido(cliente_id=cliente_id, direccion_id=direccion_id)
    for item in carro.detalles:
        pedido.detalles.append(DetallePedido(producto_id=item.producto_id,
                                              nombre_producto=item.producto.nombre,
                                              cantidad=item.cantidad, precio_unitario=item.producto.precio))
    db.session.add(pedido)
    carro.detalles.clear()
    db.session.commit()
    flash(f"Pedido #{pedido.id} creado correctamente.", "success")
    return redirect(url_for("pedidos"))


@app.get("/pedidos")
def pedidos():
    todos = db.session.scalars(select(Pedido).order_by(Pedido.id.desc())).all()
    return render_template("pedidos.html", pedidos=todos)


@app.cli.command("init-db")
def init_db():
    """Crear las tablas de la base de datos configurada."""
    db.create_all()
    print("Tablas creadas correctamente")


@app.cli.command("seed")
def seed():
    """Añadir algunos productos de ejemplo."""
    ejemplos = [("Teclado mecánico", "Teclado RGB", "79.90"),
                ("Ratón inalámbrico", "Ratón ergonómico", "29.50"),
                ("Monitor 27 pulgadas", "Pantalla Full HD", "199.99")]
    for nombre, descripcion, precio in ejemplos:
        if not db.session.scalar(select(Producto).where(Producto.nombre == nombre)):
            db.session.add(Producto(nombre=nombre, descripcion=descripcion, precio=Decimal(precio)))
    db.session.commit()
    print("Productos de ejemplo cargados")


if __name__ == "__main__":
    app.run(debug=True)
