from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router

app = FastAPI(
    title="Bug Triaging ML API",
    description="API for predicting bug assignees using ML",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from database.db_connection import init_db

init_db()

# Include routes
app.include_router(router)

@app.get("/")
async def root():
    return {"message": "Welcome to Bug Triaging ML System API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
