"""Fábrica de aplicaciones FastAPI con el mínimo común de los servicios."""

from fastapi import FastAPI


def create_app(service: str, version: str = "0.1.0",
               lifespan=None) -> FastAPI:
    """Crea la aplicación con el endpoint de salud que todo servicio
    expone (WP2.4: los diez servicios responden /health). `lifespan`
    permite arrancar el consumidor del bus al iniciar el servicio."""
    app = FastAPI(title=service, version=version, lifespan=lifespan)

    @app.get("/health", tags=["health"])
    def health():
        return {"service": service, "status": "ok", "version": version}

    return app
