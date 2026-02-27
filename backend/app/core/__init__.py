"""核心适配器模块，包装现有项目代码"""

from .project_adapter import ProjectAdapter, format_error_response

__all__ = ['ProjectAdapter', 'format_error_response']