"""
Code execution tool with enhanced security and sandboxing.
Supports Docker containerization and advanced security checks.
"""

import os
import re
import sys
import ast
import json
import time
import docker
import tempfile
import subprocess
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from utils.logger import LoggerMixin
from config import config


class ExecutionEnvironment(Enum):
    """Code execution environments."""
    LOCAL = "local"
    DOCKER = "docker"
    SANDBOX = "sandbox"


@dataclass
class ExecutionResult:
    """Code execution result."""
    success: bool
    output: str
    error: str
    execution_time: float
    memory_usage: Optional[int] = None
    exit_code: int = 0
    warnings: List[str] = None


class SecurityAnalyzer:
    """Advanced security analyzer for Python code."""
    
    def __init__(self):
        # 危险操作模式
        self.dangerous_patterns = [
            # 系统调用
            r'os\.system\s*\(',
            r'subprocess\.',
            r'__import__\s*\(',
            r'eval\s*\(',
            r'exec\s*\(',
            r'compile\s*\(',
            
            # 文件操作
            r'open\s*\([^)]*["\'][wax]["\']',  # 写入模式
            r'\.write\s*\(',
            r'\.remove\s*\(',
            r'\.unlink\s*\(',
            r'shutil\.',
            
            # 网络操作
            r'socket\.',
            r'urllib\.',
            r'requests\.',
            r'http\.',
            
            # 反射和动态执行
            r'getattr\s*\(',
            r'setattr\s*\(',
            r'hasattr\s*\(',
            r'globals\s*\(',
            r'locals\s*\(',
            r'vars\s*\(',
            
            # 模块操作
            r'importlib\.',
            r'__loader__',
            r'__spec__',
        ]
        
        # 允许的模块白名单
        self.allowed_modules = set(config.system.code_execution.allowed_imports)
        
        # 禁止的操作
        self.forbidden_operations = set(config.system.code_execution.forbidden_operations)
    
    def analyze_code(self, code: str) -> Tuple[bool, List[str]]:
        """
        分析代码安全性。
        
        Returns:
            (is_safe, warnings)
        """
        warnings = []
        
        # 1. 模式匹配检查
        for pattern in self.dangerous_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                warnings.append(f"检测到危险操作模式: {pattern}")
        
        # 2. AST 分析
        try:
            tree = ast.parse(code)
            ast_warnings = self._analyze_ast(tree)
            warnings.extend(ast_warnings)
        except SyntaxError as e:
            warnings.append(f"语法错误: {e}")
            return False, warnings
        
        # 3. 导入检查
        import_warnings = self._check_imports(code)
        warnings.extend(import_warnings)
        
        # 判断是否安全
        is_safe = len(warnings) == 0
        
        return is_safe, warnings
    
    def _analyze_ast(self, tree: ast.AST) -> List[str]:
        """AST 安全分析。"""
        warnings = []
        
        for node in ast.walk(tree):
            # 检查函数调用
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    if func_name in self.forbidden_operations:
                        warnings.append(f"禁止的函数调用: {func_name}")
                
                elif isinstance(node.func, ast.Attribute):
                    attr_name = node.func.attr
                    if attr_name in ['system', 'popen', 'spawn']:
                        warnings.append(f"危险的方法调用: {attr_name}")
            
            # 检查导入语句
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name not in self.allowed_modules:
                        warnings.append(f"未授权的模块导入: {alias.name}")
            
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module not in self.allowed_modules:
                    warnings.append(f"未授权的模块导入: {node.module}")
        
        return warnings
    
    def _check_imports(self, code: str) -> List[str]:
        """检查导入语句。"""
        warnings = []
        
        # 提取所有导入语句
        import_pattern = r'(?:^|\n)\s*(?:import|from)\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        imports = re.findall(import_pattern, code, re.MULTILINE)
        
        for module in imports:
            if module not in self.allowed_modules:
                warnings.append(f"未授权的模块: {module}")
        
        return warnings


class DockerSandbox:
    """Docker 容器沙箱。"""
    
    def __init__(self):
        self.client = None
        self.container_image = "python:3.11-slim"
        self.container_name = "deepresearch-sandbox"
        
    def _ensure_docker_client(self):
        """确保 Docker 客户端连接。"""
        if self.client is None:
            try:
                self.client = docker.from_env()
                # 测试连接
                self.client.ping()
            except Exception as e:
                raise RuntimeError(f"无法连接到 Docker: {e}")
    
    def execute_code(self, code: str, timeout: int = 60) -> ExecutionResult:
        """在 Docker 容器中执行代码。"""
        self._ensure_docker_client()
        
        start_time = time.time()
        
        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # 容器配置
            container_config = {
                'image': self.container_image,
                'command': f'python /code/{os.path.basename(temp_file)}',
                'volumes': {
                    os.path.dirname(temp_file): {'bind': '/code', 'mode': 'ro'}
                },
                'mem_limit': config.system.code_execution.get('memory_limit', '512m'),
                'cpu_quota': int(config.system.code_execution.get('cpu_limit', 0.5) * 100000),
                'network_disabled': True,
                'remove': True,
                'stdout': True,
                'stderr': True,
            }
            
            # 运行容器
            container = self.client.containers.run(**container_config)
            
            # 获取输出
            output = container.decode('utf-8')
            error = ""
            exit_code = 0
            
        except docker.errors.ContainerError as e:
            output = e.container.logs().decode('utf-8')
            error = f"容器执行错误: {e}"
            exit_code = e.exit_status
            
        except Exception as e:
            output = ""
            error = f"Docker 执行失败: {e}"
            exit_code = 1
            
        finally:
            # 清理临时文件
            if 'temp_file' in locals():
                try:
                    os.unlink(temp_file)
                except:
                    pass
        
        execution_time = time.time() - start_time
        
        return ExecutionResult(
            success=exit_code == 0,
            output=output,
            error=error,
            execution_time=execution_time,
            exit_code=exit_code
        )


