from flask import Blueprint, request, jsonify
from pydantic import ValidationError
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '..', 'src'))

from app.core.project_adapter import ProjectAdapter
from app.models.response import StandardResponse, ErrorResponse, UpdateDialogueRequest

dialogues_bp = Blueprint('dialogues', __name__)


@dialogues_bp.route('/', methods=['GET'])
def get_dialogues(project_id):
    """获取对话分配状态"""
    try:
        adapter = ProjectAdapter(project_id)
        project_info = adapter.get_project_info()

        if not project_info.get('exists'):
            return jsonify(ErrorResponse(
                error=f'Project {project_id} not found'
            ).dict()), 404

        segments = adapter.get_text_segments()

        # 统计信息
        # 需要分配的segment是非DEFAULT且非PLACEHOLDER的segment
        total_quotes = sum(1 for s in segments if s['tag'] != 'DEFAULT' and s['tag'] != 'PLACEHOLDER')
        allocated_quotes = sum(1 for s in segments if s['allocated_speaker'])
        unallocated_quotes = total_quotes - allocated_quotes

        return jsonify(StandardResponse(
            success=True,
            message=f'Found {len(segments)} segments, {allocated_quotes}/{total_quotes} quotes allocated',
            data={
                'segments': segments,
                'statistics': {
                    'total_segments': len(segments),
                    'total_quotes': total_quotes,
                    'allocated_quotes': allocated_quotes,
                    'unallocated_quotes': unallocated_quotes,
                    'allocation_rate': allocated_quotes / total_quotes if total_quotes > 0 else 0
                }
            }
        ).dict())

    except Exception as e:
        return jsonify(ErrorResponse(
            error=str(e),
            error_type=e.__class__.__name__
        ).dict()), 500


@dialogues_bp.route('/allocate', methods=['POST'])
def allocate_dialogues(project_id):
    """自动分配对话"""
    try:
        adapter = ProjectAdapter(project_id)
        project_info = adapter.get_project_info()

        if not project_info.get('exists'):
            return jsonify(ErrorResponse(
                error=f'Project {project_id} not found'
            ).dict()), 404

        result = adapter.allocate_dialogues()

        if not result.get('success'):
            return jsonify(ErrorResponse(
                error=result.get('error', 'Failed to allocate dialogues')
            ).dict()), 500

        return jsonify(StandardResponse(
            success=True,
            message=f'Allocated {result.get("allocated_count", 0)} dialogues',
            data={
                'allocated_count': result.get('allocated_count'),
                'segments': result.get('segments', [])
            }
        ).dict())

    except Exception as e:
        return jsonify(ErrorResponse(
            error=str(e),
            error_type=e.__class__.__name__
        ).dict()), 500


@dialogues_bp.route('/<int:segment_index>', methods=['PUT'])
def update_dialogue(project_id, segment_index):
    """更新单个对话分配"""
    try:
        # 验证请求数据
        data = request.get_json()
        if not data:
            return jsonify(ErrorResponse(
                error='Request body is required'
            ).dict()), 400

        try:
            req = UpdateDialogueRequest(**data)
        except ValidationError as e:
            return jsonify(ErrorResponse(
                error='Invalid request data',
                details=e.errors()
            ).dict()), 400

        adapter = ProjectAdapter(project_id)
        project_info = adapter.get_project_info()

        if not project_info.get('exists'):
            return jsonify(ErrorResponse(
                error=f'Project {project_id} not found'
            ).dict()), 404

        # 检查片段是否存在
        segments = adapter.get_text_segments()
        if segment_index < 0 or segment_index >= len(segments):
            return jsonify(ErrorResponse(
                error=f'Segment index {segment_index} out of range'
            ).dict()), 404

        # 检查是否为可分配的segment（非DEFAULT且非PLACEHOLDER）
        segment = segments[segment_index]
        if segment['tag'] == 'DEFAULT' or segment['tag'] == 'PLACEHOLDER':
            return jsonify(ErrorResponse(
                error=f'Segment {segment_index} is not assignable (tag: {segment["tag"]})'
            ).dict()), 400

        # 检查角色是否存在
        characters = adapter.get_characters()
        character_names = [c['name'] for c in characters]
        if req.speaker not in character_names:
            return jsonify(ErrorResponse(
                error=f'Character {req.speaker} not found'
            ).dict()), 404

        # 更新对话分配
        result = adapter.update_dialogue_allocation(segment_index, req.speaker)

        if not result.get('success'):
            return jsonify(ErrorResponse(
                error=result.get('error', 'Failed to update dialogue allocation')
            ).dict()), 500

        return jsonify(StandardResponse(
            success=True,
            message='Dialogue allocation updated',
            data={'segment': result.get('segment')}
        ).dict())

    except Exception as e:
        return jsonify(ErrorResponse(
            error=str(e),
            error_type=e.__class__.__name__
        ).dict()), 500


@dialogues_bp.route('/batch', methods=['POST'])
def batch_update_dialogues(project_id):
    """批量更新对话分配"""
    try:
        data = request.get_json()
        if not data:
            return jsonify(ErrorResponse(
                error='Request body is required'
            ).dict()), 400

        segment_indices = data.get('segment_indices', [])
        speaker = data.get('speaker')

        if not segment_indices:
            return jsonify(ErrorResponse(
                error='segment_indices is required'
            ).dict()), 400

        if not speaker:
            return jsonify(ErrorResponse(
                error='speaker is required'
            ).dict()), 400

        adapter = ProjectAdapter(project_id)
        project_info = adapter.get_project_info()

        if not project_info.get('exists'):
            return jsonify(ErrorResponse(
                error=f'Project {project_id} not found'
            ).dict()), 404

        # 检查角色是否存在
        characters = adapter.get_characters()
        character_names = [c['name'] for c in characters]
        if speaker not in character_names:
            return jsonify(ErrorResponse(
                error=f'Character {speaker} not found'
            ).dict()), 404

        # 批量更新
        updated_segments = []
        failed_segments = []

        for segment_index in segment_indices:
            try:
                result = adapter.update_dialogue_allocation(segment_index, speaker)
                if result.get('success'):
                    updated_segments.append(segment_index)
                else:
                    failed_segments.append({
                        'segment_index': segment_index,
                        'error': result.get('error')
                    })
            except Exception as e:
                failed_segments.append({
                    'segment_index': segment_index,
                    'error': str(e)
                })

        return jsonify(StandardResponse(
            success=True,
            message=f'Updated {len(updated_segments)} segments, {len(failed_segments)} failed',
            data={
                'updated_segments': updated_segments,
                'failed_segments': failed_segments
            }
        ).dict())

    except Exception as e:
        return jsonify(ErrorResponse(
            error=str(e),
            error_type=e.__class__.__name__
        ).dict()), 500