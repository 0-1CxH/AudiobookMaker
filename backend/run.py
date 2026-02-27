#!/usr/bin/env python3
"""Flask应用启动脚本"""

import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app

app = create_app(os.environ.get('FLASK_CONFIG', 'default'))

if __name__ == '__main__':
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    print(f"Starting ABM Backend API on http://{host}:{port}")
    print(f"Debug mode: {debug}")
    print(f"Workspace path: {app.config['WORKSPACE_PATH']}")

    app.run(host=host, port=port, debug=debug)