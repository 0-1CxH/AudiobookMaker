from flask import Flask, jsonify
from flask_cors import CORS
import os
import sys

# 添加现有src目录到Python路径，以便导入现有模块
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'src'))

from .config import config


def create_app(config_name='default'):
    """创建Flask应用工厂函数"""

    app = Flask(__name__)

    # 加载配置
    cfg = config[config_name]
    app.config.from_object(cfg)
    cfg.init_app(app)

    # 配置CORS
    cors_origins = app.config['CORS_ORIGINS'].split(',')
    CORS(app, origins=cors_origins, supports_credentials=True)

    # 注册错误处理器
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad request'}), 400

    # 注册API蓝图
    from .api.projects import projects_bp
    from .api.text import text_bp
    from .api.characters import characters_bp
    from .api.dialogues import dialogues_bp
    from .api.voice import voice_bp
    from .api.audio import audio_bp
    from .api.output import output_bp

    app.register_blueprint(projects_bp, url_prefix='/api/projects')
    app.register_blueprint(text_bp, url_prefix='/api/projects/<project_id>/text')
    app.register_blueprint(characters_bp, url_prefix='/api/projects/<project_id>/characters')
    app.register_blueprint(dialogues_bp, url_prefix='/api/projects/<project_id>/dialogues')
    app.register_blueprint(voice_bp, url_prefix='/api/projects/<project_id>/voice')
    app.register_blueprint(audio_bp, url_prefix='/api/projects/<project_id>/audio')
    app.register_blueprint(output_bp, url_prefix='/api/projects/<project_id>/output')

    # 健康检查端点
    @app.route('/api/health')
    def health_check():
        return jsonify({'status': 'healthy', 'service': 'abm-backend'})

    @app.route('/')
    def index():
        return jsonify({
            'name': 'ABM Backend API',
            'version': '1.0.0',
            'endpoints': {
                'projects': '/api/projects',
                'health': '/api/health'
            }
        })

    return app