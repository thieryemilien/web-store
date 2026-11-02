# Mi Tienda — Flask monolítico (V1 sin imágenes)

Proyecto educativo para principiantes. Incluye catálogo, CRUD básico de productos (desactivación en lugar de borrado), clientes, direcciones, carrito y pedidos. **No utiliza API REST ni JavaScript propio**: Flask renderiza HTML con Jinja2.

## Requisitos
- Python con paquetes disponibles para tu versión (se recomienda Python 3.12 o 3.13 para reducir incompatibilidades)
- MySQL Server + Workbench (o SQLite para comenzar)

## Instalación en Windows (PowerShell)
```powershell
cd tienda_flask_v1
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```
Si solo tienes otra versión de Python, crea el entorno con esa versión (`python -m venv .venv`), siempre que los paquetes sean compatibles.

## MySQL Workbench
Conéctate como administrador y ejecuta:
```sql
CREATE DATABASE IF NOT EXISTS web_store CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'tienda'@'%' IDENTIFIED BY 'tienda123';
GRANT ALL PRIVILEGES ON web_store.* TO 'tienda'@'%';
```
Si el usuario ya existía con otra contraseña, ajusta su contraseña mediante `ALTER USER`. Si Workbench conecta a otro servidor MySQL distinto al de Python, las tablas no aparecerán en el servidor esperado.

Edita `.env` para que `DATABASE_URL` coincida con tu servidor. No subas `.env` a Git.

## Crear tablas y datos
```powershell
.\.venv\Scripts\python.exe -m flask --app app init-db
.\.venv\Scripts\python.exe -m flask --app app seed
.\.venv\Scripts\python.exe -m flask --app app run --debug
```
Abre http://127.0.0.1:5000

## Alternativa más fácil: SQLite
Para comenzar sin MySQL, elimina o comenta `DATABASE_URL` en `.env`. Se creará una base SQLite en la carpeta `instance` al ejecutar `init-db`. Más tarde puedes cambiar a MySQL.

## Flujo para probar
1. Abre **Administrar productos** y crea productos.
2. Abre **Clientes** y registra uno.
3. Agrega una dirección al cliente.
4. Abre **Carrito**, selecciona cliente y añade productos.
5. Confirma el pedido y revisa **Pedidos**.

## Archivos clave
- `app.py`: rutas Flask, formularios y lógica sencilla.
- `models.py`: clases/tablas SQLAlchemy.
- `database.py`: objeto de conexión SQLAlchemy.
- `templates/`: páginas HTML con Jinja2.
- `static/`: CSS.

## Notas educativas
- `db.create_all()` crea tablas nuevas, **no migra** tablas existentes. Usa una base vacía para esta V1 o aplica migraciones cuidadosamente. La estructura de esta versión no tiene por qué ser idéntica a la versión FastAPI anterior.
- El proyecto es **para aprendizaje**, no para exponer en Internet: no incluye autenticación, protección CSRF ni control de roles. No uses `--debug` en producción.
- En concurrencia real habría que reforzar la coordinación de todas las modificaciones del carrito.

## Actualización desde la versión con imágenes
Si ya tienes una tabla `producto` creada con el campo `imagen_url`, puedes dejar esa columna en MySQL; esta versión simplemente no la utiliza. Si la columna es obligatoria (NOT NULL), deberás hacerla nullable o eliminarla tras una copia de seguridad. No es necesario borrar tus datos para utilizar la nueva versión.
