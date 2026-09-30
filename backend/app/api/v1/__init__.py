from fastapi import APIRouter
from app.api.v1 import auth, scenarios, materials, reports, dashboard, solver, cost

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(scenarios.router)
api_router.include_router(materials.router)
api_router.include_router(reports.router)
api_router.include_router(dashboard.router)
api_router.include_router(solver.router)
api_router.include_router(cost.router)


