from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os

loaded = load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"))

from app.database.init import init_mongo, close_mongo
from app.utils.middleware import JWTAuthMiddleware
from app.routes import router as api_router
from app.routes.auth import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_mongo()
        app.state.ready = True
        print("✅ Mongo + Beanie initialized")
    except Exception as e:
        print(f"❌ Mongo init failed: {e}")
    yield
    await close_mongo()


app = FastAPI(title="FashionifyAI Backend", lifespan=lifespan)


# CORS middleware - allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://fashionifyai.vercel.app",
        "http://localhost:3000",
        "https://fashionifyai.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(JWTAuthMiddleware)


@app.get("/")
async def root():
    return {"message": "Welcome to the FashionifyAI Backend!"}


@app.get("/ai")
async def ai_check():
    return {"status": "todo", "message": "AI service placeholder"}


app.include_router(auth_router)
app.include_router(api_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
