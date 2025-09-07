from src.core.config import settings

if __name__ == "__main__":
    import uvicorn
    reload = True
    if settings.ENV == "prod":
        reload = False
    uvicorn.run(app="src.core.setup:app", host="0.0.0.0", port=settings.APP_PORT, reload=reload)
