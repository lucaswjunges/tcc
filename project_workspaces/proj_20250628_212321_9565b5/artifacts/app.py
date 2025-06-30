from flask import Flask, render_template, request, redirect, url_for
from models import db, Post, Comment

app = Flask(__name__)

def initialize_database():
    # Criação de posts iniciais para teste
    post1 = Post(title="Primeiro Post", content="Este é o primeiro post do blog.")
    post2 = Post(title="Segundo Post", content="Este é o segundo post do blog.")
    db.session.add_all([post1, post2])
    db.session.commit()

@app.route('/')
def index():
    posts = Post.query.all()
    return render_template('index.html', posts=posts)

@app.route('/post/new', methods=['GET', 'POST'])
def create_post():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        new_post = Post(title=title, content=content)
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('create_post.html')

@app.route('/post/<int:post_id>')
def view_post(post_id):
    post = Post.query.get_or_404(post_id)
    comments = Comment.query.filter_by(post_id=post_id).all()
    return render_template('post.html', post=post, comments=comments)

@app.route('/post/<int:post_id>/comment', methods=['POST'])
def add_comment(post_id):
    content = request.form.get('content')
    post = Post.query.get_or_404(post_id)
    new_comment = Comment(content=content, post_id=post_id)
    db.session.add(new_comment)
    db.session.commit()
    return redirect(url_for('view_post', post_id=post_id))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        initialize_database()
    app.run(debug=True)
