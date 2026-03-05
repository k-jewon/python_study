from flask import Flask, render_template, request, redirect, url_for, flash
from markupsafe import Markup, escape
from models import db, Post, Comment
from datetime import datetime

app = Flask(__name__)


@app.template_filter('nl2br')
def nl2br_filter(value):
    return Markup(escape(value).replace('\n', '<br>\n'))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bulletin.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'

db.init_app(app)

with app.app_context():
    db.create_all()


@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    query = Post.query.order_by(Post.created_at.desc())
    if search:
        query = query.filter(Post.title.contains(search) | Post.content.contains(search))
    posts = query.paginate(page=page, per_page=10, error_out=False)
    return render_template('index.html', posts=posts, search=search)


@app.route('/post/<int:post_id>')
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    post.views += 1
    db.session.commit()
    return render_template('post.html', post=post)


@app.route('/post/create', methods=['GET', 'POST'])
def post_create():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        author = request.form.get('author', '').strip()
        content = request.form.get('content', '').strip()
        if not title or not author or not content:
            flash('모든 항목을 입력해주세요.', 'error')
            return render_template('create.html', title=title, author=author, content=content)
        post = Post(title=title, author=author, content=content)
        db.session.add(post)
        db.session.commit()
        flash('게시글이 등록되었습니다.', 'success')
        return redirect(url_for('post_detail', post_id=post.id))
    return render_template('create.html', title='', author='', content='')


@app.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
def post_edit(post_id):
    post = Post.query.get_or_404(post_id)
    if request.method == 'POST':
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
        post.updated_at = datetime.utcnow()
        db.session.commit()
        flash('게시글이 수정되었습니다.', 'success')
        return redirect(url_for('post_detail', post_id=post.id))
    return render_template('edit.html', post=post)


@app.route('/post/<int:post_id>/delete', methods=['POST'])
def post_delete(post_id):
    post = Post.query.get_or_404(post_id)
    password = request.form.get('password', '')
    if password != post.password:
        flash('비밀번호가 틀렸습니다.', 'error')
        return redirect(url_for('post_detail', post_id=post.id))
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
    return redirect(url_for('post_detail', post_id=post.id))


@app.route('/comment/<int:comment_id>/delete', methods=['POST'])
def comment_delete(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    post_id = comment.post_id
    db.session.delete(comment)
    db.session.commit()
    flash('댓글이 삭제되었습니다.', 'success')
    return redirect(url_for('post_detail', post_id=post_id))


if __name__ == '__main__':
    app.run(debug=True)
