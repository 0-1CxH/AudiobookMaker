from flask import Blueprint, send_file, jsonify
import os
import sys
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '..', 'src'))

from app.core.project_adapter import ProjectAdapter
from app.models.response import StandardResponse, ErrorResponse

output_bp = Blueprint('output', __name__)


@output_bp.route('/render', methods=['POST'])
def render_audio(project_id):
    """渲染最终音频"""
    try:
        adapter = ProjectAdapter(project_id)
        project_info = adapter.get_project_info()

        if not project_info.get('exists'):
            return jsonify(ErrorResponse(
                error=f'Project {project_id} not found'
            ).dict()), 404

        result = adapter.render_final_audio()

        if not result.get('success'):
            return jsonify(ErrorResponse(
                error=result.get('error', 'Failed to render final audio')
            ).dict()), 500

        return jsonify(StandardResponse(
            success=True,
            message=result.get('message', 'Final audio rendered successfully'),
            data={
                'final_audio_path': result.get('final_audio_path'),
                'download_url': f'/api/projects/{project_id}/output/download'
            }
        ).dict())

    except Exception as e:
        return jsonify(ErrorResponse(
            error=str(e),
            error_type=e.__class__.__name__
        ).dict()), 500


@output_bp.route('/download', methods=['GET'])
def download_final_audio(project_id):
    """下载最终音频文件"""
    try:
        adapter = ProjectAdapter(project_id)
        project_info = adapter.get_project_info()

        if not project_info.get('exists'):
            return jsonify(ErrorResponse(
                error=f'Project {project_id} not found'
            ).dict()), 404

        # 检查最终音频文件是否存在
        final_audio_path = os.path.join(
            os.environ.get('WORKSPACE_PATH', './workspace'),
            'projects',
            project_id,
            'final_audio.wav'
        )

        if not os.path.exists(final_audio_path):
            return jsonify(ErrorResponse(
                error='Final audio file not found. Please render it first.'
            ).dict()), 404

        # 发送文件
        return send_file(
            final_audio_path,
            as_attachment=True,
            download_name=f'{project_id}_final_audio.wav',
            mimetype='audio/wav'
        )

    except Exception as e:
        return jsonify(ErrorResponse(
            error=str(e),
            error_type=e.__class__.__name__
        ).dict()), 500


@output_bp.route('/status', methods=['GET'])
def get_output_status(project_id):
    """获取输出状态"""
    try:
        adapter = ProjectAdapter(project_id)
        project_info = adapter.get_project_info()

        if not project_info.get('exists'):
            return jsonify(ErrorResponse(
                error=f'Project {project_id} not found'
            ).dict()), 404

        # 检查最终音频文件是否存在
        final_audio_path = os.path.join(
            os.environ.get('WORKSPACE_PATH', './workspace'),
            'projects',
            project_id,
            'final_audio.wav'
        )

        final_audio_exists = os.path.exists(final_audio_path)

        # 获取文件信息
        file_info = None
        if final_audio_exists:
            stat_info = os.stat(final_audio_path)
            file_info = {
                'size': stat_info.st_size,
                'created': time.ctime(stat_info.st_ctime),
                'modified': time.ctime(stat_info.st_mtime)
            }

        return jsonify(StandardResponse(
            success=True,
            message='Output status retrieved',
            data={
                'final_audio_exists': final_audio_exists,
                'final_audio_path': final_audio_path if final_audio_exists else None,
                'file_info': file_info,
                'download_available': final_audio_exists
            }
        ).dict())

    except Exception as e:
        return jsonify(ErrorResponse(
            error=str(e),
            error_type=e.__class__.__name__
        ).dict()), 500


@output_bp.route('/metadata', methods=['GET'])
def get_metadata(project_id):
    """获取项目元数据"""
    try:
        adapter = ProjectAdapter(project_id)
        project_info = adapter.get_project_info()

        if not project_info.get('exists'):
            return jsonify(ErrorResponse(
                error=f'Project {project_id} not found'
            ).dict()), 404

        # 获取项目信息
        characters = adapter.get_characters()
        segments = adapter.get_text_segments()
        voice_designs = adapter.get_voice_designs()

        # 统计信息
        generated_audio_count = sum(1 for s in segments if s['has_audio'])

        metadata = {
            'project': project_info,
            'statistics': {
                'character_count': len(characters),
                'segment_count': len(segments),
                'generated_audio_count': generated_audio_count,
                'voice_design_count': len(voice_designs),
                'total_text_length': sum(len(s['content']) for s in segments)
            },
            'characters': characters[:10],  # 限制数量
            'voice_designs': voice_designs[:5]  # 限制数量
        }

        return jsonify(StandardResponse(
            success=True,
            message='Project metadata retrieved',
            data=metadata
        ).dict())

    except Exception as e:
        return jsonify(ErrorResponse(
            error=str(e),
            error_type=e.__class__.__name__
        ).dict()), 500


@output_bp.route('/metadata/update', methods=['PUT'])
def update_metadata(project_id):
    """更新项目元数据"""
    try:
        # TODO: 实现更新元数据的功能
        # 可以更新项目标题、描述、作者等信息
        return jsonify(StandardResponse(
            success=True,
            message='Metadata update endpoint (feature not fully implemented yet)',
            data={'project_id': project_id}
        ).dict())

    except Exception as e:
        return jsonify(ErrorResponse(
            error=str(e),
            error_type=e.__class__.__name__
        ).dict()), 500