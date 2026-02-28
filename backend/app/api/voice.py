from flask import Blueprint, request, jsonify, send_file
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '..', 'src'))

from app.core.project_adapter import ProjectAdapter
from app.models.response import StandardResponse, ErrorResponse

voice_bp = Blueprint('voice', __name__)


@voice_bp.route('/designs', methods=['GET'])
def get_voice_designs(project_id):
    """获取语音设计列表"""
    try:
        adapter = ProjectAdapter(project_id)
        project_info = adapter.get_project_info()

        if not project_info.get('exists'):
            return jsonify(ErrorResponse(
                error=f'Project {project_id} not found'
            ).dict()), 404

        designs = adapter.get_voice_designs()

        return jsonify(StandardResponse(
            success=True,
            message=f'Found {len(designs)} voice designs',
            data={'voice_designs': designs}
        ).dict())

    except Exception as e:
        return jsonify(ErrorResponse(
            error=str(e),
            error_type=e.__class__.__name__
        ).dict()), 500


@voice_bp.route('/generate-designs', methods=['POST'])
def generate_voice_designs(project_id):
    """生成语音设计"""
    try:
        adapter = ProjectAdapter(project_id)
        project_info = adapter.get_project_info()

        if not project_info.get('exists'):
            return jsonify(ErrorResponse(
                error=f'Project {project_id} not found'
            ).dict()), 404

        result = adapter.generate_voice_designs()

        if not result.get('success'):
            return jsonify(ErrorResponse(
                error=result.get('error', 'Failed to generate voice designs')
            ).dict()), 500

        return jsonify(StandardResponse(
            success=True,
            message=result.get('message', 'Voice designs generated successfully'),
            data={'voice_designs': result.get('voice_designs', [])}
        ).dict())

    except Exception as e:
        return jsonify(ErrorResponse(
            error=str(e),
            error_type=e.__class__.__name__
        ).dict()), 500


@voice_bp.route('/designs/<voice_name>', methods=['GET'])
def get_voice_design(project_id, voice_name):
    """获取单个语音设计"""
    try:
        adapter = ProjectAdapter(project_id)
        project_info = adapter.get_project_info()

        if not project_info.get('exists'):
            return jsonify(ErrorResponse(
                error=f'Project {project_id} not found'
            ).dict()), 404

        designs = adapter.get_voice_designs()
        design = next((d for d in designs if d['name'] == voice_name), None)

        if not design:
            return jsonify(ErrorResponse(
                error=f'Voice design {voice_name} not found'
            ).dict()), 404

        return jsonify(StandardResponse(
            success=True,
            message='Voice design found',
            data={'voice_design': design}
        ).dict())

    except Exception as e:
        return jsonify(ErrorResponse(
            error=str(e),
            error_type=e.__class__.__name__
        ).dict()), 500


@voice_bp.route('/designs/<voice_name>/update', methods=['PUT'])
def update_voice_design(project_id, voice_name):
    """更新语音设计"""
    try:
        data = request.get_json()
        if not data:
            return jsonify(ErrorResponse(
                error='Request body is required'
            ).dict()), 400

        tts_instruction = data.get('tts_instruction')
        reference_text = data.get('reference_text')

        if not tts_instruction and not reference_text:
            return jsonify(ErrorResponse(
                error='At least one field (tts_instruction or reference_text) is required'
            ).dict()), 400

        adapter = ProjectAdapter(project_id)
        project_info = adapter.get_project_info()

        if not project_info.get('exists'):
            return jsonify(ErrorResponse(
                error=f'Project {project_id} not found'
            ).dict()), 404

        # TODO: 在ProjectAdapter中添加更新语音设计的方法
        # 目前暂时返回成功
        return jsonify(StandardResponse(
            success=True,
            message='Voice design updated (feature not fully implemented yet)',
            data={'voice_name': voice_name}
        ).dict())

    except Exception as e:
        return jsonify(ErrorResponse(
            error=str(e),
            error_type=e.__class__.__name__
        ).dict()), 500


