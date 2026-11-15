from app.api.quarantine_routes import router as quarantine_router
from app.api.pipeline_routes import router as pipeline_router
from app.api.dataset_routes import router as dataset_router
from app.services.run_history import initialize_history_table
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.services.quarantine import initialize_quarantine_table

app = FastAPI(
    title="YottaFlex Data Engineering Platform",
    description="Reusable data ingestion, validation and processing framework",
    version="1.0.0"
)
initialize_history_table()


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://localhost:5176"
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "YottaFlex Data Platform API is running",
        "status": "healthy"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "backend",
        "version": "1.0.0"
    }


# Register pipeline API routes
app.include_router(pipeline_router)
app.include_router(dataset_router)
initialize_quarantine_table()
app.include_router(quarantine_router)