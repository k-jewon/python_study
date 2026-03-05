# REST API 모듈
# Flask-RESTX를 사용해 /api 경로에 Swagger UI가 포함된 REST API를 제공한다.
# Swagger UI 접속: http://127.0.0.1:5000/api/docs

from flask import request
from flask_restx import Api, Namespace, Resource, fields
from models import db, Post, Comment
from datetime import datetime

# ─────────────────────────────────────────────────────────────────
# API 인스턴스 생성
# doc='/api/docs' : Swagger UI 경로
# ─────────────────────────────────────────────────────────────────
api = Api(
    title='게시판 REST API',
    version='1.0',
    description='Flask 게시판의 REST API입니다. 게시글과 댓글 CRUD를 지원합니다.',
    doc='/api/docs',          # Swagger UI URL
    prefix='/api',            # 모든 API 경로 앞에 /api 붙임
)

# ─────────────────────────────────────────────────────────────────
# Namespace (라우트 그룹)
# ─────────────────────────────────────────────────────────────────
posts_ns    = Namespace('posts',    description='게시글 관련 API')
comments_ns = Namespace('comments', description='댓글 관련 API')

api.add_namespace(posts_ns)
api.add_namespace(comments_ns)


# ─────────────────────────────────────────────────────────────────
# Swagger 모델 정의 (요청/응답 스펙 문서화 및 유효성 검사)
# ─────────────────────────────────────────────────────────────────

# 댓글 응답 모델
comment_model = api.model('Comment', {
    'id':         fields.Integer(description='댓글 ID'),
    'author':     fields.String(description='작성자'),
    'content':    fields.String(description='댓글 내용'),
    'created_at': fields.String(description='작성 시각'),
})

# 게시글 목록 아이템 모델 (상세 없이 요약 정보만)
post_summary_model = api.model('PostSummary', {
    'id':           fields.Integer(description='게시글 ID'),
    'title':        fields.String(description='제목'),
    'author':       fields.String(description='작성자'),
    'views':        fields.Integer(description='조회수'),
    'comment_count': fields.Integer(description='댓글 수'),
    'created_at':   fields.String(description='작성 시각'),
})

# 게시글 상세 모델 (댓글 목록 포함)
post_detail_model = api.model('PostDetail', {
    'id':         fields.Integer(description='게시글 ID'),
    'title':      fields.String(description='제목'),
    'author':     fields.String(description='작성자'),
    'content':    fields.String(description='본문'),
    'views':      fields.Integer(description='조회수'),
    'created_at': fields.String(description='작성 시각'),
    'updated_at': fields.String(description='수정 시각'),
    'comments':   fields.List(fields.Nested(comment_model), description='댓글 목록'),
})

# 게시글 목록 응답 모델 (페이지네이션 포함)
post_list_model = api.model('PostList', {
    'posts':       fields.List(fields.Nested(post_summary_model)),
    'total':       fields.Integer(description='전체 게시글 수'),
    'page':        fields.Integer(description='현재 페이지'),
    'pages':       fields.Integer(description='전체 페이지 수'),
    'per_page':    fields.Integer(description='페이지당 게시글 수'),
})

# 게시글 생성 요청 모델
post_create_model = api.model('PostCreate', {
    'title':    fields.String(required=True,  description='제목',      example='안녕하세요'),
    'author':   fields.String(required=True,  description='작성자',    example='홍길동'),
    'content':  fields.String(required=True,  description='본문 내용', example='게시글 내용입니다.'),
    'password': fields.String(required=True,  description='수정·삭제용 비밀번호', example='1234'),
})

# 게시글 수정 요청 모델
post_update_model = api.model('PostUpdate', {
    'title':    fields.String(required=True, description='수정할 제목',   example='수정된 제목'),
    'content':  fields.String(required=True, description='수정할 본문',   example='수정된 내용'),
    'password': fields.String(required=True, description='등록 시 설정한 비밀번호', example='1234'),
})

# 게시글 삭제 요청 모델
post_delete_model = api.model('PostDelete', {
    'password': fields.String(required=True, description='등록 시 설정한 비밀번호', example='1234'),
})

# 댓글 생성 요청 모델
comment_create_model = api.model('CommentCreate', {
    'author':  fields.String(required=True, description='작성자', example='홍길동'),
    'content': fields.String(required=True, description='댓글 내용', example='좋은 글이네요!'),
})


# ─────────────────────────────────────────────────────────────────
# 헬퍼 함수
# ─────────────────────────────────────────────────────────────────

def fmt(dt) -> str:
    """datetime 객체를 ISO 8601 문자열로 변환한다."""
    return dt.strftime('%Y-%m-%dT%H:%M:%S') if dt else None

def serialize_post_summary(post: Post) -> dict:
    return {
        'id':            post.id,
        'title':         post.title,
        'author':        post.author,
        'views':         post.views,
        'comment_count': len(post.comments),
        'created_at':    fmt(post.created_at),
    }

def serialize_post_detail(post: Post) -> dict:
    return {
        'id':         post.id,
        'title':      post.title,
        'author':     post.author,
        'content':    post.content,
        'views':      post.views,
        'created_at': fmt(post.created_at),
        'updated_at': fmt(post.updated_at),
        'comments': [
            {
                'id':         c.id,
                'author':     c.author,
                'content':    c.content,
                'created_at': fmt(c.created_at),
            }
            for c in post.comments
        ],
    }


# ─────────────────────────────────────────────────────────────────
# 게시글 API
# ─────────────────────────────────────────────────────────────────