class LocalSandbox:
    """本地受限环境沙箱。"""
    
    def __init__(self):
        self.restricted_builtins = {
            '__import__': None,
            'eval': None,
            'exec': None,
            'compile': None,
            'open': self._safe_open,
            'input': None,
            'raw_input': None,
        }
    
    def _safe_open(self, *args, **kwargs):
        """安全的文件打开函数。"""
        if len(args) > 1 and args[1] in ['w', 'a', 'x']:
            raise PermissionError("写入操作被禁止")
        return open(*args, **kwargs)
    
    def execute_code(self, code: str, timeout: int = 60) -> ExecutionResult:
        """在受限环境中执行代码。"""
        start_time = time.time()
        
        # 创建受限的全局环境
        restricted_globals = {
            '__builtins__': self.restricted_builtins,
            '__name__': '__main__',
        }
        
        # 添加允许的模块
        for module_name in config.system.code_execution.allowed_imports:
            try:
                module = __import__(module_name)
                restricted_globals[module_name] = module
            except ImportError:
                pass
        
        # 捕获输出
        import io
        import contextlib
        
        output_buffer = io.StringIO()
        error_buffer = io.StringIO()
        
        try:
            with contextlib.redirect_stdout(output_buffer), \
                 contextlib.redirect_stderr(error_buffer):
                
                # 使用 exec 执行代码
                exec(code, restricted_globals)
            
            output = output_buffer.getvalue()
            error = error_buffer.getvalue()
            success = True
            exit_code = 0
            
        except Exception as e:
            output = output_buffer.getvalue()
            error = f"{error_buffer.getvalue()}\n{type(e).__name__}: {e}"
            success = False
            exit_code = 1
        
        execution_time = time.time() - start_time
        
        return ExecutionResult(
            success=success,
            output=output,
            error=error,
            execution_time=execution_time,
            exit_code=exit_code
        )


class CodeRunner(LoggerMixin):
    """Enhanced code runner with security and sandboxing."""
    
    def __init__(self):
        """Initialize code runner."""
        self.security_analyzer = SecurityAnalyzer()
        self.environment = ExecutionEnvironment(config.tools.code_tool.execution_environment)
        
        # 初始化沙箱
        if self.environment == ExecutionEnvironment.DOCKER:
            self.sandbox = DockerSandbox()
        else:
            self.sandbox = LocalSandbox()
        
        self.timeout = config.system.code_execution.timeout
        self.max_output_length = config.system.code_execution.max_output_length
    
    def execute_code(self, code: str, language: str = "python") -> ExecutionResult:
        """
        Execute code with security checks and sandboxing.
        
        Args:
            code: Code to execute
            language: Programming language (currently only Python supported)
        
        Returns:
            ExecutionResult with output and metadata
        """
        if language.lower() != "python":
            return ExecutionResult(
                success=False,
                output="",
                error=f"不支持的编程语言: {language}",
                execution_time=0.0,
                exit_code=1
            )
        
        self.log_info(f"执行代码 ({self.environment.value} 环境)")
        
        # 1. 安全性检查
        is_safe, warnings = self.security_analyzer.analyze_code(code)
        
        if not is_safe:
            self.log_warning(f"代码安全检查失败: {warnings}")
            return ExecutionResult(
                success=False,
                output="",
                error=f"代码安全检查失败: {'; '.join(warnings)}",
                execution_time=0.0,
                exit_code=1,
                warnings=warnings
            )
        
        # 2. 长度检查
        if len(code) > 10000:  # 10KB 限制
            return ExecutionResult(
                success=False,
                output="",
                error="代码长度超过限制 (10KB)",
                execution_time=0.0,
                exit_code=1
            )
        
        # 3. 执行代码
        try:
            result = self.sandbox.execute_code(code, self.timeout)
            
            # 4. 输出长度限制
            if len(result.output) > self.max_output_length:
                result.output = result.output[:self.max_output_length] + "\n... (输出被截断)"
            
            if len(result.error) > self.max_output_length:
                result.error = result.error[:self.max_output_length] + "\n... (错误信息被截断)"
            
            # 5. 记录执行结果
            if result.success:
                self.log_info(f"代码执行成功 (耗时: {result.execution_time:.2f}s)")
            else:
                self.log_warning(f"代码执行失败: {result.error}")
            
            return result
            
        except Exception as e:
            self.log_error(f"代码执行异常: {e}")
            return ExecutionResult(
                success=False,
                output="",
                error=f"执行异常: {e}",
                execution_time=0.0,
                exit_code=1
            )
    
    def validate_environment(self) -> bool:
        """验证执行环境是否可用。"""
        try:
            if self.environment == ExecutionEnvironment.DOCKER:
                self.sandbox._ensure_docker_client()
                self.log_info("Docker 环境验证成功")
            else:
                self.log_info("本地沙箱环境验证成功")
            return True
        except Exception as e:
            self.log_error(f"环境验证失败: {e}")
            return False
    
    def get_environment_info(self) -> Dict[str, Any]:
        """获取执行环境信息。"""
        info = {
            "environment": self.environment.value,
            "timeout": self.timeout,
            "max_output_length": self.max_output_length,
            "allowed_modules": list(self.security_analyzer.allowed_modules),
            "security_enabled": True,
        }
        
        if self.environment == ExecutionEnvironment.DOCKER:
            try:
                self.sandbox._ensure_docker_client()
                info["docker_available"] = True
                info["docker_image"] = self.sandbox.container_image
            except:
                info["docker_available"] = False
        
        return info 