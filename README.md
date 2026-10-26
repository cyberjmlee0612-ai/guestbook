# 간단한 방명록 앱

day1~day8에서 사용한 Python 기초, FastAPI, Pydantic, HTML/CSS/JavaScript 흐름을 연결한 작은 예제입니다. 별도 프런트엔드 빌드 도구나 외부 API 없이 동작하며, Python 표준 라이브러리 `sqlite3`로 한 개의 테이블에 방명록을 저장합니다.

## 실행

프로젝트 루트(`C:\ai4_이정민`)에서 이미 만든 가상환경을 사용합니다.

```powershell
cd "C:\ai4_이정민\guestbook_app"
& "C:\ai4_이정민\.venv\Scripts\python.exe" -m pip install -r requirements.txt
& "C:\ai4_이정민\.venv\Scripts\python.exe" -m uvicorn main:app --reload
```

브라우저에서 `http://127.0.0.1:8000`을 엽니다. API 문서는 `http://127.0.0.1:8000/docs`입니다.

서버를 중지하려면 서버가 실행 중인 터미널에서 `Ctrl+C`를 누릅니다. `--reload`를 사용했으므로 개발 중 파일을 바꾸면 서버가 다시 시작됩니다.

## 구조

- `main.py`: FastAPI 경로, Pydantic 입력 검증, SQLite 저장
- `static/index.html`: 화면 구조
- `static/styles.css`: 최소 화면 스타일
- `static/app.js`: 목록 조회, 등록, 삭제
- `guestbook.db`: 첫 실행 시 자동 생성되는 SQLite 데이터베이스

테이블은 `entries` 하나만 사용합니다. `id`, `name`, `message`, `created_at` 네 컬럼이며 다른 테이블과 관계를 만들지 않습니다. SQL에는 매개변수 바인딩을 사용하고, 화면 출력은 `textContent`로 처리합니다.

## 무료 배포 시 주의

호스팅 서비스의 무료 플랜에서 아래 시작 명령을 사용합니다.

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

무료 플랜은 서비스가 잠들거나 재시작될 수 있고, 일부 서비스는 로컬 파일을 영구 보관하지 않습니다. 따라서 이 학습용 SQLite 데이터는 재배포·재시작 뒤 사라질 수 있습니다. 영구 데이터가 필요해지는 시점에는 무료 범위와 제공 데이터베이스 정책을 먼저 확인한 뒤 저장소를 바꿔야 합니다.

## Render 무료 Web Service 배포

이 앱은 FastAPI 서버가 HTML과 API를 함께 제공하므로 Render의 **Web Service**로 배포합니다. Static Site를 선택하면 Python API가 실행되지 않습니다.

Render는 GitHub 저장소를 연결해 배포합니다. 아직 저장소가 없다면 이 프로젝트를 GitHub에 올린 뒤 진행합니다. Render Dashboard에서 `New` → `Web Service`를 선택하고 저장소를 연결합니다.

저장소의 루트에 다른 day 폴더도 함께 있는 현재 구조라면 다음 값을 입력합니다.

| Render 항목 | 입력값 |
| --- | --- |
| Name | 원하는 서비스 이름, 예: `my-guestbook` |
| Branch | 배포할 Git 브랜치, 보통 `main` |
| Root Directory | `guestbook_app` |
| Language | `Python 3` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| Instance Type | `Free` |

Root Directory를 `guestbook_app`으로 지정하면 Render가 그 폴더 안에서 `requirements.txt`를 읽고 `main.py`를 실행합니다. Root Directory를 비워 두면 저장소 전체가 실행 기준이 되어 `requirements.txt`와 `main.py`를 찾지 못할 수 있습니다.

`Create Web Service`를 누르면 빌드와 배포가 시작됩니다. Deploy Logs에서 다음 흐름을 확인합니다.

1. `pip install -r requirements.txt`가 성공합니다.
2. `uvicorn`이 `0.0.0.0`과 Render가 제공한 `$PORT`로 시작합니다.
3. 배포가 성공하면 `https://서비스이름.onrender.com` 주소가 표시됩니다.
4. 해당 주소를 브라우저에서 열고 방명록 등록·조회·삭제를 확인합니다.

Render 무료 Web Service의 제약을 확인해야 합니다.

- 15분 동안 요청이 없으면 서비스가 자동으로 절전 상태가 되며, 다음 접속 때 다시 시작하는 데 시간이 걸릴 수 있습니다.
- 무료 서비스의 파일 시스템은 임시 저장소입니다. 재배포·재시작·절전 후 `guestbook.db`가 사라질 수 있습니다.
- 따라서 이 앱의 SQLite 데이터는 학습·시연용입니다. 사용자 방명록을 영구 보관해야 한다면 저장소를 Render Postgres 같은 별도 데이터베이스로 바꿔야 합니다.
- 이 앱은 사용자가 입력한 내용을 저장하므로 공개 URL에 올릴 때는 테스트용 이름과 메시지만 사용하세요.

Render 설정을 바꾼 뒤에는 `Manual Deploy` → `Deploy latest commit`으로 다시 배포합니다. 배포 실패 시 `Logs`에서 `ModuleNotFoundError`, 잘못된 Root Directory, Start Command 오류를 먼저 확인합니다.

공식 문서:

- [Render 첫 배포](https://render.com/docs/your-first-deploy)
- [Render 무료 서비스 제한](https://render.com/docs/free)
- [Render Python 배포 문제 해결](https://render.com/docs/troubleshooting-python-deploys)
