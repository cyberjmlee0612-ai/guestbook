"""HTML 방명록: FastAPI + 파이썬 표준 라이브러리 SQLite."""

import hashlib
import hmac
import os
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from urllib.parse import parse_qs, quote

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, field_validator


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("GUESTBOOK_DB_PATH", BASE_DIR / "guestbook.db"))
app = FastAPI(title="우리들의 방명록")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


class EntryIn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=30)
    message: str = Field(min_length=1, max_length=500)
    password: str = Field(min_length=4, max_length=72)

    @field_validator("name", "message", "password")
    @classmethod
    def reject_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("공백만 입력할 수 없습니다.")
        return value


@contextmanager
def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db():
    with connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            message TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )""")


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return f"{salt.hex()}:{digest.hex()}"


def valid_password(password: str, stored: str) -> bool:
    salt, _ = stored.split(":", 1)
    return hmac.compare_digest(hash_password(password, bytes.fromhex(salt)), stored)


def page(content: str, title: str = "우리들의 방명록") -> HTMLResponse:
    html = (BASE_DIR / "templates" / "base.html").read_text(encoding="utf-8")
    return HTMLResponse(html.replace("{{ title }}", escape(title)).replace("{{ content }}", content))


def notice(message: str) -> str:
    return f'<p class="notice" role="alert">{escape(message)}</p>' if message else ""


async def fields(request: Request) -> dict[str, str]:
    if request.headers.get("content-type", "").split(";", 1)[0] != "application/x-www-form-urlencoded":
        raise HTTPException(415, "HTML 폼 형식만 지원합니다.")
    raw = await request.body()
    if len(raw) > 4096:
        raise HTTPException(413, "입력 내용이 너무 깁니다.")
    try:
        return {key: values[0] for key, values in parse_qs(raw.decode("utf-8"), keep_blank_values=True, max_num_fields=5).items()}
    except (UnicodeDecodeError, ValueError) as error:
        raise HTTPException(400, "잘못된 입력 형식입니다.") from error


def entry_form(values: dict[str, str] | None = None) -> str:
    values = values or {}
    return f'''<form method="post" action="/entries" class="write-form">
      <div class="form-row"><label>이름<input name="name" required maxlength="30" value="{escape(values.get('name', ''), quote=True)}" placeholder="이름을 적어 주세요"></label>
      <label>수정·삭제 비밀번호<input type="password" name="password" required minlength="4" maxlength="72" placeholder="4자 이상"></label></div>
      <label>남길 이야기<textarea name="message" required maxlength="500" rows="5" placeholder="오늘의 이야기를 남겨 주세요">{escape(values.get('message', ''))}</textarea></label>
      <div class="form-bottom"><small>최대 500자 · 비밀번호는 수정·삭제에 사용돼요</small><button type="submit">글 남기기 <span aria-hidden="true">↗</span></button></div>
    </form>'''


def home_view(search: str = "", message: str = "", values: dict[str, str] | None = None, status: int = 200) -> HTMLResponse:
    search = search.strip()[:100]
    with connect() as db:
        if search:
            pattern = "%" + search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
            rows = db.execute("SELECT id, name, message, created_at FROM entries WHERE name LIKE ? ESCAPE '\\' OR message LIKE ? ESCAPE '\\' ORDER BY id DESC LIMIT 100", (pattern, pattern)).fetchall()
        else:
            rows = db.execute("SELECT id, name, message, created_at FROM entries ORDER BY id DESC LIMIT 100").fetchall()
        count = db.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
    cards = "".join(f'''<article class="entry"><div class="entry-top"><span class="avatar">{escape(row['name'][0])}</span><div><strong>{escape(row['name'])}</strong><time datetime="{escape(row['created_at'])}">{escape(row['created_at'][:16].replace('T', ' '))} UTC</time></div><span class="entry-no">#{row['id']:03d}</span></div><p>{escape(row['message'])}</p><a class="edit-link" href="/entries/{row['id']}/edit">수정 / 삭제 →</a></article>''' for row in rows)
    if not cards:
        cards = '<div class="empty">아직 남겨진 이야기가 없어요.<br>첫 번째 글을 남겨 주세요.</div>' if not search else '<div class="empty">검색 결과가 없어요.</div>'
    content = f'''<div class="shell"><header class="topbar"><a class="brand" href="/">✳ &nbsp;우리들의 방명록</a><span>작은 이야기를 남기는 공간</span></header>
    <main><section class="hero"><div class="eyebrow">OUR GUESTBOOK · 2026</div><h1>잠깐 들러서,<br><em>마음을 남겨 주세요.</em></h1><p>오늘의 생각, 반가운 인사, 소소한 일상까지.<br>우리의 기록이 이곳에 차곡차곡 쌓입니다.</p><div class="hero-line"><span>✦</span><span>현재 {count}개의 이야기</span></div></section>
    <section class="panel" aria-labelledby="write-title"><div class="section-head"><div><span class="kicker">01 / WRITE</span><h2 id="write-title">방명록 작성</h2></div><span class="section-mark">✎</span></div>{notice(message)}{entry_form(values)}</section>
    <section class="entries-section" aria-labelledby="entries-title"><div class="section-head"><div><span class="kicker">02 / STORIES</span><h2 id="entries-title">남겨진 이야기 <sup>{len(rows)}</sup></h2></div></div><form method="get" action="/" class="search"><label class="sr-only" for="search">이름 또는 내용 검색</label><input id="search" name="q" value="{escape(search, quote=True)}" placeholder="이름 또는 내용 검색"><button type="submit">검색</button>{'<a href="/">전체 보기</a>' if search else ''}</form><div class="entries">{cards}</div>{'<p class="list-note">최근 100개의 글을 보여줍니다.</p>' if count > 100 and not search else ''}</section></main><footer>우리들의 방명록 <span>·</span> 작은 기록, 오래 남는 마음</footer></div>'''
    result = page(content)
    result.status_code = status
    return result


@app.get("/", response_class=HTMLResponse)
def home(q: str = "", message: str = ""):
    return home_view(q, message)


@app.post("/entries", response_class=HTMLResponse)
async def create_entry(request: Request):
    data = await fields(request)
    try:
        entry = EntryIn.model_validate(data)
    except Exception:
        return home_view(message="이름, 내용, 비밀번호를 확인해 주세요.", values=data, status=422)
    with connect() as db:
        db.execute("INSERT INTO entries (name, message, password_hash, created_at) VALUES (?, ?, ?, ?)", (entry.name, entry.message, hash_password(entry.password), datetime.now(timezone.utc).isoformat(timespec="minutes")))
    return RedirectResponse("/?message=" + quote("글을 남겼어요."), status_code=303)


def edit_view(entry_id: int, message: str = "", status: int = 200) -> HTMLResponse:
    with connect() as db:
        row = db.execute("SELECT id, name, message FROM entries WHERE id = ?", (entry_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "글을 찾을 수 없습니다.")
    content = f'''<div class="shell"><header class="topbar"><a class="brand" href="/">✳ &nbsp;우리들의 방명록</a><span>작은 이야기를 남기는 공간</span></header><main class="edit-main"><a class="back" href="/">← 방명록으로 돌아가기</a><section class="panel"><span class="kicker">EDIT / #{entry_id:03d}</span><h1 class="edit-title">이야기 다듬기</h1>{notice(message)}<form action="/entries/{entry_id}/edit" method="post" class="write-form"><label>이름<input name="name" required maxlength="30" value="{escape(row['name'], quote=True)}"></label><label>남길 이야기<textarea name="message" required maxlength="500" rows="7">{escape(row['message'])}</textarea></label><label>작성할 때 정한 비밀번호<input name="password" type="password" required minlength="4" maxlength="72"></label><button type="submit">수정 완료</button></form><form action="/entries/{entry_id}/delete" method="post" class="delete-form"><label>삭제할 때 정한 비밀번호<input name="password" type="password" required></label><button type="submit">글 삭제</button></form></section></main><footer>우리들의 방명록</footer></div>'''
    result = page(content, "글 수정 · 우리들의 방명록")
    result.status_code = status
    return result


@app.get("/entries/{entry_id}/edit", response_class=HTMLResponse)
def edit_page(entry_id: int):
    return edit_view(entry_id)


@app.post("/entries/{entry_id}/edit", response_class=HTMLResponse)
async def edit_entry(entry_id: int, request: Request):
    data = await fields(request)
    try:
        entry = EntryIn.model_validate(data)
    except Exception:
        return edit_view(entry_id, "입력 내용을 확인해 주세요.", 422)
    with connect() as db:
        row = db.execute("SELECT password_hash FROM entries WHERE id = ?", (entry_id,)).fetchone()
        if row is None:
            raise HTTPException(404, "글을 찾을 수 없습니다.")
        if not valid_password(entry.password, row["password_hash"]):
            return edit_view(entry_id, "비밀번호가 맞지 않습니다.", 403)
        db.execute("UPDATE entries SET name = ?, message = ? WHERE id = ?", (entry.name, entry.message, entry_id))
    return RedirectResponse("/?message=" + quote("글을 수정했어요."), status_code=303)


@app.post("/entries/{entry_id}/delete", response_class=HTMLResponse)
async def delete_entry(entry_id: int, request: Request):
    data = await fields(request)
    with connect() as db:
        row = db.execute("SELECT password_hash FROM entries WHERE id = ?", (entry_id,)).fetchone()
        if row is None:
            raise HTTPException(404, "글을 찾을 수 없습니다.")
        if not valid_password(data.get("password", ""), row["password_hash"]):
            return edit_view(entry_id, "비밀번호가 맞지 않습니다.", 403)
        db.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
    return RedirectResponse("/?message=" + quote("글을 삭제했어요."), status_code=303)


@app.get("/health")
def health():
    return {"status": "ok"}


init_db()
