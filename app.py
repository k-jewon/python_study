# Flask 게시판 애플리케이션 메인 파일
# 라우팅(URL 처리)과 앱 설정을 담당한다.
# REST API + Swagger UI: http://127.0.0.1:5000/api/docs

from flask import Flask, render_template, request, redirect, url_for, flash
from markupsafe import Markup, escape
from models import db, Post, Comment
from datetime import datetime

app = Flask(__name__)

# --- 앱 설정 ---
# SQLite 데이터베이스 파일 경로 (instance/ 폴더 또는 현재 디렉토리에 생성됨)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bulletin.db'
# 모델 변경 감지 기능 비활성화 (불필요한 메모리 사용 방지)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# 세션·플래시 메시지 암호화에 사용하는 비밀 키 (배포 시 반드시 변경)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
# flask-restx가 Flask 에러 핸들러를 덮어쓰지 않도록 설정
app.config['ERROR_404_HELP'] = False

# SQLAlchemy를 현재 Flask 앱과 연결
db.init_app(app)

# REST API (flask-restx) 등록 - Swagger UI: /api/docs
from api import api as rest_api
rest_api.init_app(app)

# 앱 컨텍스트 안에서 테이블이 없으면 자동으로 생성
with app.app_context():
    db.create_all()


# --- Jinja2 커스텀 필터 ---
@app.template_filter('nl2br')
def nl2br_filter(value):
    # 텍스트의 줄바꿈(\n)을 HTML <br> 태그로 변환
    # escape()로 XSS 공격을 방지한 뒤 변환한다.
    return Markup(escape(value).replace('\n', '<br>\n'))


# --- 라우트 ---

@app.route('/')
def index():
    # 쿼리 파라미터에서 현재 페이지 번호와 검색어를 가져온다.
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')

    # 최신 게시글이 위에 오도록 내림차순 정렬
    query = Post.query.order_by(Post.created_at.desc())

    # 검색어가 있으면 제목 또는 내용에서 검색 (대소문자 무관)
    if search:
        query = query.filter(Post.title.contains(search) | Post.content.contains(search))

    # 한 페이지에 10개씩 페이지네이션 적용
    posts = query.paginate(page=page, per_page=10, error_out=False)
    return render_template('index.html', posts=posts, search=search)


@app.route('/post/<int:post_id>')
def post_detail(post_id):
    # 존재하지 않는 ID면 자동으로 404 반환
    post = Post.query.get_or_404(post_id)
    # 상세 페이지를 열 때마다 조회수 1 증가
    post.views += 1
    db.session.commit()
    return render_template('post.html', post=post)


@app.route('/post/create', methods=['GET', 'POST'])
def post_create():
    if request.method == 'POST':
        # 폼 데이터를 가져오고 앞뒤 공백 제거
        title = request.form.get('title', '').strip()
        author = request.form.get('author', '').strip()
        content = request.form.get('content', '').strip()

        # 필수 항목 유효성 검사
        if not title or not author or not content:
            flash('모든 항목을 입력해주세요.', 'error')
            # 입력했던 값을 유지한 채 폼을 다시 보여준다.
            return render_template('create.html', title=title, author=author, content=content)

        post = Post(title=title, author=author, content=content)
        db.session.add(post)
        db.session.commit()
        flash('게시글이 등록되었습니다.', 'success')
        # 등록 후 작성된 게시글 상세 페이지로 이동
        return redirect(url_for('post_detail', post_id=post.id))

    # GET 요청이면 빈 폼을 보여준다.
    return render_template('create.html', title='', author='', content='')


@app.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
def post_edit(post_id):
    post = Post.query.get_or_404(post_id)

    if request.method == 'POST':
        # 비밀번호 검증: 등록 시 설정한 비밀번호와 일치해야 수정 가능
        password = request.form.get('password', '')
        if password != post.password:
            flash('비밀번호가 틀렸습니다.', 'error')
            return render_template('edit.html', post=post)

        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        if not title or not content:
            flash('제목과 내용을 입력해주세요.', 'error')
            return render_template('edit.html', post=post)

        post.title = title
        post.content = content
        post.updated_at = datetime.utcnow()  # 수정 시각 갱신
        db.session.commit()
        flash('게시글이 수정되었습니다.', 'success')
        return redirect(url_for('post_detail', post_id=post.id))

    return render_template('edit.html', post=post)


@app.route('/post/<int:post_id>/delete', methods=['POST'])
def post_delete(post_id):
    post = Post.query.get_or_404(post_id)

    # 비밀번호 검증: 일치하지 않으면 삭제하지 않는다.
    password = request.form.get('password', '')
    if password != post.password:
        flash('비밀번호가 틀렸습니다.', 'error')
        return redirect(url_for('post_detail', post_id=post.id))

    # cascade 설정에 의해 연결된 댓글도 함께 삭제된다. (models.py 참고)
    db.session.delete(post)
    db.session.commit()
    flash('게시글이 삭제되었습니다.', 'success')
    return redirect(url_for('index'))


@app.route('/post/<int:post_id>/comment', methods=['POST'])
def comment_create(post_id):
    post = Post.query.get_or_404(post_id)
    author = request.form.get('author', '').strip()
    content = request.form.get('content', '').strip()

    if not author or not content:
        flash('작성자와 댓글 내용을 입력해주세요.', 'error')
    else:
        comment = Comment(post_id=post.id, author=author, content=content)
        db.session.add(comment)
        db.session.commit()
        flash('댓글이 등록되었습니다.', 'success')

    # 댓글 등록 후 같은 게시글 상세 페이지로 돌아간다.
    return redirect(url_for('post_detail', post_id=post.id))


@app.route('/comment/<int:comment_id>/delete', methods=['POST'])
def comment_delete(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    post_id = comment.post_id  # 삭제 후 돌아갈 게시글 ID를 미리 저장
    db.session.delete(comment)
    db.session.commit()
    flash('댓글이 삭제되었습니다.', 'success')
    return redirect(url_for('post_detail', post_id=post_id))


if __name__ == '__main__':
    app.run(debug=True)
