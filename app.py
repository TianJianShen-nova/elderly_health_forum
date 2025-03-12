from flask import Flask
from flask_cors import CORS
from extensions import db, login_manager, babel, admin
from models import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def nl2br(value):
    from flask import Markup
    return Markup(value.replace('\n', '<br>'))

def create_app():
    app = Flask(__name__)
    
    # 配置
    app.config['SECRET_KEY'] = 'admin2025.'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///elderly_health_forum.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['BABEL_DEFAULT_LOCALE'] = 'zh_CN'
    
    # 添加全局函数到Jinja2环境
    app.jinja_env.globals.update({
        'max': max,
        'min': min
    })
    
    # 添加自定义过滤器
    app.jinja_env.filters['nl2br'] = nl2br
    
    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)
    babel.init_app(app)
    from extensions import init_admin
    init_admin(app)
    CORS(app)
    
    # 注册蓝图
    from routes import main, auth, admin_routes#, admin
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(admin_routes.bp)
    #app.register_blueprint(admin.bp)

    # 初始化管理员账号
    with app.app_context():
        db.create_all()
        admin_routes.init_admin_user()
    
    return app