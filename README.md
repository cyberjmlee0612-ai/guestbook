# 우리들의 방명록

Day 5~8의 FastAPI·Pydantic 수업 코드와 `txt.md`를 바탕으로 만든 HTML 방명록입니다. 글 작성, 목록·검색, 비밀번호로 수정·삭제를 지원합니다. 데이터는 관계 없는 SQLite 테이블 하나에 저장합니다. JavaScript나 별도 데이터베이스 서버는 사용하지 않습니다.

## 로컬 실행

Python 3.10 이상에서 `day8_aio` 폴더로 이동한 다음:

```sh
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

브라우저에서 `http://127.0.0.1:8000`을 엽니다. 처음 실행할 때 `guestbook.db`가 자동 생성됩니다.

## Render 배포

저장소 루트의 이 폴더를 Git 저장소에 올린 뒤 Render에서 **Blueprint**를 만들고 Blueprint Path를 `day8_aio/render.yaml`로 지정합니다. 직접 Web Service를 만드는 경우 Root Directory를 `day8_aio`, Build Command를 `pip install -r requirements.txt`, Start Command를 `uvicorn main:app --host 0.0.0.0 --port $PORT`로 지정합니다.

**무료 플랜 주의:** Render 무료 Web Service의 파일은 재시작·절전·재배포 때 사라집니다. 따라서 무료 플랜의 SQLite 글은 영구 보존되지 않습니다. 장기 보존이 필요하면 Render 유료 Web Service에 영구 디스크를 붙이고 환경 변수 `GUESTBOOK_DB_PATH`를 디스크 경로(예: `/var/data/guestbook.db`)로 설정해야 합니다. 영구 디스크는 무료 플랜에서 지원하지 않습니다.
