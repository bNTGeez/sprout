"""FastAPI application instance.

This file creates the `app` instance and wires up all API routers.
Add new routers here when you create new route modules.
"""

from fastapi import FastAPI

from .api.routes import router

app = FastAPI()
app.include_router(router)

