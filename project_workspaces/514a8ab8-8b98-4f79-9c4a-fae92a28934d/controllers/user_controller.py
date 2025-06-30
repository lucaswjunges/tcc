from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.user import User
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db

user_bp = Blueprint('user', __name__)

@user_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('As senhas não coincidem.', 'error')
            return redirect(url_for('user.register'))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email já cadastrado.', 'error')
            return redirect(url_for('user.register'))
        
        hashed_password = generate_password_hash(password, method='sha256')
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registro realizado com sucesso!', 'success')
        return redirect(url_for('user.login'))

    return render_template('register.html')


@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('main.index'))  # Redireciona para a página principal após o login
        else:
            flash('Credenciais inválidas.', 'error')
            return redirect(url_for('user.login'))
    return render_template('login.html')


@user_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('main.index'))  # Redireciona para a página principal após o logout

@user_bp.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('Você precisa estar logado para acessar esta página.', 'error')
        return redirect(url_for('user.login'))

    user = User.query.get(session['user_id'])
    return render_template('profile.html', user=user)