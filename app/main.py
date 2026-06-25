from fastapi import FastAPI
from app.config import settings

app = FastAPI(
    title="DarkAtlas Asset Management API",
    description="Asset Management module for the DarkAtlas ASM platform",
    version="1.0.0",
    debug=settings.debug
)

# Define a root endpoint to check if the API is running
@app.get("/")
def root():
    return {"message": "DarkAtlas Asset API is running"}

# Define a health check endpoint to verify the server is running
@app.get("/health")
def health():
    return {"status": "ok"}