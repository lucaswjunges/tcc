from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Inicializar a aplicação Flask
app = Flask(__name__)

# Configuração do SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelo de Post
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    comments = db.relationship('Comment', backref='post', lazy=True)

# Modelo de Comentário
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

# Criar as tabelas no banco de dados
with app.app_context():
    db.create_all()

# Rota para listar todos os posts
@app.route('/posts', methods=['GET'])
def get_posts():
    posts = Post.query.all()
    return jsonify([{
        'id': post.id,
        'title': post.title,
        'content': post.content,
        'date_posted': post.date_posted.isoformat()
    } for post in posts]), 200

# Rota para criar um novo post
@app.route('/posts', methods=['POST'])
def create_post():
    data = request.get_json()
    if not data or 'title' not in data or 'content' not in data:
        return jsonify({'error': 'Dados insuficientes para criar o post'}), 400
    
    new_post = Post(title=data['title'], content=data['content'])
    db.session.add(new_post)
    db.session.commit()
    
    return jsonify({
        'id': new_post.id,
        'title': new_post.title,
        'content': new_post.content,
        'date_posted': new_post.date_posted.isoformat()
    }), 201

# Rota para visualizar um post por ID
@app.route('/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    post = Post.query.get_or_404(post_id)
    return jsonify({
        'id': post.id,
        'title': post.title,
        'content': post.content,
        'date_posted': post.date_posted.isoformat(),
        'comments': [
            {
                'id': comment.id,
                'content': comment.content,
                'date_posted': comment.date_posted.isoformat()
            } for comment in post.comments
        ]
    }), 200

# Rota para adicionar comentários a um post
@app.route('/posts/<int:post_id>/comments', methods=['POST'])
def add_comment(post_id):
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({'error': 'Dados insuficientes para adicionar comentário'}), 400
    
    post = Post.query.get_or_404(post_id)
    new_comment = Comment(content=data['content'], post_id=post_id)
    db.session.add(new_comment)
    db.session.commit()
    
    return jsonify({
        'id': new_comment.id,
        'content': new_comment.content,
        'date_posted': new_comment.date_posted.isoformat(),
        'post_id': new_comment.post_id
    }), 201

# Página inicial
@app.route('/')
def index():
    return 'Bem-vindo ao blog usando Flask!'

# Iniciar a aplicação
if __name__ == '__main__':
    app.run(debug=True)
