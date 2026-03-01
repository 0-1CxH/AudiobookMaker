from flask import Blueprint, request, jsonify, send_file
import os
import sys
import time
from tqdm import tqdm

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '..', 'src'))

from app.core.project_adapter import ProjectAdapter
from app.models.response import StandardResponse, ErrorResponse

audio_bp = Blueprint('audio', __name__)

# 简单的任务状态存储（生产环境应使用Redis或数据库）
task_status_store = {}


@audio_bp.route('/generate', methods=['POST'])
def generate_audio(project_id):
    """开始生成音频"""
    try:
        adapter = ProjectAdapter(project_id)
        project_info = adapter.get_project_info()

        if not project_info.get('exists'):
            return jsonify(ErrorResponse(
                error=f'Project {project_id} not found'
            ).dict()), 404

        # 生成任务ID
        task_id = f'audio_gen_{project_id}_{int(time.time())}'

        # 存储任务状态
        task_status_store[task_id] = {
            'task_id': task_id,
            'project_id': project_id,
            'status': 'pending',
            'progress': 0,
            'started_at': time.time(),
            'updated_at': time.time(),
            'message': 'Task created, waiting to start'
        }

        # 异步执行音频生成（这里简化处理，实际应使用Celery等）
        def generate_audio_task():
            try:
                task_status_store[task_id]['status'] = 'running'
                task_status_store[task_id]['message'] = 'Starting audio generation'
                task_status_store[task_id]['updated_at'] = time.time()

                # 获取未生成的片段列表
                result = adapter.generate_audio()
                if not result.get('success'):
                    task_status_store[task_id]['status'] = 'failed'
                    task_status_store[task_id]['message'] = result.get('error', 'Failed to get segment list')
                    task_status_store[task_id]['error'] = result.get('error')
                    task_status_store[task_id]['updated_at'] = time.time()
                    task_status_store[task_id]['completed_at'] = time.time()
                    return

                not_generated = result.get('not_generated', [])
                total = len(not_generated)
                task_status_store[task_id]['total_segments'] = total
                task_status_store[task_id]['processed_segments'] = 0
                task_status_store[task_id]['failed_segments'] = []

                # 逐个生成未生成的片段
                for i, seg_index in enumerate(tqdm(not_generated, desc='Generating audio segments')):
                    # 检查任务是否被取消
                    if task_status_store.get(task_id, {}).get('status') == 'cancelled':
                        task_status_store[task_id]['message'] = 'Task cancelled by user'
                        task_status_store[task_id]['updated_at'] = time.time()
                        task_status_store[task_id]['completed_at'] = time.time()
                        return

                    # 更新状态
                    task_status_store[task_id]['message'] = f'Generating segment {seg_index} (current task progress: {i+1}/{total})'
                    task_status_store[task_id]['progress'] = adapter.get_percentage_generated()
                    task_status_store[task_id]['current_task_progress'] = int((i / total) * 100) if total > 0 else 0
                    task_status_store[task_id]['current_segment'] = seg_index
                    task_status_store[task_id]['updated_at'] = time.time()

                    # 调用 regenerate_segment
                    seg_result = adapter.regenerate_segment(seg_index)
                    if not seg_result.get('success'):
                        # 记录失败，但继续生成其他片段
                        task_status_store[task_id]['failed_segments'].append({
                            'index': seg_index,
                            'error': seg_result.get('error')
                        })
                    else:
                        task_status_store[task_id]['processed_segments'] += 1

                    # 更新进度
                    task_status_store[task_id]['progress'] = adapter.get_percentage_generated()
                    task_status_store[task_id]['current_task_progress'] = int((i / total) * 100) if total > 0 else 0
                    task_status_store[task_id]['updated_at'] = time.time()

                # 所有片段处理完成
                failed_count = len(task_status_store[task_id]['failed_segments'])
                if failed_count == 0:
                    task_status_store[task_id]['status'] = 'completed'
                    task_status_store[task_id]['message'] = f'Successfully generated {total} audio segments'
                else:
                    task_status_store[task_id]['status'] = 'completed'
                    task_status_store[task_id]['message'] = f'Generated {total - failed_count} segments, {failed_count} failed'

                task_status_store[task_id]['progress'] = 100
                task_status_store[task_id]['updated_at'] = time.time()
                task_status_store[task_id]['completed_at'] = time.time()

            except Exception as e:
                task_status_store[task_id]['status'] = 'failed'
                task_status_store[task_id]['message'] = f'Task failed: {str(e)}'
                task_status_store[task_id]['error'] = str(e)
                task_status_store[task_id]['updated_at'] = time.time()
                task_status_store[task_id]['completed_at'] = time.time()

        # 在实际应用中，这里应该启动异步任务
        # 为了简化，我们直接执行（在后台线程中）
        import threading
        thread = threading.Thread(target=generate_audio_task)
        thread.daemon = True
        thread.start()

        return jsonify(StandardResponse(
            success=True,
            message='Audio generation started',
            data={
                'task_id': task_id,
                'status_url': f'/api/projects/{project_id}/audio/status/{task_id}'
            }
        ).dict()), 202

    except Exception as e:
        return jsonify(ErrorResponse(
            error=str(e),
            error_type=e.__class__.__name__
        ).dict()), 500


@audio_bp.route('/status/<task_id>', methods=['GET'])
def get_generation_status(project_id, task_id):
    """获取生成状态"""
    try:
        if task_id not in task_status_store:
            return jsonify(ErrorResponse(
                error=f'Task {task_id} not found'
            ).dict()), 404

        task_status = task_status_store[task_id]

        # 如果任务已完成一段时间，可以清理
        if task_status['status'] in ['completed', 'failed', 'cancelled']:
            completed_time = task_status.get('completed_at', 0)
            if time.time() - completed_time > 3600:  # 1小时后清理
                del task_status_store[task_id]

        return jsonify(StandardResponse(
            success=True,
            message='Task status retrieved',
            data=task_status
        ).dict())

    except Exception as e:
        return jsonify(ErrorResponse(
            error=str(e),
            error_type=e.__class__.__name__
        ).dict()), 500


