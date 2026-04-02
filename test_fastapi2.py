from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import traceback

from src.api.main import app

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print('GLOBAL EXCEPTION:', str(exc))
    print(traceback.format_exc())
    return JSONResponse(status_code=500, content={'message': str(exc), 'traceback': traceback.format_exc()})
