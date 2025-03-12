from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from models import Post, Comment, Like, User
from forms import PostForm, CommentForm
from datetime import datetime

bp = Blueprint('main', __name__)

@bp.route('/')
@bp.route('/index')
def index():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter_by(is_approved=True).order_by(Post.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False)
    return render_template('main/index.html', title='首页', posts=posts)

@bp.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('帖子已提交，等待管理员审核')
        return redirect(url_for('main.index'))
    return render_template('main/create_post.html', title='发帖', form=form)

@bp.route('/post/<int:id>')
def view_post(id):
    post = Post.query.get_or_404(id)
    if not post.is_approved and (not current_user.is_authenticated or 
                               (current_user.id != post.author_id and not current_user.is_admin)):
        flash('该帖子正在审核中')
        return redirect(url_for('main.index'))
    form = CommentForm()
    comments = Comment.query.filter_by(post_id=id, is_approved=True).order_by(Comment.created_at.desc()).all()
    return render_template('main/post.html', post=post, comments=comments, form=form)

@bp.route('/post/<int:id>/comment', methods=['POST'])
@login_required
def add_comment(id):
    post = Post.query.get_or_404(id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(content=form.content.data, author=current_user, post=post)
        db.session.add(comment)
        db.session.commit()
        flash('评论已提交，等待管理员审核')
    return redirect(url_for('main.view_post', id=id))

@bp.route('/post/<int:id>/like', methods=['POST'])
@login_required
def like_post(id):
    post = Post.query.get_or_404(id)
    like = Like.query.filter_by(user_id=current_user.id, post_id=id).first()
    
    if like is None:
        like = Like(user_id=current_user.id, post_id=id)
        db.session.add(like)
        post.likes = max(0, post.likes + 1)
        db.session.commit()
        return jsonify({'status': 'success', 'likes': post.likes})
    else:
        db.session.delete(like)
        post.likes = max(0, post.likes - 1)
        db.session.commit()
        return jsonify({'status': 'success', 'likes': post.likes})

@bp.route('/user/<int:id>')
def user_profile(id):
    user = User.query.get_or_404(id)
    posts = Post.query.filter_by(author_id=id, is_approved=True).order_by(Post.created_at.desc()).all()
    return render_template('main/profile.html', user=user, posts=posts)