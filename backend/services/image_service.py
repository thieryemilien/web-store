from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile


BASE_DIR = Path(__file__).resolve().parents[1]
UPLOAD_DIR = BASE_DIR / "uploads" / "productos"

MAX_SIZE = 5 * 1024 * 1024  # 5 MB

ALLOWED_TYPES = {
    "image/jpeg": (".jpg", b"\xff\xd8\xff"),
    "image/png": (".png", b"\x89PNG\r\n\x1a\n"),
    "image/webp": (".webp", b"RIFF"),
}


class ImageService:

    @staticmethod
    async def guardar_imagen(file: UploadFile) -> str:
        if file.content_type not in ALLOWED_TYPES:
            raise ValueError(
                "Formato no permitido. Utiliza JPG, PNG o WebP"
            )

        extension, signature = ALLOWED_TYPES[file.content_type]

        # Lectura limitada para evitar archivos demasiado grandes
        contenido = await file.read(MAX_SIZE + 1)

        if len(contenido) > MAX_SIZE:
            raise ValueError(
                "La imagen no puede superar los 5 MB"
            )

        if not contenido.startswith(signature):
            raise ValueError("El contenido no corresponde al formato")

        # Validación adicional para WebP
        if extension == ".webp" and contenido[8:12] != b"WEBP":
            raise ValueError("Archivo WebP no válido")

        if not contenido:
            raise ValueError("El archivo está vacío")

        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        nombre = f"{uuid4().hex}{extension}"
        ruta = UPLOAD_DIR / nombre

        try:
            ruta.write_bytes(contenido)
        finally:
            await file.close()

        return f"/uploads/productos/{nombre}"

    @staticmethod
    def eliminar_imagen(imagen_url: str | None):
        if not imagen_url:
            return

        prefijo = "/uploads/productos/"

        if not imagen_url.startswith(prefijo):
            return

        nombre = imagen_url.removeprefix(prefijo)

        # No aceptar rutas arbitrarias
        if Path(nombre).name != nombre:
            return

        ruta = UPLOAD_DIR / nombre
        ruta.unlink(missing_ok=True)