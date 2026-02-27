import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """应用配置类"""

    # Flask基础配置
    SECRET_KEY: str = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG: bool = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    # 项目路径配置
    WORKSPACE_PATH: str = os.environ.get('WORKSPACE_PATH', os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'workspace'))
    PROJECTS_PATH: str = os.path.join(WORKSPACE_PATH, 'projects')

    # LLM配置
    LLM_API_KEY: Optional[str] = os.environ.get('LLM_API_KEY')
    LLM_API_URL: str = os.environ.get('LLM_API_URL', 'https://api.openai.com/v1')
    LLM_MODEL: str = os.environ.get('LLM_MODEL', 'gpt-4')

    # TTS配置
    TTS_DESIGN_MODEL_PATH: str = os.environ.get('TTS_DESIGN_MODEL_PATH', os.path.join(WORKSPACE_PATH, 'design_model'))
    TTS_CLONE_MODEL_PATH: str = os.environ.get('TTS_CLONE_MODEL_PATH', os.path.join(WORKSPACE_PATH, 'clone_model'))
    USE_FLASH_ATTENTION: bool = os.environ.get('USE_FLASH_ATTENTION', 'False').lower() == 'true'

    # 音频配置
    DEFAULT_DURATION: float = float(os.environ.get('DEFAULT_DURATION', '0.2'))
    LINE_BREAK_DURATION: float = float(os.environ.get('LINE_BREAK_DURATION', '0.5'))
    SENTENCE_MARGIN_DURATION: float = float(os.environ.get('SENTENCE_MARGIN_DURATION', '0.3'))

    # API配置
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16MB文件上传限制
    CORS_ORIGINS: str = os.environ.get('CORS_ORIGINS', 'http://localhost:5173,http://localhost:3000')

    # 异步任务配置
    REDIS_URL: str = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

    @classmethod
    def init_app(cls, app):
        """初始化Flask应用配置"""
        app.config['SECRET_KEY'] = cls.SECRET_KEY
        app.config['DEBUG'] = cls.DEBUG
        app.config['MAX_CONTENT_LENGTH'] = cls.MAX_CONTENT_LENGTH

        # 确保工作空间目录存在
        os.makedirs(cls.WORKSPACE_PATH, exist_ok=True)
        os.makedirs(cls.PROJECTS_PATH, exist_ok=True)

        # 确保TTS模型目录存在
        os.makedirs(cls.TTS_DESIGN_MODEL_PATH, exist_ok=True)
        os.makedirs(cls.TTS_CLONE_MODEL_PATH, exist_ok=True)


# 开发环境配置
class DevelopmentConfig(Config):
    DEBUG = True
    CORS_ORIGINS = 'http://localhost:5173'


# 生产环境配置
class ProductionConfig(Config):
    DEBUG = False


# 测试环境配置
class TestingConfig(Config):
    TESTING = True
    DEBUG = True


# 配置映射
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}