# Python Flask 게시판

Flask와 SQLite를 사용해 만든 심플한 웹 게시판입니다.

## 주요 기능

- 게시글 목록 조회 (페이지네이션, 검색)
- 게시글 작성 / 상세보기 / 수정 / 삭제 (비밀번호 기반)
- 댓글 작성 / 삭제
- 조회수 카운트

## 프로젝트 구조

```
bulletin_board/
├── app.py              # Flask 앱 설정 및 라우팅
├── models.py           # 데이터베이스 모델 (Post, Comment)
├── requirements.txt    # 의존 패키지 목록
├── templates/
│   ├── base.html       # 공통 레이아웃 (헤더, 푸터, 플래시 메시지)
│   ├── index.html      # 게시글 목록 페이지
│   ├── post.html       # 게시글 상세 + 댓글
│   ├── create.html     # 게시글 작성 폼
│   └── edit.html       # 게시글 수정 폼
└── static/
    └── style.css       # 전체 스타일
```

## 기술 스택

| 구분 | 사용 기술 |
|------|----------|
| 언어 | Python 3 |
| 웹 프레임워크 | Flask 3.0 |
| ORM | Flask-SQLAlchemy 3.1 |
| 데이터베이스 | SQLite |
| 템플릿 엔진 | Jinja2 |

## 데이터베이스 구조

### posts (게시글)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | INTEGER | 기본키 (자동 증가) |
| title | VARCHAR(200) | 제목 |
| author | VARCHAR(50) | 작성자 |
| content | TEXT | 본문 |
| password | VARCHAR(100) | 수정·삭제용 비밀번호 |
| views | INTEGER | 조회수 |
| created_at | DATETIME | 작성 시각 |
| updated_at | DATETIME | 수정 시각 |

### comments (댓글)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | INTEGER | 기본키 (자동 증가) |
| post_id | INTEGER | 게시글 외래키 |
| author | VARCHAR(50) | 작성자 |
| content | TEXT | 내용 |
| created_at | DATETIME | 작성 시각 |

## URL 구조

| URL | 메서드 | 설명 |
|-----|--------|------|
| `/` | GET | 게시글 목록 (검색: `?search=키워드`, 페이지: `?page=2`) |
| `/post/create` | GET / POST | 게시글 작성 |
| `/post/<id>` | GET | 게시글 상세 |
| `/post/<id>/edit` | GET / POST | 게시글 수정 |
| `/post/<id>/delete` | POST | 게시글 삭제 |
| `/post/<id>/comment` | POST | 댓글 작성 |
| `/comment/<id>/delete` | POST | 댓글 삭제 |

## 설치 및 실행

**1. 의존 패키지 설치**
```bash
pip install -r requirements.txt
```

**2. 서버 실행**
```bash
python app.py
```

**3. 브라우저 접속**
```
http://127.0.0.1:5000
```

> 첫 실행 시 `bulletin.db` 파일이 자동으로 생성됩니다.

## 배포 시 주의사항

- `app.py`의 `SECRET_KEY`를 예측 불가능한 값으로 반드시 변경하세요.
- `debug=True`는 개발용 설정이므로 배포 환경에서는 제거하세요.
- 프로덕션 환경에서는 Gunicorn 등 WSGI 서버를 사용하세요.
