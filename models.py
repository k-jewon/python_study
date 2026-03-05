# 데이터베이스 모델 정의 파일
# SQLAlchemy ORM을 사용해 Python 클래스로 테이블 구조를 표현한다.

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# app.py에서 db.init_app(app)으로 Flask 앱과 연결할 SQLAlchemy 인스턴스
db = SQLAlchemy()


class Post(db.Model):
    # 실제 DB에서 사용할 테이블 이름
    __tablename__ = 'posts'

    id         = db.Column(db.Integer, primary_key=True)          # 게시글 고유 번호 (자동 증가)
    title      = db.Column(db.String(200), nullable=False)         # 제목 (최대 200자)
    author     = db.Column(db.String(50), nullable=False)          # 작성자명 (최대 50자)
    content    = db.Column(db.Text, nullable=False)                # 본문 내용 (길이 제한 없음)
    password   = db.Column(db.String(100), nullable=False, default='1234')  # 수정·삭제용 비밀번호
    views      = db.Column(db.Integer, default=0)                  # 조회수
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # 최초 작성 시각
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)  # 마지막 수정 시각

    # 게시글과 댓글의 1:N 관계 설정
    # cascade='all, delete-orphan': 게시글 삭제 시 연결된 댓글도 자동 삭제
    # backref='post': Comment 모델에서 comment.post 로 부모 게시글에 접근 가능
    comments = db.relationship('Comment', backref='post', cascade='all, delete-orphan', lazy=True)

    def __repr__(self):
        return f'<Post {self.id}: {self.title}>'


class Comment(db.Model):
    __tablename__ = 'comments'

    id         = db.Column(db.Integer, primary_key=True)                          # 댓글 고유 번호
    post_id    = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False) # 부모 게시글 ID (외래키)
    author     = db.Column(db.String(50), nullable=False)                          # 댓글 작성자명
    content    = db.Column(db.Text, nullable=False)                                # 댓글 내용
    created_at = db.Column(db.DateTime, default=datetime.utcnow)                  # 작성 시각

    def __repr__(self):
        return f'<Comment {self.id} on Post {self.post_id}>'
