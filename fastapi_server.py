import asyncio
import os

import aiofiles
from fastapi import FastAPI, File, UploadFile, status, Header
from fastapi.exceptions import HTTPException

app = FastAPI()

CHUNK_SIZE = 1024 * 1024  # adjust the chunk size as desired


# ALLOWS TO CONTINUE UPLOADING A FILE EVEN WHEN THERE WAS AN ERROR BEFORE (NOT RE-UPLOADING THE FULL FILE)
@app.post("/upload_files_by_chunks")
async def upload(identifier: str = Header(...), file: UploadFile = File(...)):
    directory = os.path.join(os.path.abspath("media"), identifier)
    await asyncio.get_event_loop().run_in_executor(None, os.makedirs, directory, 0o777, True)
    filepath = os.path.join(directory, file.filename)
    try:
        async with aiofiles.open(filepath, "ab") as f:
            async for chunk in read_in_chunks_generator(file, filepath):
                await f.write(chunk)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"There was an error uploading the file: {e}"
        )
    return {"message": f"Successfuly uploaded {file.filename}"}


async def read_in_chunks_generator(file: UploadFile, full_file_path: str):
    try:
        already_written_size = await asyncio.get_event_loop().run_in_executor(None, os.path.getsize, full_file_path)
    except FileNotFoundError:
        already_written_size = 0
    await file.seek(already_written_size)
    while chunk := await file.read(CHUNK_SIZE):
        yield chunk