@voice_bp.route('/generate-reference-audio', methods=['POST'])
def generate_reference_audio(project_id):
    """生成参考音频"""
    try:
        data = request.get_json() or {}
        character_name = data.get('character_name')

        adapter = ProjectAdapter(project_id)
        project_info = adapter.get_project_info()

        if not project_info.get('exists'):
            return jsonify(ErrorResponse(
                error=f'Project {project_id} not found'
            ).dict()), 404

        # 调用ProjectAdapter生成参考音频
        result = adapter.generate_reference_audio(character_name)

        if not result.get('success'):
            return jsonify(ErrorResponse(
                error=result.get('error', 'Failed to generate reference audio')
            ).dict()), 500

        return jsonify(StandardResponse(
            success=True,
            message=result.get('message', 'Reference audio generated successfully'),
            data={
                'voice_designs': result.get('voice_designs', []),
                'character_name': result.get('character_name')
            }
        ).dict())

    except Exception as e:
        return jsonify(ErrorResponse(
            error=str(e),
            error_type=e.__class__.__name__
        ).dict()), 500


@voice_bp.route('/test', methods=['POST'])
def test_voice(project_id):
    """测试语音"""
    try:
        data = request.get_json()
        if not data:
            return jsonify(ErrorResponse(
                error='Request body is required'
            ).dict()), 400

        voice_name = data.get('voice_name')
        text = data.get('text')

        if not voice_name:
            return jsonify(ErrorResponse(
                error='voice_name is required'
            ).dict()), 400

        if not text:
            return jsonify(ErrorResponse(
                error='text is required'
            ).dict()), 400

        adapter = ProjectAdapter(project_id)
        project_info = adapter.get_project_info()

        if not project_info.get('exists'):
            return jsonify(ErrorResponse(
                error=f'Project {project_id} not found'
            ).dict()), 404

        # TODO: 实现语音测试功能
        return jsonify(StandardResponse(
            success=True,
            message='Voice test started (feature not fully implemented yet)',
            data={'voice_name': voice_name, 'text_length': len(text)}
        ).dict())

    except Exception as e:
        return jsonify(ErrorResponse(
            error=str(e),
            error_type=e.__class__.__name__
        ).dict()), 500


@voice_bp.route('/reference-audio/<voice_name>', methods=['GET'])
def get_reference_audio(project_id, voice_name):
    """获取参考音频文件"""
    try:
        adapter = ProjectAdapter(project_id)
        project_info = adapter.get_project_info()

        if not project_info.get('exists'):
            return jsonify(ErrorResponse(
                error=f'Project {project_id} not found'
            ).dict()), 404

        # Get voice designs to check if reference audio exists
        designs = adapter.get_voice_designs()
        design = next((d for d in designs if d['name'] == voice_name), None)

        if not design:
            return jsonify(ErrorResponse(
                error=f'Voice design {voice_name} not found'
            ).dict()), 404

        if not design.get('has_reference_audio'):
            return jsonify(ErrorResponse(
                error=f'Reference audio not generated for voice {voice_name}'
            ).dict()), 404
        
        # Construct the audio file path
        # The reference audio is stored in voice_lib_folder_path/{voice_name}.wav
        # We need to get the voice_lib_folder_path from the project
        if not adapter.project or not adapter.project.voice_manager:
            return jsonify(ErrorResponse(
                error='Voice manager not available'
            ).dict()), 500

        voice_lib_folder_path = adapter.project.voice_manager.voice_lib_folder_path
        audio_file_path = os.path.join(voice_lib_folder_path, f"{voice_name}.wav")

        if not os.path.exists(audio_file_path):
            return jsonify(ErrorResponse(
                error=f'Reference audio file not found for voice {voice_name}'
            ).dict()), 404

        # Send the audio file
        return send_file(
            os.path.abspath(audio_file_path),
            as_attachment=False,
            download_name=f'{voice_name}_reference_audio.wav',
            mimetype='audio/wav'
        )

    except Exception as e:
        return jsonify(ErrorResponse(
            error=str(e),
            error_type=e.__class__.__name__
        ).dict()), 500