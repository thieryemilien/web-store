from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from backend.controllers.tienda_controller import router


app = FastAPI(
    title="Tienda API",
    description="API REST con datos en memoria y POO",
)


@app.exception_handler(LookupError)
async def not_found_handler(request: Request, exc: LookupError):
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)}
    )


@app.exception_handler(ValueError)
async def validation_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )


@app.get("/health")
def health():
    return {"status": "UP"}


app.include_router(router)