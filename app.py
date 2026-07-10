import datetime
import os
import traceback
import asyncio
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from tools.tool import extract_project_data
from tools.rag_engine import evaluate

app = FastAPI(title="Project Health Agent")
executor = ThreadPoolExecutor(max_workers=2)


@app.get("/favicon.ico")
async def favicon():
    from fastapi.responses import Response
    return Response(status_code=204)


static_dir = Path(__file__).parent / "static"
uploads_dir = Path("/tmp") / "project-health-uploads"
uploads_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def root():
    index = static_dir / "index.html"
    if not index.exists():
        return HTMLResponse("<h1>Project Health Agent</h1><p>UI not found.</p>")
    return HTMLResponse(index.read_text())


@app.post("/assess")
async def assess(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(400, "Only .xlsx or .xls files are supported.")

    content = await file.read()
    if not content:
        raise HTTPException(400, "Empty file uploaded.")

    fsize = len(content)
    magic = content[:4].hex()
    print(f"Upload: {file.filename} ({fsize} bytes, magic: {magic})")

    is_zip = content[:2] == b"PK"
    is_ole = content[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"

    if not is_zip and not is_ole:
        raise HTTPException(400, (
            f"Unknown file format ({fsize} bytes, header: {magic[:8]}). "
            "Upload a .xlsx file saved from Excel."
        ))

    tmp_path = uploads_dir / f"upload_{os.urandom(4).hex()}.xlsx"
    if is_zip:
        tmp_path.write_bytes(content)
    else:
        import xlrd
        import xlsxwriter
        xls_book = xlrd.open_workbook(file_contents=content)
        xlsx_book = xlsxwriter.Workbook(str(tmp_path))
        for sheet_name in xls_book.sheet_names():
            xls_sheet = xls_book.sheet_by_name(sheet_name)
            xlsx_sheet = xlsx_book.add_worksheet(sheet_name)
            for row in range(xls_sheet.nrows):
                for col in range(xls_sheet.ncols):
                    cell = xls_sheet.cell(row, col)
                    xlsx_sheet.write(row, col, cell.value)
        xlsx_book.close()
        print(f"Converted .xls ({xls_book.nsheets} sheets) to .xlsx")

    try:
        as_of = datetime.datetime.now()
        data = extract_project_data.invoke({"filepath": str(tmp_path), "as_of_date": as_of})
        rag = evaluate.invoke({"data": data})
        return {"extracted": data, "rag": rag, "filepath": str(tmp_path)}
    except HTTPException:
        raise
    except Exception as e:
        tb = traceback.format_exc()
        print(f"Error processing {file.filename}:\n{tb}")
        raise HTTPException(500, f"Failed to read the Excel file: {e}")


@app.post("/chat")
async def chat(message: str = Form(...), filepath: str = Form(...)):
    if not Path(filepath).exists():
        raise HTTPException(400, "Project file expired. Please re-upload the file.")

    from agent import create_project_agent
    agent, err = create_project_agent()
    if err:
        raise HTTPException(503, f"Agent unavailable: {err}. Set GROQ_API_KEY in your Vercel environment variables.")

    prompt = f"I have a project file at {filepath}. {message}"

    loop = asyncio.get_event_loop()
    try:
        result = await asyncio.wait_for(
            loop.run_in_executor(executor, lambda: agent.invoke(
                {"messages": [{"role": "user", "content": prompt}]},
                config={"configurable": {"thread_id": "web-user"}},
            )),
            timeout=25,
        )
        return {"response": result["messages"][-1].content}
    except asyncio.TimeoutError:
        raise HTTPException(504, "Agent took too long to respond. Try a simpler question.")
    except Exception as e:
        print(f"Agent error: {e}")
        raise HTTPException(500, f"Agent error: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8005, reload=True)
