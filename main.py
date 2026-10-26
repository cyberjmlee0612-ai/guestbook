from pathlib import Path
import os
import sqlite3

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field


APP_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("GUESTBOOK_DB", APP_DIR / "guestbook.db"))
STATIC_DIR = APP_DIR / "static"

app = FastAPI(title="간단한 방명록", version="1.0.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class EntryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=40)
    message: str = Field(min_length=1, max_length=500)


class EntryOut(EntryCreate):
    id: int
    created_at: str


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            )
            """
        )


@app.on_event("startup")
def startup() -> None:
    initialize_database()


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/entries", response_model=list[EntryOut])
def list_entries() -> list[EntryOut]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT id, name, message, created_at FROM entries ORDER BY id DESC"
        ).fetchall()
    return [EntryOut(**dict(row)) for row in rows]


@app.post("/api/entries", response_model=EntryOut, status_code=status.HTTP_201_CREATED)
def create_entry(payload: EntryCreate) -> EntryOut:
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO entries (name, message) VALUES (?, ?)",
            (payload.name, payload.message),
        )
        row = connection.execute(
            "SELECT id, name, message, created_at FROM entries WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
    return EntryOut(**dict(row))


@app.delete("/api/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(entry_id: int) -> None:
    with get_connection() as connection:
        cursor = connection.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="방명록을 찾을 수 없습니다.")
