from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

# Serve the index.html at the root
@app.get("/")
async def read_root():
    return FileResponse("index.html")

# Mount static files for all other resources
app.mount("/", StaticFiles(directory="."), name="dbt_docs")