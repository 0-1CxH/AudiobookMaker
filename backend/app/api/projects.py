from flask import Blueprint, request, jsonify
from pydantic import ValidationError
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '..', 'src'))

from app.core.project_adapter import ProjectAdapter
from app.models.response import StandardResponse, ErrorResponse, CreateProjectRequest, ProjectInfo

projects_bp = Blueprint('projects', __name__)


@projects_bp.route('/', methods=['GET'])
def list_projects():
    """获取项目列表"""
    try:
        # 获取工作空间路径
        workspace_path = os.environ.get('WORKSPACE_PATH', './workspace')
        projects_path = os.path.join(workspace_path, 'projects')

        if not os.path.exists(projects_path):
            return jsonify(StandardResponse(
                success=True,
                message='No projects found',
                data={'projects': []}
            ).dict())

        # 列出所有项目目录
        projects = []
        for item in os.listdir(projects_path):
            project_path = os.path.join(projects_path, item)
            if os.path.isdir(project_path):
                metadata_path = os.path.join(project_path, 'project_metadata.json')
                project_info = {
                    'project_id': item,
                    'exists': os.path.exists(metadata_path),
                    'name': item
                }

                if os.path.exists(metadata_path):
                    try:
                        adapter = ProjectAdapter(item)
                        info = adapter.get_project_info()
                        project_info.update(info)
                    except Exception:
                        pass

                projects.append(project_info)

        return jsonify(StandardResponse(
            success=True,
            message=f'Found {len(projects)} projects',
            data={'projects': projects}
        ).dict())

    except Exception as e:
        return jsonify(ErrorResponse(
            error=str(e),
            error_type=e.__class__.__name__
        ).dict()), 500


@projects_bp.route('/', methods=['POST'])
def create_project():
    """创建新项目"""
    try:
        # 验证请求数据
        data = request.get_json()
        if not data:
            return jsonify(ErrorResponse(
                error='Request body is required'
            ).dict()), 400

        try:
            req = CreateProjectRequest(**data)
        except ValidationError as e:
            return jsonify(ErrorResponse(
                error='Invalid request data',
                details=e.errors()
            ).dict()), 400

        # 检查项目是否已存在
        workspace_path = os.environ.get('WORKSPACE_PATH', './workspace')
        project_path = os.path.join(workspace_path, 'projects', req.name)
        metadata_path = os.path.join(project_path, 'project_metadata.json')

        if os.path.exists(metadata_path):
            return jsonify(ErrorResponse(
                error=f'Project {req.name} already exists'
            ).dict()), 409

        # 创建项目适配器
        adapter = ProjectAdapter(req.name)

        # 创建项目
        result = adapter.create_project(
            raw_text=req.raw_text,
            settings=req.settings
        )

        if not result.get('success'):
            return jsonify(ErrorResponse(
                error=result.get('error', 'Failed to create project')
            ).dict()), 500

        # 获取项目信息
        project_info = adapter.get_project_info()

        return jsonify(StandardResponse(
            success=True,
            message='Project created successfully',
            data=project_info
        ).dict()), 201

    except Exception as e:
        return jsonify(ErrorResponse(
            error=str(e),
            error_type=e.__class__.__name__
        ).dict()), 500


@projects_bp.route('/<project_id>', methods=['GET'])
def get_project(project_id):
    """获取项目详情"""
    try:
        adapter = ProjectAdapter(project_id)
        project_info = adapter.get_project_info()

        if not project_info.get('exists'):
            return jsonify(ErrorResponse(
                error=f'Project {project_id} not found'
            ).dict()), 404

        return jsonify(StandardResponse(
            success=True,
            message='Project found',
            data=project_info
        ).dict())

    except Exception as e:
        return jsonify(ErrorResponse(
            error=str(e),
            error_type=e.__class__.__name__
        ).dict()), 500


@projects_bp.route('/<project_id>', methods=['PUT'])
def update_project(project_id):
    """更新项目"""
    try:
        data = request.get_json()
        if not data:
            return jsonify(ErrorResponse(
                error='Request body is required'
            ).dict()), 400

        adapter = ProjectAdapter(project_id)
        project_info = adapter.get_project_info()

        if not project_info.get('exists'):
            return jsonify(ErrorResponse(
                error=f'Project {project_id} not found'
            ).dict()), 404

        # 支持更新项目设置
        project_setting = data.get('project_setting')

        updated = False

        if project_setting is not None:
            # 更新项目设置
            result = adapter.update_settings(project_setting)
            if not result.get('success'):
                return jsonify(ErrorResponse(
                    error=result.get('error', 'Failed to update settings')
                ).dict()), 400
            updated = True

        if not updated:
            # 没有提供任何更新字段
            return jsonify(ErrorResponse(
                error='No update fields provided (supported: raw_text, project_setting)'
            ).dict()), 400

        return jsonify(StandardResponse(
            success=True,
            message='Project updated',
            data=adapter.get_project_info()
        ).dict())

    except Exception as e:
        return jsonify(ErrorResponse(
            error=str(e),
            error_type=e.__class__.__name__
        ).dict()), 500


@projects_bp.route('/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """删除项目"""
    try:
        adapter = ProjectAdapter(project_id)
        project_info = adapter.get_project_info()

        if not project_info.get('exists'):
            return jsonify(ErrorResponse(
                error=f'Project {project_id} not found'
            ).dict()), 404

        # TODO: 实现删除项目目录
        import shutil
        workspace_path = os.environ.get('WORKSPACE_PATH', './workspace')
        project_path = os.path.join(workspace_path, 'projects', project_id)

        if os.path.exists(project_path):
            shutil.rmtree(project_path)

        return jsonify(StandardResponse(
            success=True,
            message='Project deleted successfully'
        ).dict())

    except Exception as e:
        return jsonify(ErrorResponse(
            error=str(e),
            error_type=e.__class__.__name__
        ).dict()), 500