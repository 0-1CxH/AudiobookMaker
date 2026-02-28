from flask import Blueprint, request, jsonify
from pydantic import ValidationError
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '..', 'src'))

@characters_bp.route('/<character_name>/generate-description', methods=['POST'])
def generate_character_description(project_id, character_name):
    """生成角色描述"""
    try:
        # 验证请求数据
        data = request.get_json()
        if not data:
            return jsonify(ErrorResponse(
                error='Request body is required'
            ).dict()), 400

        try:
            req = GenerateCharacterDescriptionRequest(**data)
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

        # 检查角色是否已存在
        characters = adapter.get_characters()
        existing_characters = [c['name'] for c in characters]
        if character_name not in existing_characters:
            return jsonify(ErrorResponse(
                error=f'Character {character_name} not found'
            ).dict()), 404

        # 生成角色描述
        result = adapter.generate_character_description(
            character_name=character_name,
            suggestion=req.suggestion or ""
        )

        if not result.get('success'):
            return jsonify(ErrorResponse(
                error=result.get('error', 'Failed to generate character description')
            ).dict()), 500

        return jsonify(StandardResponse(
            success=True,
            message=f'Character description generated for {character_name}',
            data={
                'character_name': result.get('character_name'),
                'description': result.get('description')
            }
        ).dict())

    except Exception as e:
        return jsonify(ErrorResponse(
            error=str(e),
            error_type=e.__class__.__name__
        ).dict()), 500

characters_bp = Blueprint('characters', __name__)


@characters_bp.route('/', methods=['GET'])
def get_characters(project_id):
    """获取角色列表"""
    try:
        adapter = ProjectAdapter(project_id)
        project_info = adapter.get_project_info()

        if not project_info.get('exists'):
            return jsonify(ErrorResponse(
                error=f'Project {project_id} not found'
            ).dict()), 404

        characters = adapter.get_characters()

        return jsonify(StandardResponse(
            success=True,
            message=f'Found {len(characters)} characters',
            data={'characters': characters}
        ).dict())

    except Exception as e:
        return jsonify(ErrorResponse(
            error=str(e),
            error_type=e.__class__.__name__
        ).dict()), 500


@characters_bp.route('/extract', methods=['POST'])
def extract_characters(project_id):
    """自动提取角色"""
    try:
        adapter = ProjectAdapter(project_id)
        project_info = adapter.get_project_info()

        if not project_info.get('exists'):
            return jsonify(ErrorResponse(
                error=f'Project {project_id} not found'
            ).dict()), 404

        result = adapter.extract_characters()

        if not result.get('success'):
            return jsonify(ErrorResponse(
                error=result.get('error', 'Failed to extract characters')
            ).dict()), 500

        return jsonify(StandardResponse(
            success=True,
            message=result.get('message', 'Characters extracted successfully'),
            data={'characters': result.get('characters', [])}
        ).dict())

    except Exception as e:
        return jsonify(ErrorResponse(
            error=str(e),
            error_type=e.__class__.__name__
        ).dict()), 500


@characters_bp.route('/', methods=['POST'])
def add_character(project_id):
    """添加角色"""
    try:
        # 验证请求数据
        data = request.get_json()
        if not data:
            return jsonify(ErrorResponse(
                error='Request body is required'
            ).dict()), 400

        try:
            req = AddCharacterRequest(**data)
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

        # 检查角色是否已存在
        characters = adapter.get_characters()
        existing_characters = [c['name'] for c in characters]
        if req.name in existing_characters:
            return jsonify(ErrorResponse(
                error=f'Character {req.name} already exists'
            ).dict()), 409

        # 添加角色
        result = adapter.add_character({
            'name': req.name,
            'description': req.description,
            'requires_tts': req.requires_tts,
            'voice_name': req.voice_name
        })

        if not result.get('success'):
            return jsonify(ErrorResponse(
                error=result.get('error', 'Failed to add character')
            ).dict()), 500

        return jsonify(StandardResponse(
            success=True,
            message='Character added successfully',
            data={'character': result.get('character')}
        ).dict()), 201

    except Exception as e:
        return jsonify(ErrorResponse(
            error=str(e),
            error_type=e.__class__.__name__
        ).dict()), 500


@characters_bp.route('/<character_name>', methods=['GET'])
def get_character(project_id, character_name):
    """获取单个角色信息"""
    try:
        adapter = ProjectAdapter(project_id)
        project_info = adapter.get_project_info()

        if not project_info.get('exists'):
            return jsonify(ErrorResponse(
                error=f'Project {project_id} not found'
            ).dict()), 404

        characters = adapter.get_characters()
        character = next((c for c in characters if c['name'] == character_name), None)

        if not character:
            return jsonify(ErrorResponse(
                error=f'Character {character_name} not found'
            ).dict()), 404

        return jsonify(StandardResponse(
            success=True,
            message='Character found',
            data={'character': character}
        ).dict())

    except Exception as e:
        return jsonify(ErrorResponse(
            error=str(e),
            error_type=e.__class__.__name__
        ).dict()), 500


@characters_bp.route('/<character_name>', methods=['PUT'])
def update_character(project_id, character_name):
    """更新角色信息"""
    try:
        # 验证请求数据
        data = request.get_json()
        if not data:
            return jsonify(ErrorResponse(
                error='Request body is required'
            ).dict()), 400

        try:
            req = UpdateCharacterRequest(**data)
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

        # 更新角色
        result = adapter.update_character(character_name, {
            'description': req.description,
            'requires_tts': req.requires_tts,
            'voice_name': req.voice_name
        })

        if not result.get('success'):
            return jsonify(ErrorResponse(
                error=result.get('error', 'Failed to update character')
            ).dict()), 500

        return jsonify(StandardResponse(
            success=True,
            message='Character updated successfully',
            data={'character': result.get('character')}
        ).dict())

    except Exception as e:
        return jsonify(ErrorResponse(
            error=str(e),
            error_type=e.__class__.__name__
        ).dict()), 500


@characters_bp.route('/<character_name>', methods=['DELETE'])
def delete_character(project_id, character_name):
    """删除角色"""
    try:
        adapter = ProjectAdapter(project_id)
        project_info = adapter.get_project_info()

        if not project_info.get('exists'):
            return jsonify(ErrorResponse(
                error=f'Project {project_id} not found'
            ).dict()), 404

        result = adapter.delete_character(character_name)

        if not result.get('success'):
            return jsonify(ErrorResponse(
                error=result.get('error', 'Failed to delete character')
            ).dict()), 500

        return jsonify(StandardResponse(
            success=True,
            message=result.get('message', 'Character deleted successfully')
        ).dict())

    except Exception as e:
        return jsonify(ErrorResponse(
            error=str(e),
            error_type=e.__class__.__name__
        ).dict()), 500