@audio_bp.route('/segments', methods=['GET'])
def get_audio_segments(project_id):
    """获取音频片段列表"""
    try:
        adapter = ProjectAdapter(project_id)
        project_info = adapter.get_project_info()

        if not project_info.get('exists'):
            return jsonify(ErrorResponse(
                error=f'Project {project_id} not found'
            ).dict()), 404

        segments = adapter.get_text_segments()

        # 添加音频文件信息
        for segment in segments:
            if segment['has_audio']:
                # TODO: 获取音频文件详细信息
                segment['audio_duration'] = 0  # 占位符
                segment['audio_size'] = 0  # 占位符

        return jsonify(StandardResponse(
            success=True,
            message=f'Found {len(segments)} segments',
            data={'segments': segments}
        ).dict())

    except Exception as e:
        return jsonify(ErrorResponse(
            error=str(e),
            error_type=e.__class__.__name__
        ).dict()), 500


@audio_bp.route('/segments/<int:segment_index>/regenerate', methods=['POST'])
def regenerate_segment(project_id, segment_index):
    """重新生成单个音频片段"""
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

        # 调用适配器重新生成片段
        result = adapter.regenerate_segment(segment_index)

        if not result.get('success'):
            return jsonify(ErrorResponse(
                error=result.get('error', f'Failed to regenerate segment {segment_index}')
            ).dict()), 500

        return jsonify(StandardResponse(
            success=True,
            message=result.get('message', f'Segment {segment_index} regenerated successfully'),
            data=result
        ).dict())

    except Exception as e:
        return jsonify(ErrorResponse(
            error=str(e),
            error_type=e.__class__.__name__
        ).dict()), 500


@audio_bp.route('/segments/<int:segment_index>/audio', methods=['GET'])
def get_segment_audio(project_id, segment_index):
    """获取片段音频文件"""
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

        segment = segments[segment_index]
        if not segment.get('has_audio'):
            return jsonify(ErrorResponse(
                error=f'Segment {segment_index} has no audio generated'
            ).dict()), 404

        # 获取音频文件路径 - 从project_adapter获取或根据项目结构推断
        workspace_path = os.environ.get('WORKSPACE_PATH', './workspace')

        # 尝试voice_artifacts目录（这是Project类实际存储音频的地方）
        voice_artifacts_path = os.path.join(
            workspace_path,
            'projects',
            project_id,
            'voice_artifacts',
            f'segment_{segment_index}.wav'
        )
        # 检查文件存在
        if os.path.exists(voice_artifacts_path):
            audio_file_path = voice_artifacts_path
        else:
            return jsonify(ErrorResponse(
                error=f'Audio file not found for segment {segment_index}'
            ).dict()), 404

        # 发送音频文件
        return send_file(
            os.path.abspath(audio_file_path),
            as_attachment=False,
            download_name=f'segment_{segment_index}_audio.wav',
            mimetype='audio/wav'
        )

    except Exception as e:
        return jsonify(ErrorResponse(
            error=str(e),
            error_type=e.__class__.__name__
        ).dict()), 500


@audio_bp.route('/progress', methods=['GET'])
def get_generation_progress(project_id):
    """获取音频生成进度"""
    try:
        adapter = ProjectAdapter(project_id)
        project_info = adapter.get_project_info()

        if not project_info.get('exists'):
            return jsonify(ErrorResponse(
                error=f'Project {project_id} not found'
            ).dict()), 404

        segments = adapter.get_text_segments()
        generated_count = sum(1 for s in segments if s['has_audio'])
        total_count = len(segments)

        return jsonify(StandardResponse(
            success=True,
            message=f'Progress: {generated_count}/{total_count} segments generated',
            data={
                'generated_count': generated_count,
                'total_count': total_count,
                'progress_percentage': (generated_count / total_count * 100) if total_count > 0 else 0
            }
        ).dict())

    except Exception as e:
        return jsonify(ErrorResponse(
            error=str(e),
            error_type=e.__class__.__name__
        ).dict()), 500


@audio_bp.route('/cancel/<task_id>', methods=['POST'])
def cancel_generation(project_id, task_id):
    """取消音频生成任务"""
    try:
        if task_id not in task_status_store:
            return jsonify(ErrorResponse(
                error=f'Task {task_id} not found'
            ).dict()), 404

        task_status = task_status_store[task_id]

        # 验证任务属于当前项目
        if task_status.get('project_id') != project_id:
            return jsonify(ErrorResponse(
                error=f'Task {task_id} does not belong to project {project_id}'
            ).dict()), 403

        # 只有运行中或等待中的任务可以取消
        if task_status['status'] not in ['pending', 'running']:
            return jsonify(ErrorResponse(
                error=f'Task {task_id} cannot be cancelled (current status: {task_status["status"]})'
            ).dict()), 400

        # 更新任务状态为取消
        task_status_store[task_id]['status'] = 'cancelled'
        task_status_store[task_id]['message'] = 'Task cancelled by user'
        task_status_store[task_id]['updated_at'] = time.time()
        task_status_store[task_id]['completed_at'] = time.time()

        return jsonify(StandardResponse(
            success=True,
            message=f'Task {task_id} cancelled successfully',
            data={'task_id': task_id, 'status': 'cancelled'}
        ).dict())

    except Exception as e:
        return jsonify(ErrorResponse(
            error=str(e),
            error_type=e.__class__.__name__
        ).dict()), 500