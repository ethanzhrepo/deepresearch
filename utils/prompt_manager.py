"""
Prompt management system for DeepResearch.
Provides centralized prompt template management with versioning and localization.
"""

import os
import json
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import warnings

from utils.logger import LoggerMixin


class PromptType(Enum):
    """Types of prompts."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TEMPLATE = "template"


@dataclass
class PromptTemplate:
    """Prompt template with metadata."""
    id: str
    name: str
    description: str
    type: PromptType
    template: str
    variables: List[str]
    language: str = "zh-CN"
    version: str = "1.0"
    tags: List[str] = None
    metadata: Dict[str, Any] = None


class PromptManager(LoggerMixin):
    """
    Centralized prompt template manager.
    Handles loading, caching, and rendering of prompt templates.
    """
    
    def __init__(self, prompts_dir: str = "prompts"):
        """
        Initialize prompt manager.
        
        Args:
            prompts_dir: Directory containing prompt templates
        """
        self.prompts_dir = Path(prompts_dir)
        self.prompts_dir.mkdir(exist_ok=True)
        
        self.templates: Dict[str, PromptTemplate] = {}
        self.cache: Dict[str, str] = {}
        
        self._load_templates()
    
    def _load_templates(self):
        """Load all prompt templates from files."""
        try:
            # Load from YAML files
            for yaml_file in self.prompts_dir.glob("*.yml"):
                self._load_yaml_templates(yaml_file)
            
            for yaml_file in self.prompts_dir.glob("*.yaml"):
                self._load_yaml_templates(yaml_file)
            
            # Load from JSON files
            for json_file in self.prompts_dir.glob("*.json"):
                self._load_json_templates(json_file)
            
            self.log_info(f"Loaded {len(self.templates)} prompt templates")
            
        except Exception as e:
            self.log_error(f"Failed to load prompt templates: {e}")
    
    def _load_yaml_templates(self, file_path: Path):
        """Load templates from YAML file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if isinstance(data, dict) and 'templates' in data:
                for template_data in data['templates']:
                    template = self._create_template_from_dict(template_data)
                    self.templates[template.id] = template
            
        except Exception as e:
            self.log_error(f"Failed to load YAML templates from {file_path}: {e}")
    
    def _load_json_templates(self, file_path: Path):
        """Load templates from JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, dict) and 'templates' in data:
                for template_data in data['templates']:
                    template = self._create_template_from_dict(template_data)
                    self.templates[template.id] = template
            
        except Exception as e:
            self.log_error(f"Failed to load JSON templates from {file_path}: {e}")
    
    def _create_template_from_dict(self, data: Dict[str, Any]) -> PromptTemplate:
        """Create PromptTemplate from dictionary data."""
        return PromptTemplate(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            type=PromptType(data.get('type', 'template')),
            template=data['template'],
            variables=data.get('variables', []),
            language=data.get('language', 'zh-CN'),
            version=data.get('version', '1.0'),
            tags=data.get('tags', []),
            metadata=data.get('metadata', {})
        )
    
    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """
        Get prompt template by ID.
        
        Args:
            template_id: Template identifier
        
        Returns:
            PromptTemplate or None if not found
        """
        return self.templates.get(template_id)
    
    def render_template(
        self,
        template_id: str,
        variables: Optional[Dict[str, Any]] = None,
        language: Optional[str] = None
    ) -> Optional[str]:
        """
        Render prompt template with variables.
        
        Args:
            template_id: Template identifier
            variables: Variables to substitute
            language: Target language (optional)
        
        Returns:
            Rendered prompt string or None if template not found
        """
        template = self.get_template(template_id)
        if not template:
            self.log_warning(f"Template not found: {template_id}")
            return None
        
        variables = variables or {}
        
        # Check for language-specific template
        if language and language != template.language:
            lang_template_id = f"{template_id}_{language}"
            lang_template = self.get_template(lang_template_id)
            if lang_template:
                template = lang_template
        
        try:
            # Use string formatting for variable substitution
            rendered = template.template.format(**variables)
            
            # Cache the rendered result
            cache_key = f"{template_id}_{hash(str(variables))}"
            self.cache[cache_key] = rendered
            
            return rendered
            
        except KeyError as e:
            self.log_error(f"Missing variable {e} for template {template_id}")
            return None
        except Exception as e:
            self.log_error(f"Failed to render template {template_id}: {e}")
            return None
    
    def list_templates(
        self,
        template_type: Optional[PromptType] = None,
        language: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[PromptTemplate]:
        """
        List templates with optional filtering.
        
        Args:
            template_type: Filter by template type
            language: Filter by language
            tags: Filter by tags
        
        Returns:
            List of matching templates
        """
        templates = list(self.templates.values())
        
        if template_type:
            templates = [t for t in templates if t.type == template_type]
        
        if language:
            templates = [t for t in templates if t.language == language]
        
        if tags:
            templates = [
                t for t in templates
                if t.tags and any(tag in t.tags for tag in tags)
            ]
        
        return templates
    
    def add_template(self, template: PromptTemplate) -> bool:
        """
        Add a new prompt template.
        
        Args:
            template: PromptTemplate to add
        
        Returns:
            True if added successfully
        """
        try:
            self.templates[template.id] = template
            self.log_info(f"Added template: {template.id}")
            return True
        except Exception as e:
            self.log_error(f"Failed to add template {template.id}: {e}")
            return False
    
    def save_template_to_file(
        self,
        template: PromptTemplate,
        file_path: Optional[Path] = None
    ) -> bool:
        """
        Save template to file.
        
        Args:
            template: PromptTemplate to save
            file_path: Target file path (optional)
        
        Returns:
            True if saved successfully
        """
        if not file_path:
            file_path = self.prompts_dir / f"{template.id}.yml"
        
        try:
            template_data = {
                'templates': [{
                    'id': template.id,
                    'name': template.name,
                    'description': template.description,
                    'type': template.type.value,
                    'template': template.template,
                    'variables': template.variables,
                    'language': template.language,
                    'version': template.version,
                    'tags': template.tags or [],
                    'metadata': template.metadata or {}
                }]
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(template_data, f, ensure_ascii=False, indent=2)
            
            self.log_info(f"Saved template {template.id} to {file_path}")
            return True
            
        except Exception as e:
            self.log_error(f"Failed to save template {template.id}: {e}")
            return False
    
    def create_default_templates(self):
        """Create default prompt templates."""
        default_templates = [
            # 研究提纲生成模板
            PromptTemplate(
                id="research_outline",
                name="研究提纲生成",
                description="生成研究主题的详细提纲",
                type=PromptType.SYSTEM,
                template="""你是一个专业的研究助手。请为给定的研究主题生成一个详细的研究提纲。

