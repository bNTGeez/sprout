"""FastAPI application instance.

This file creates the `app` instance and wires up all API routers.
Add new routers here when you create new route modules.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.plaid.routes import router as plaid_router
from .api.routes import router
from .api.agents.routes import router as agents_router
from .api.transactions import router as transactions_router
from .api.categories import router as categories_router
from .api.accounts import router as accounts_router

app = FastAPI(
    title="Sprout",
    description="AI-powered budgeting and financial planning API",
    version="1.0.0",
)

# CORS middleware 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(router, prefix="/api")
app.include_router(plaid_router, prefix="/api/plaid")
app.include_router(agents_router, prefix="/api/agents")
app.include_router(transactions_router, prefix="/api")
app.include_router(categories_router, prefix="/api")
app.include_router(accounts_router, prefix="/api")

