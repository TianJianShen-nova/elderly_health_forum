from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_admin import Admin
from flask_babel import Babel
from flask_admin.contrib.sqla import ModelView
from flask_admin.actions import action
from flask_login import current_user
from flask import redirect, url_for, flash


db = SQLAlchemy()
login_manager = LoginManager()
babel = Babel()
admin = Admin(name='老年人健康论坛管理系统', template_mode='bootstrap3')

def init_admin(app):
    # 导入模型
    from models import User, Post, Comment
    
    # 注册管理视图
    admin.add_view(UserModelView(User, db.session, name='用户管理'))
    admin.add_view(PostModelView(Post, db.session, name='帖子管理'))
    admin.add_view(CommentModelView(Comment, db.session, name='评论管理'))
    
    # 初始化admin
    admin.init_app(app)

class AdminModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    
    def inaccessible_callback(self, name, **kwargs):
        flash('请先登录管理员账号')
        return redirect(url_for('auth.login'))

class UserModelView(AdminModelView):
    column_list = ['id', 'username', 'email', 'is_admin']
    column_searchable_list = ['username', 'email']
    column_filters = ['is_admin']
    form_excluded_columns = ['password_hash', 'posts', 'comments']

class PostModelView(AdminModelView):
    column_list = ['id', 'title', 'author', 'created_at', 'is_approved', 'likes']
    column_searchable_list = ['title', 'content']
    column_filters = ['is_approved', 'created_at']
    form_excluded_columns = ['likes', 'comments']
    can_export = True
    action_disallowed_list = ['delete']

    def on_model_change(self, form, model, is_created):
        if is_created:
            model.author = current_user

    column_formatters = {
        'is_approved': lambda v, c, m, p: '已审核' if m.is_approved else '待审核'
    }

    @action('approve', '批量审核通过', '确定要批量审核通过选中的帖子吗？')
    def action_approve(self, ids):
        from models import Post
        try:
            query = Post.query.filter(Post.id.in_(ids))
            count = 0
            for post in query.all():
                if not post.is_approved:
                    post.is_approved = True
                    count += 1
            db.session.commit()
            flash(f'成功审核通过 {count} 篇帖子')
        except Exception as ex:
            db.session.rollback()
            flash(f'审核操作失败：{str(ex)}')

    @action('reject', '批量拒绝审核', '确定要拒绝选中的帖子吗？')
    def action_reject(self, ids):
        try:
            query = Post.query.filter(Post.id.in_(ids))
            count = 0
            for post in query.all():
                if post.is_approved:
                    post.is_approved = False
                    count += 1
            db.session.commit()
            flash(f'已拒绝 {count} 篇帖子')
        except Exception as ex:
            db.session.rollback()
            flash(f'操作失败：{str(ex)}')

class CommentModelView(AdminModelView):
    
    column_list = ['id', 'author', 'post', 'created_at', 'is_approved']
    column_filters = ['is_approved', 'created_at']
    form_excluded_columns = ['created_at']
    action_disallowed_list = ['delete']
    can_export = True

    column_formatters = {
        'is_approved': lambda v, c, m, p: '已审核' if m.is_approved else '待审核'
    }

    @action('approve', '批量审核通过', '确定要批量审核通过选中的评论吗？')
    def action_approve(self, ids):
        from models import Comment
        try:
            query = Comment.query.filter(Comment.id.in_(ids))
            count = 0
            for comment in query.all():
                if not comment.is_approved:
                    comment.is_approved = True
                    count += 1
            db.session.commit()
            flash(f'成功审核通过 {count} 条评论')
        except Exception as ex:
            db.session.rollback()
            flash(f'审核操作失败：{str(ex)}')

    @action('reject', '批量拒绝审核', '确定要拒绝选中的评论吗？')
    def action_reject(self, ids):
        try:
            query = Comment.query.filter(Comment.id.in_(ids))
            count = 0
            for comment in query.all():
                if comment.is_approved:
                    comment.is_approved = False
                    count += 1
            db.session.commit()
            flash(f'已拒绝 {count} 条评论')
        except Exception as ex:
            db.session.rollback()
            flash(f'操作失败：{str(ex)}')