要求:
1. 提纲应该包含 {max_sections} 个主要章节
2. 每个章节应该有 2-3 个子章节
3. 提供每个章节的简要描述和关键词
4. 估算每个部分的字数
5. 使用 {language} 语言

请以JSON格式返回提纲，格式如下:
{{
    "title": "研究标题",
    "abstract": "研究摘要",
    "sections": [
        {{
            "title": "章节标题",
            "description": "章节描述",
            "keywords": ["关键词1", "关键词2"],
            "estimated_length": 1000,
            "subsections": [
                {{
                    "title": "子章节标题",
                    "description": "子章节描述",
                    "keywords": ["关键词"],
                    "estimated_length": 500
                }}
            ]
        }}
    ],
    "keywords": ["总体关键词"],
    "estimated_total_length": 5000,
    "language": "{language}"
}}""",
                variables=["max_sections", "language"],
                tags=["research", "outline", "generation"]
            ),
            
            # 内容生成模板
            PromptTemplate(
                id="content_generation",
                name="内容生成",
                description="为研究章节生成详细内容",
                type=PromptType.SYSTEM,
                template="""你是一个专业的研究写作助手。请为给定的研究章节生成详细的内容。

要求:
1. 内容应该专业、准确、有深度
2. 字数约 {estimated_length} 字
3. 使用 {language} 语言
4. 结构清晰，逻辑严密
5. 如果有参考资料，请合理引用

章节信息:
- 标题: {section_title}
- 描述: {section_description}
- 关键词: {keywords}""",
                variables=["estimated_length", "language", "section_title", "section_description", "keywords"],
                tags=["research", "content", "writing"]
            ),
            
            # 代码生成模板
            PromptTemplate(
                id="code_generation",
                name="代码生成",
                description="生成Python代码",
                type=PromptType.SYSTEM,
                template="""你是一个专业的Python程序员。请根据任务描述生成Python代码。

