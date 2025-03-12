from flask import Blueprint, jsonify, request, flash, redirect, url_for, render_template
from flask_login import login_required, current_user, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from models import User, Post, Comment
from extensions import db

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired

bp = Blueprint('admin_routes', __name__, url_prefix='/admin')

class AdminLoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])
    submit = SubmitField('登录')

def init_admin_user():
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@example.com', is_admin=True)
        admin.password_hash = generate_password_hash('admin2025')
        db.session.add(admin)
        db.session.commit()

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('admin.index'))
    
    form = AdminLoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.is_admin and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('admin.index')
            return redirect(next_page)
        flash('用户名或密码错误')
    return render_template('admin_routes/login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('admin.login'))

@bp.route('/approve/<int:post_id>', methods=['POST'])
@login_required
def approve_post(post_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': '您没有权限执行此操作'}), 403
    
    post = Post.query.get_or_404(post_id)
    post.is_approved = True
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/reject/<int:post_id>', methods=['POST'])
@login_required
def reject_post(post_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': '您没有权限执行此操作'}), 403
    
    post = Post.query.get_or_404(post_id)
    post.is_approved = False
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/batch-approve', methods=['POST'])
@login_required
def batch_approve():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': '您没有权限执行此操作'}), 403
    
    data = request.get_json()
    post_ids = data.get('post_ids', [])
    
    if not post_ids:
        return jsonify({'success': False, 'message': '未选择任何帖子'}), 400
    
    try:
        posts = Post.query.filter(Post.id.in_(post_ids)).all()
        for post in posts:
            post.is_approved = True
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500