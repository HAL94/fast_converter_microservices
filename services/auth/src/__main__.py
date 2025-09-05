from .config.settings import settings

if __name__ == "__main__":
    import uvicorn
    reload = False
    if settings.ENV == "dev":
        reload = True
    uvicorn.run(app="src.server:app", host="0.0.0.0", port=settings.APP_PORT, reload=reload)
