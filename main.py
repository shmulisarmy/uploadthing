import os
from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Form
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

app = FastAPI()

# Allow frontend access if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Serve static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")



def file_exists(filename: str):
    return (UPLOAD_DIR / filename).exists()


def get_full_file_name(before_extension: str, extension: str, i: int):
    if i > 0:
        before_extension += f"_{i}"
    filename = f"{before_extension}.{extension}"
    return filename


@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    provided_before_extension_filename: str = Form(None)  # <---- key fix here
):
    print(f'{file = }')
    print(f'{provided_before_extension_filename = }')

    before_extension = provided_before_extension_filename or file.filename.rsplit(".", 1)[0]
    extension = file.filename.rsplit(".", 1)[-1]

    i = 0
    while file_exists(get_full_file_name(before_extension, extension, i)):
        i += 1
    filename = get_full_file_name(before_extension, extension, i)

    file_location = UPLOAD_DIR / filename

    with open(file_location, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    return {
        "filename": filename,
        "full-url": f"@{filename}",
        "url-ending": f"@{filename}"
    }


@app.get("/{filenameWithAtSign}")
async def get_file(filenameWithAtSign: str):
    if not filenameWithAtSign.startswith("@"):
        raise HTTPException(status_code=404, detail="a file name should start with @")
    filename = filenameWithAtSign.replace("@", "")
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="file not found")
    return FileResponse(file_path)



port = int(os.getenv("PORT", 8000))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
