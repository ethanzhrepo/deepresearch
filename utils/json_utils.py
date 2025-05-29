"""
JSON utilities for DeepResearch system.
Handles validation and parsing of research outline structures.
"""

import json
import re
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, validator

from .logger import get_logger

logger = get_logger(__name__)


class SubSection(BaseModel):
    """Model for research subsection."""
    title: str = Field(..., description="Subsection title")
    description: Optional[str] = Field(None, description="Brief description of subsection content")
    keywords: List[str] = Field(default_factory=list, description="Key terms for research")
    estimated_length: int = Field(default=500, description="Estimated word count")


class Section(BaseModel):
    """Model for research section."""
    title: str = Field(..., description="Section title")
    description: Optional[str] = Field(None, description="Brief description of section content")
    subsections: List[SubSection] = Field(default_factory=list, description="List of subsections")
    keywords: List[str] = Field(default_factory=list, description="Key terms for research")
    estimated_length: int = Field(default=1000, description="Estimated word count")


class ResearchOutline(BaseModel):
    """Model for complete research outline structure."""
    title: str = Field(..., description="Research topic title")
    abstract: Optional[str] = Field(None, description="Research abstract/summary")
    sections: List[Section] = Field(..., description="List of main sections")
    keywords: List[str] = Field(default_factory=list, description="Overall research keywords")
    estimated_total_length: int = Field(default=5000, description="Total estimated word count")
    language: str = Field(default="zh-CN", description="Research language")
    
    @validator('sections')
    def validate_sections(cls, v):
        """Validate that there are sections defined."""
        if not v:
            raise ValueError("Research outline must have at least one section")
        return v
    
    @validator('title')
    def validate_title(cls, v):
        """Validate title is not empty."""
        if not v.strip():
            raise ValueError("Research title cannot be empty")
        return v.strip()


def parse_json_safely(json_str: str) -> Optional[Dict[str, Any]]:
    """
    Safely parse JSON string with error handling.
    
    Args:
        json_str: JSON string to parse
    
    Returns:
        Parsed dictionary or None if parsing fails
    """
    try:
        # Clean up common JSON formatting issues
        cleaned = clean_json_string(json_str)
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing failed: {e}")
        logger.debug(f"Failed JSON string: {json_str[:500]}...")
        return None
    except Exception as e:
        logger.error(f"Unexpected error parsing JSON: {e}")
        return None


def clean_json_string(json_str: str) -> str:
    """
    Clean up common JSON formatting issues.
    
    Args:
        json_str: Raw JSON string
    
    Returns:
        Cleaned JSON string
    """
    # Remove markdown code blocks
    json_str = re.sub(r'```json\s*', '', json_str)
    json_str = re.sub(r'```\s*$', '', json_str)
    
    # Remove leading/trailing whitespace
    json_str = json_str.strip()
    
    # Fix common quote issues
    json_str = re.sub(r'([{,]\s*)(\w+)(\s*:)', r'\1"\2"\3', json_str)
    
    return json_str


def validate_outline_structure(data: Dict[str, Any]) -> Optional[ResearchOutline]:
    """
    Validate research outline structure against schema.
    
    Args:
        data: Dictionary containing outline data
    
    Returns:
        Validated ResearchOutline object or None if validation fails
    """
    try:
        outline = ResearchOutline(**data)
        logger.info(f"Successfully validated outline: {outline.title}")
        return outline
    except Exception as e:
        logger.error(f"Outline validation failed: {e}")
        logger.debug(f"Invalid data: {data}")
        return None


def extract_outline_from_text(text: str) -> Optional[ResearchOutline]:
    """
    Extract and validate research outline from text response.
    
    Args:
        text: Text containing JSON outline
    
    Returns:
        Validated ResearchOutline or None if extraction fails
    """
    # Try to find JSON in the text
    json_patterns = [
        r'```json\s*(\{.*?\})\s*```',
        r'```\s*(\{.*?\})\s*```',
        r'(\{.*?\})',
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            data = parse_json_safely(match)
            if data:
                outline = validate_outline_structure(data)
                if outline:
                    return outline
    
    logger.warning("Could not extract valid outline from text")
    return None


def outline_to_dict(outline: ResearchOutline) -> Dict[str, Any]:
    """
    Convert ResearchOutline to dictionary.
    
    Args:
        outline: ResearchOutline object
    
    Returns:
        Dictionary representation
    """
    return outline.dict()


def create_sample_outline(topic: str) -> ResearchOutline:
    """
    Create a sample research outline for testing.
    
    Args:
        topic: Research topic
    
    Returns:
        Sample ResearchOutline
    """
    return ResearchOutline(
        title=f"{topic} 深度研究报告",
        abstract=f"本报告对 {topic} 进行全面深入的研究分析。",
        sections=[
            Section(
                title="概述与背景",
                description="介绍研究主题的基本概念和背景信息",
                subsections=[
                    SubSection(
                        title="定义与概念",
                        description="核心概念的定义和解释",
                        keywords=["定义", "概念", "基础"]
                    ),
                    SubSection(
                        title="历史发展",
                        description="发展历程和重要里程碑",
                        keywords=["历史", "发展", "演进"]
                    )
                ],
                keywords=["背景", "概述", "基础知识"]
            ),
            Section(
                title="现状分析",
                description="当前发展状况和趋势分析",
                subsections=[
                    SubSection(
                        title="市场现状",
                        description="当前市场规模和竞争格局",
                        keywords=["市场", "现状", "规模"]
                    ),
                    SubSection(
                        title="技术发展",
                        description="最新技术进展和创新",
                        keywords=["技术", "创新", "进展"]
                    )
                ],
                keywords=["现状", "分析", "趋势"]
            ),
            Section(
                title="未来展望",
                description="发展趋势预测和建议",
                subsections=[
                    SubSection(
                        title="发展趋势",
                        description="未来发展方向和趋势预测",
                        keywords=["趋势", "预测", "未来"]
                    ),
                    SubSection(
                        title="建议与结论",
                        description="研究结论和发展建议",
                        keywords=["建议", "结论", "总结"]
                    )
                ],
                keywords=["未来", "展望", "建议"]
            )
        ],
        keywords=[topic, "研究", "分析", "报告"],
        language="zh-CN"
    ) 