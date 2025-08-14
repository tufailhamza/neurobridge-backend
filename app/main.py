from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from src.routes.auth import router as auth_router
from src.routes.posts import router as posts_router
from src.routes.clinicians import router as clinicians_router
from src.routes.stripe import router as stripe_router
from src.routes.collections import router as collections_router

app = FastAPI(
    title="NeuroBridge API",
    description="Backend API for NeuroBridge application",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(posts_router)
app.include_router(clinicians_router)
app.include_router(stripe_router)
app.include_router(collections_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)