要求:
1. 代码应该简洁、高效、可读
2. 只使用标准库和允许的第三方库: {allowed_libraries}
3. 不要使用文件操作、网络请求等危险操作
4. 包含适当的注释
5. 确保代码可以直接执行

请只返回Python代码，不要包含其他解释。""",
                variables=["allowed_libraries"],
                tags=["code", "generation", "python"]
            ),
            
            # 数据分析模板
            PromptTemplate(
                id="data_analysis",
                name="数据分析",
                description="数据分析和可视化",
                type=PromptType.SYSTEM,
                template="""你是一个专业的数据分析师。请根据给定的数据进行分析。

分析要求:
1. 分析类型: {analysis_type}
2. 数据描述: {data_description}
3. 分析目标: {analysis_goals}
4. 输出格式: {output_format}

请提供:
1. 数据概览和基本统计
2. 关键发现和洞察
3. 可视化建议
4. 结论和建议""",
                variables=["analysis_type", "data_description", "analysis_goals", "output_format"],
                tags=["data", "analysis", "statistics"]
            ),
            
            # 搜索查询优化模板
            PromptTemplate(
                id="search_query_optimization",
                name="搜索查询优化",
                description="优化搜索查询以获得更好的结果",
                type=PromptType.SYSTEM,
                template="""你是一个搜索专家。请优化给定的搜索查询以获得更准确和相关的结果。

原始查询: {original_query}
搜索目标: {search_goal}
目标语言: {language}
搜索引擎: {search_engine}

请提供:
1. 优化后的查询词
2. 相关的同义词和变体
3. 可能的过滤条件
4. 搜索策略建议""",
                variables=["original_query", "search_goal", "language", "search_engine"],
                tags=["search", "optimization", "query"]
            )
        ]
        
        # 保存默认模板
        for template in default_templates:
            self.add_template(template)
            self.save_template_to_file(template)
        
        self.log_info(f"Created {len(default_templates)} default templates")
    
    def validate_template(self, template: PromptTemplate) -> List[str]:
        """
        Validate prompt template.
        
        Args:
            template: PromptTemplate to validate
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check required fields
        if not template.id:
            errors.append("Template ID is required")
        
        if not template.name:
            errors.append("Template name is required")
        
        if not template.template:
            errors.append("Template content is required")
        
        # Check for variable consistency
        import re
        template_vars = set(re.findall(r'\{(\w+)\}', template.template))
        declared_vars = set(template.variables)
        
        missing_vars = template_vars - declared_vars
        if missing_vars:
            errors.append(f"Undeclared variables: {missing_vars}")
        
        unused_vars = declared_vars - template_vars
        if unused_vars:
            errors.append(f"Unused variables: {unused_vars}")
        
        return errors
    
    def get_template_stats(self) -> Dict[str, Any]:
        """Get statistics about loaded templates."""
        stats = {
            "total_templates": len(self.templates),
            "by_type": {},
            "by_language": {},
            "by_tags": {},
            "cache_size": len(self.cache)
        }
        
        for template in self.templates.values():
            # Count by type
            type_name = template.type.value
            stats["by_type"][type_name] = stats["by_type"].get(type_name, 0) + 1
            
            # Count by language
            stats["by_language"][template.language] = stats["by_language"].get(template.language, 0) + 1
            
            # Count by tags
            if template.tags:
                for tag in template.tags:
                    stats["by_tags"][tag] = stats["by_tags"].get(tag, 0) + 1
        
        return stats


# Global prompt manager instance
# DEPRECATED: Use get_prompt_manager() from utils.service_container instead
def _get_deprecated_prompt_manager():
    """Internal function to handle deprecated global access."""
    warnings.warn(
        "Direct import of prompt_manager is deprecated. "
        "Use get_prompt_manager() from utils.service_container instead.",
        DeprecationWarning,
        stacklevel=3
    )
    from utils.service_container import get_prompt_manager
    return get_prompt_manager()

# 保持向后兼容性的全局实例
prompt_manager = _get_deprecated_prompt_manager() 