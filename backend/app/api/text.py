from flask import Blueprint, request, jsonify
from pydantic import ValidationError
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '..', 'src'))

from app.core.project_adapter import ProjectAdapter
from app.models.response import StandardResponse, ErrorResponse

text_bp = Blueprint('text', __name__)


@text_bp.route('/process-text', methods=['POST'])
def process_text(project_id):
    """处理文本（分割、引语检测）"""
    try:
        adapter = ProjectAdapter(project_id)
        project_info = adapter.get_project_info()

        if not project_info.get('exists'):
            return jsonify(ErrorResponse(
                error=f'Project {project_id} not found'
            ).dict()), 404

        # 获取请求数据
        data = request.get_json() or {}

        # 目前使用项目创建时提供的文本
        # 如果提供新文本，可以在这里处理
        raw_text = data.get('raw_text')

        if raw_text:
            # TODO: 实现更新文本的功能
            pass

        # 文本处理已经在项目创建时完成
        segments = adapter.get_text_segments()

        return jsonify(StandardResponse(
            success=True,
            message=f'Text processed into {len(segments)} segments',
            data={'segments': segments}
        ).dict())

    except Exception as e:
        return jsonify(ErrorResponse(
            error=str(e),
            error_type=e.__class__.__name__
        ).dict()), 500


@text_bp.route('/segments', methods=['GET'])
def get_segments(project_id):
    """获取文本分段"""
    try:
        adapter = ProjectAdapter(project_id)
        project_info = adapter.get_project_info()

        if not project_info.get('exists'):
            return jsonify(ErrorResponse(
                error=f'Project {project_id} not found'
            ).dict()), 404

        segments = adapter.get_text_segments()

        return jsonify(StandardResponse(
            success=True,
            message=f'Found {len(segments)} text segments',
            data={'segments': segments}
        ).dict())

    except Exception as e:
        return jsonify(ErrorResponse(
            error=str(e),
            error_type=e.__class__.__name__
        ).dict()), 500


@text_bp.route('/segments/<int:segment_index>', methods=['GET'])
def get_segment(project_id, segment_index):
    """获取单个文本片段"""
    try:
        adapter = ProjectAdapter(project_id)
        project_info = adapter.get_project_info()

        if not project_info.get('exists'):
            return jsonify(ErrorResponse(
                error=f'Project {project_id} not found'
            ).dict()), 404

        segments = adapter.get_text_segments()

        if segment_index < 0 or segment_index >= len(segments):
            return jsonify(ErrorResponse(
                error=f'Segment index {segment_index} out of range'
            ).dict()), 404

        return jsonify(StandardResponse(
            success=True,
            message='Segment found',
            data=segments[segment_index]
        ).dict())

    except Exception as e:
        return jsonify(ErrorResponse(
            error=str(e),
            error_type=e.__class__.__name__
        ).dict()), 500