@posts_ns.route('/')
class PostList(Resource):

    @posts_ns.doc('게시글 목록 조회')
    @posts_ns.marshal_with(post_list_model)
    @posts_ns.param('page',    '페이지 번호 (기본값: 1)',       type=int)
    @posts_ns.param('per_page','페이지당 게시글 수 (기본값: 10)', type=int)
    @posts_ns.param('search',  '검색어 (제목 또는 내용)',        type=str)
    def get(self):
        """게시글 목록을 반환합니다. 페이지네이션과 검색을 지원합니다."""
        page     = request.args.get('page',     1,  type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search   = request.args.get('search',  '')

        query = Post.query.order_by(Post.created_at.desc())
        if search:
            query = query.filter(
                Post.title.contains(search) | Post.content.contains(search)
            )

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return {
            'posts':    [serialize_post_summary(p) for p in pagination.items],
            'total':    pagination.total,
            'page':     pagination.page,
            'pages':    pagination.pages,
            'per_page': pagination.per_page,
        }

    @posts_ns.doc('게시글 생성')
    @posts_ns.expect(post_create_model, validate=True)
    @posts_ns.response(201, '생성 성공')
    @posts_ns.response(400, '유효성 오류')
    def post(self):
        """새 게시글을 생성합니다."""
        data    = api.payload
        title   = (data.get('title')   or '').strip()
        author  = (data.get('author')  or '').strip()
        content = (data.get('content') or '').strip()
        password = (data.get('password') or '').strip()

        if not all([title, author, content, password]):
            posts_ns.abort(400, '모든 항목(title, author, content, password)을 입력해주세요.')

        post = Post(title=title, author=author, content=content, password=password)
        db.session.add(post)
        db.session.commit()
        return serialize_post_detail(post), 201


@posts_ns.route('/<int:post_id>')
@posts_ns.param('post_id', '게시글 ID')
class PostItem(Resource):

    @posts_ns.doc('게시글 상세 조회')
    @posts_ns.marshal_with(post_detail_model)
    @posts_ns.response(404, '게시글 없음')
    def get(self, post_id):
        """게시글 상세 정보와 댓글 목록을 반환합니다. 조회 시 조회수가 1 증가합니다."""
        post = Post.query.get_or_404(post_id)
        post.views += 1
        db.session.commit()
        return serialize_post_detail(post)

    @posts_ns.doc('게시글 수정')
    @posts_ns.expect(post_update_model, validate=True)
    @posts_ns.response(200, '수정 성공')
    @posts_ns.response(401, '비밀번호 불일치')
    @posts_ns.response(404, '게시글 없음')
    def put(self, post_id):
        """게시글을 수정합니다. 등록 시 설정한 비밀번호가 필요합니다."""
        post = Post.query.get_or_404(post_id)
        data = api.payload

        if data.get('password') != post.password:
            posts_ns.abort(401, '비밀번호가 틀렸습니다.')

        title   = (data.get('title')   or '').strip()
        content = (data.get('content') or '').strip()
        if not title or not content:
            posts_ns.abort(400, '제목과 내용을 입력해주세요.')

        post.title      = title
        post.content    = content
        post.updated_at = datetime.utcnow()
        db.session.commit()
        return serialize_post_detail(post)

    @posts_ns.doc('게시글 삭제')
    @posts_ns.expect(post_delete_model, validate=True)
    @posts_ns.response(200, '삭제 성공')
    @posts_ns.response(401, '비밀번호 불일치')
    @posts_ns.response(404, '게시글 없음')
    def delete(self, post_id):
        """게시글을 삭제합니다. 연결된 댓글도 함께 삭제됩니다."""
        post = Post.query.get_or_404(post_id)
        data = api.payload

        if data.get('password') != post.password:
            posts_ns.abort(401, '비밀번호가 틀렸습니다.')

        db.session.delete(post)
        db.session.commit()
        return {'message': f'게시글 {post_id}번이 삭제되었습니다.'}


# ─────────────────────────────────────────────────────────────────
# 댓글 API
# ─────────────────────────────────────────────────────────────────

@posts_ns.route('/<int:post_id>/comments')
@posts_ns.param('post_id', '게시글 ID')
class CommentList(Resource):

    @posts_ns.doc('댓글 목록 조회')
    @posts_ns.marshal_list_with(comment_model)
    @posts_ns.response(404, '게시글 없음')
    def get(self, post_id):
        """특정 게시글의 댓글 목록을 반환합니다."""
        post = Post.query.get_or_404(post_id)
        return [
            {'id': c.id, 'author': c.author, 'content': c.content, 'created_at': fmt(c.created_at)}
            for c in post.comments
        ]

    @posts_ns.doc('댓글 작성')
    @posts_ns.expect(comment_create_model, validate=True)
    @posts_ns.response(201, '생성 성공')
    @posts_ns.response(404, '게시글 없음')
    def post(self, post_id):
        """특정 게시글에 댓글을 작성합니다."""
        post   = Post.query.get_or_404(post_id)
        data   = api.payload
        author  = (data.get('author')  or '').strip()
        content = (data.get('content') or '').strip()

        if not author or not content:
            posts_ns.abort(400, '작성자와 댓글 내용을 입력해주세요.')

        comment = Comment(post_id=post.id, author=author, content=content)
        db.session.add(comment)
        db.session.commit()
        return {'id': comment.id, 'author': comment.author, 'content': comment.content,
                'created_at': fmt(comment.created_at)}, 201


@comments_ns.route('/<int:comment_id>')
@comments_ns.param('comment_id', '댓글 ID')
class CommentItem(Resource):

    @comments_ns.doc('댓글 삭제')
    @comments_ns.response(200, '삭제 성공')
    @comments_ns.response(404, '댓글 없음')
    def delete(self, comment_id):
        """댓글을 삭제합니다."""
        comment = Comment.query.get_or_404(comment_id)
        db.session.delete(comment)
        db.session.commit()
        return {'message': f'댓글 {comment_id}번이 삭제되었습니다.'}
