"""
Configuration module for DeepResearch system.
Handles configuration loading from YAML file and environment variables.
"""

import os
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class LLMProviderConfig(BaseModel):
    """Configuration for a specific LLM provider."""
    model: str
    temperature: float = 0.7
    max_tokens: int = 4000
    timeout: int = 60
    base_url: Optional[str] = None  # For Ollama


class TaskSpecificModelConfig(BaseModel):
    """Configuration for task-specific LLM models."""
    provider: str
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    stop: Optional[List[str]] = None


class LLMConfig(BaseModel):
    """LLM configurations."""
    default_provider: str = "openai"
    openai: LLMProviderConfig
    claude: LLMProviderConfig
    gemini: LLMProviderConfig
    ollama: LLMProviderConfig
    deepseek: LLMProviderConfig
    
    # Agent特定LLM配置
    agent_llms: Dict[str, str] = Field(default_factory=dict)
    
    # 任务特定LLM配置
    task_specific_models: Dict[str, TaskSpecificModelConfig] = Field(default_factory=dict)
    
    # API Keys from environment
    openai_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    anthropic_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY"))
    google_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("GOOGLE_API_KEY"))
    deepseek_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("DEEPSEEK_API_KEY"))


class SearchEngineConfig(BaseModel):
    """Search engine specific configuration."""
    enabled: bool = True
    region: Optional[str] = None
    safe_search: Optional[str] = None
    country: Optional[str] = None
    language: Optional[str] = None
    market: Optional[str] = None
    include_answer: Optional[bool] = None
    include_raw_content: Optional[bool] = None
    max_results: Optional[int] = None
    search_lang: Optional[str] = None
    ui_lang: Optional[str] = None
    sort_by: Optional[str] = None
    sort_order: Optional[str] = None


class SearchConfig(BaseModel):
    """Search configurations."""
    default_engine: str = "tavily"  # 默认使用 Tavily
    fallback_engines: List[str] = ["duckduckgo", "brave", "google", "bing"]
    max_results: int = 10
    timeout: int = 30
    engines: Dict[str, SearchEngineConfig] = {}
    
    # Google Docs 搜索配置
    enable_google_docs: bool = False
    
    # 权威网站搜索配置
    authority_sites: List[str] = []
    enable_authority_search: bool = False
    
    # Arxiv 学术搜索配置
    enable_arxiv_search: bool = True
    
    # API Keys from environment
    tavily_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("TAVILY_API_KEY"))
    brave_search_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("BRAVE_SEARCH_API_KEY"))
    serpapi_key: Optional[str] = Field(default_factory=lambda: os.getenv("SERPAPI_KEY"))
    bing_search_key: Optional[str] = Field(default_factory=lambda: os.getenv("BING_SEARCH_KEY"))


class GoogleDriveConfig(BaseModel):
    """Google Drive configuration."""
    credentials_file: str = "credentials.json"
    token_file: str = "token.json"
    scopes: List[str] = ["https://www.googleapis.com/auth/drive.readonly"]


class DropboxConfig(BaseModel):
    """Dropbox configuration."""
    timeout: int = 30
    
    # API Keys from environment
    app_key: Optional[str] = Field(default_factory=lambda: os.getenv("DROPBOX_APP_KEY"))
    app_secret: Optional[str] = Field(default_factory=lambda: os.getenv("DROPBOX_APP_SECRET"))
    access_token: Optional[str] = Field(default_factory=lambda: os.getenv("DROPBOX_ACCESS_TOKEN"))


class FileStorageConfig(BaseModel):
    """File storage configurations."""
    google_drive: GoogleDriveConfig
    dropbox: DropboxConfig


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = "INFO"
    file: str = "deepresearch.log"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    max_file_size: str = "10MB"
    backup_count: int = 5


class BrowserConfig(BaseModel):
    """Browser automation configuration."""
    headless: bool = True
    timeout: int = 30000
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    viewport: Dict[str, int] = {"width": 1920, "height": 1080}


class CodeExecutionConfig(BaseModel):
    """Code execution configuration."""
    timeout: int = 60
    max_output_length: int = 10000
    allowed_imports: List[str] = []
    forbidden_operations: List[str] = []


class OutlineConfig(BaseModel):
    """Outline generation configuration."""
    max_depth: int = 3
    max_sections: int = 8
    max_subsections_per_section: int = 5
    default_language: str = "zh-CN"
    research_depth: str = "comprehensive"


class TaskSplittingConfig(BaseModel):
    """Task splitting configuration."""
    max_tasks_per_section: int = 5
    max_tasks_per_subsection: int = 3
    include_verification_tasks: bool = True
    include_synthesis_tasks: bool = True
    task_granularity: str = "medium"


class WritingStyleConfig(BaseModel):
    """Writing style configuration."""
    tone: str = "academic"
    target_audience: str = "general"
    citation_style: str = "inline"
    include_examples: bool = True
    include_statistics: bool = True


class ContentLimitsConfig(BaseModel):
    """Content limits configuration."""
    max_length: int = 2000
    min_length: int = 300


class QualityControlConfig(BaseModel):
    """Quality control configuration."""
    include_sources: bool = True
    fact_check: bool = True
    use_templates: bool = True


class ContentWritingConfig(BaseModel):
    """Content writing configuration."""
    writing_style: WritingStyleConfig
    content_limits: ContentLimitsConfig
    quality_control: QualityControlConfig


class PlanningConfig(BaseModel):
    """Planning configuration."""
    default_strategy: str = "adaptive"
    max_parallel_tasks: int = 3
    enable_dynamic_replanning: bool = True
    resource_optimization: bool = True
    fallback_enabled: bool = True


class ResearchConfig(BaseModel):
    """Research configuration."""
    outline: OutlineConfig
    task_splitting: TaskSplittingConfig
    content_writing: ContentWritingConfig
    planning: PlanningConfig


class PerformanceConfig(BaseModel):
    """Performance configuration."""
    max_concurrent_requests: int = 5
    request_retry_count: int = 3
    request_retry_delay: int = 1
    cache_enabled: bool = True
    cache_ttl: int = 3600


class SecurityConfig(BaseModel):
    """Security configuration."""
    enable_sandbox: bool = True
    max_file_size: str = "50MB"
    allowed_file_types: List[str] = []
    rate_limiting: Dict[str, int] = {}


class SystemConfig(BaseModel):
    """System configurations."""
    output_dir: str = "output"
    temp_dir: str = "temp"
    logging: LoggingConfig
    browser: BrowserConfig
    code_execution: CodeExecutionConfig
    research: ResearchConfig
    performance: PerformanceConfig
    security: SecurityConfig


class ToolConfig(BaseModel):
    """Tool configuration."""
    enabled: bool = True
    execution_environment: str = "local"  # local, docker, sandbox
    enable_sandbox: bool = True
    timeout: int = 60
    max_memory: str = "512MB"


class BrowserUseToolConfig(BaseModel):
    """Browser-Use tool specific configuration."""
    enabled: bool = True
    llm_provider: str = "deepseek"
    llm_model: str = "deepseek-chat"
    browser: Dict[str, Any] = Field(default_factory=lambda: {
        "headless": True,
        "timeout": 300,
        "max_steps": 50,
        "save_screenshots": True,
        "extract_data": True
    })
    output_dir: str = "browser_outputs"
    features: Dict[str, bool] = Field(default_factory=lambda: {
        "search_and_extract": True,
        "navigate_and_extract": True,
        "fill_form": True,
        "monitor_changes": True,
        "automate_workflow": True,
        "custom_task": True
    })
    security: Dict[str, Any] = Field(default_factory=lambda: {
        "allowed_domains": [],
        "blocked_domains": ["malicious-site.com"],
        "max_execution_time": 600,
        "enable_content_filtering": True
    })


class ToolsConfig(BaseModel):
    """Tools configurations."""
    search_tool: ToolConfig = ToolConfig()
    code_tool: ToolConfig = ToolConfig()
    browser_tool: ToolConfig = ToolConfig()
    file_tool: ToolConfig = ToolConfig()
    browser_use_tool: BrowserUseToolConfig = BrowserUseToolConfig()


class CapabilityMappingConfig(BaseModel):
    """Capability mapping configuration."""
    tools: List[str]
    priority: int


class MCPExecutionConfig(BaseModel):
    """MCP execution configuration."""
    batch_size: int = 3
    timeout_per_batch: int = 300
    failure_threshold: float = 0.3


class MCPPerformanceTrackingConfig(BaseModel):
    """MCP performance tracking configuration."""
    enabled: bool = True
    track_execution_time: bool = True
    track_success_rate: bool = True
    track_resource_usage: bool = True


class MCPConfig(BaseModel):
    """MCP (Multi-Capability Planning) configuration."""
    capability_mapping: Dict[str, CapabilityMappingConfig] = {}
    execution: MCPExecutionConfig = MCPExecutionConfig()
    performance_tracking: MCPPerformanceTrackingConfig = MCPPerformanceTrackingConfig()


class MarkdownFormattingConfig(BaseModel):
    """Markdown formatting configuration."""
    heading_style: str = "atx"
    code_block_style: str = "fenced"
    emphasis_style: str = "asterisk"


class MarkdownTemplatesConfig(BaseModel):
    """Markdown templates configuration."""
    report_template: str = "default"
    section_template: str = "academic"


class MarkdownConfig(BaseModel):
    """Markdown output configuration."""
    include_toc: bool = True
    include_metadata: bool = True
    include_sources: bool = True
    include_timestamps: bool = True
    formatting: MarkdownFormattingConfig = MarkdownFormattingConfig()
    templates: MarkdownTemplatesConfig = MarkdownTemplatesConfig()


class FileNamingConfig(BaseModel):
    """File naming configuration."""
    pattern: str = "{topic}_{timestamp}"
    timestamp_format: str = "%Y%m%d_%H%M%S"
    max_filename_length: int = 100
    sanitize_filename: bool = True


class OutputConfig(BaseModel):
    """Output configuration."""
    markdown: MarkdownConfig = MarkdownConfig()
    file_naming: FileNamingConfig = FileNamingConfig()


class LanguageSettingsConfig(BaseModel):
    """Language specific settings."""
    date_format: str
    number_format: str


class I18nConfig(BaseModel):
    """Internationalization configuration."""
    default_language: str = "zh-CN"
    supported_languages: List[str] = ["zh-CN", "en-US", "ja-JP"]
    language_settings: Dict[str, LanguageSettingsConfig] = {}


class TestingConfig(BaseModel):
    """Testing configuration."""
    mock_api_calls: bool = False
    test_data_dir: str = "tests/data"


class DevToolsConfig(BaseModel):
    """Development tools configuration."""
    auto_reload: bool = False
    show_stack_traces: bool = True


class DevelopmentConfig(BaseModel):
    """Development configuration."""
    debug_mode: bool = False
    verbose_logging: bool = False
    enable_profiling: bool = False
    testing: TestingConfig = TestingConfig()
    dev_tools: DevToolsConfig = DevToolsConfig()


class Config:
    """Main configuration class that loads from YAML file."""
    
    def __init__(self, config_file: str = "config.yml"):
        """
        Initialize configuration from YAML file.
        
        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file
        self._load_config()
    
    def _load_config(self):
        """Load configuration from YAML file."""
        config_path = Path(self.config_file)
        
        if not config_path.exists():
            # Create default config if not exists
            self._create_default_config()
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            # Parse configuration sections using dedicated methods
            self.llm = self._parse_llm_config(config_data.get('llm', {}))
            self.search = self._parse_search_config(config_data.get('search', {}))
            self.file_storage = self._parse_file_storage_config(config_data.get('file_storage', {}))
            self.system = self._parse_system_config(config_data.get('system', {}))
            self.tools = self._parse_tools_config(config_data.get('tools', {}))
            self.mcp = self._parse_mcp_config(config_data.get('mcp', {}))
            self.output = self._parse_output_config(config_data.get('output', {}))
            self.i18n = self._parse_i18n_config(config_data.get('i18n', {}))
            self.development = self._parse_development_config(config_data.get('development', {}))
            
        except Exception as e:
            print(f"Error loading config file {config_path}: {e}")
            print("Using default configuration...")
            self._load_default_config()
    
    def _parse_llm_config(self, llm_data: Dict[str, Any]) -> LLMConfig:
        """Parse LLM configuration section."""
        # 解析任务特定模型配置
        task_specific_models = {}
        for task_name, task_config in llm_data.get('task_specific_models', {}).items():
            task_specific_models[task_name] = TaskSpecificModelConfig(**task_config)
        
        return LLMConfig(
            default_provider=llm_data.get('default_provider', 'openai'),
            openai=LLMProviderConfig(**llm_data.get('openai', {})),
            claude=LLMProviderConfig(**llm_data.get('claude', {})),
            gemini=LLMProviderConfig(**llm_data.get('gemini', {})),
            ollama=LLMProviderConfig(**llm_data.get('ollama', {})),
            deepseek=LLMProviderConfig(**llm_data.get('deepseek', {})),
            agent_llms=llm_data.get('agent_llms', {}),
            task_specific_models=task_specific_models
        )
    
    def _parse_search_config(self, search_data: Dict[str, Any]) -> SearchConfig:
        """Parse search configuration section."""
        return SearchConfig(
            default_engine=search_data.get('default_engine', 'duckduckgo'),
            fallback_engines=search_data.get('fallback_engines', ['google', 'bing']),
            max_results=search_data.get('max_results', 10),
            timeout=search_data.get('timeout', 30),
            engines={
                name: SearchEngineConfig(**engine_config) 
                for name, engine_config in search_data.get('engines', {}).items()
            },
            enable_google_docs=search_data.get('enable_google_docs', False),
            authority_sites=search_data.get('authority_sites', []),
            enable_authority_search=search_data.get('enable_authority_search', False)
        )
    
    def _parse_file_storage_config(self, file_storage_data: Dict[str, Any]) -> FileStorageConfig:
        """Parse file storage configuration section."""
        return FileStorageConfig(
            google_drive=GoogleDriveConfig(**file_storage_data.get('google_drive', {})),
            dropbox=DropboxConfig(**file_storage_data.get('dropbox', {}))
        )
    
    def _parse_system_config(self, system_data: Dict[str, Any]) -> SystemConfig:
        """Parse system configuration section."""
        return SystemConfig(
            output_dir=system_data.get('output_dir', 'output'),
            temp_dir=system_data.get('temp_dir', 'temp'),
            logging=LoggingConfig(**system_data.get('logging', {})),
            browser=BrowserConfig(**system_data.get('browser', {})),
            code_execution=CodeExecutionConfig(**system_data.get('code_execution', {})),
            research=self._parse_research_config(system_data.get('research', {})),
            performance=PerformanceConfig(**system_data.get('performance', {})),
            security=SecurityConfig(**system_data.get('security', {}))
        )
    
    def _parse_research_config(self, research_data: Dict[str, Any]) -> ResearchConfig:
        """Parse research configuration section."""
        return ResearchConfig(
            outline=OutlineConfig(**research_data.get('outline', {})),
            task_splitting=TaskSplittingConfig(**research_data.get('task_splitting', {})),
            content_writing=ContentWritingConfig(
                writing_style=WritingStyleConfig(**research_data.get('content_writing', {}).get('writing_style', {})),
                content_limits=ContentLimitsConfig(**research_data.get('content_writing', {}).get('content_limits', {})),
                quality_control=QualityControlConfig(**research_data.get('content_writing', {}).get('quality_control', {}))
            ),
            planning=PlanningConfig(**research_data.get('planning', {}))
        )
    
    def _parse_tools_config(self, tools_data: Dict[str, Any]) -> ToolsConfig:
        """Parse tools configuration section."""
        return ToolsConfig(
            search_tool=ToolConfig(**tools_data.get('search_tool', {})),
            code_tool=ToolConfig(**tools_data.get('code_tool', {})),
            browser_tool=ToolConfig(**tools_data.get('browser_tool', {})),
            file_tool=ToolConfig(**tools_data.get('file_tool', {})),
            browser_use_tool=BrowserUseToolConfig(**tools_data.get('browser_use_tool', {}))
        )
    
    def _parse_mcp_config(self, mcp_data: Dict[str, Any]) -> MCPConfig:
        """Parse MCP configuration section."""
        return MCPConfig(
            capability_mapping={
                name: CapabilityMappingConfig(**mapping_config)
                for name, mapping_config in mcp_data.get('capability_mapping', {}).items()
            },
            execution=MCPExecutionConfig(**mcp_data.get('execution', {})),
            performance_tracking=MCPPerformanceTrackingConfig(**mcp_data.get('performance_tracking', {}))
        )
    
    def _parse_output_config(self, output_data: Dict[str, Any]) -> OutputConfig:
        """Parse output configuration section."""
        markdown_data = output_data.get('markdown', {})
        return OutputConfig(
            markdown=MarkdownConfig(
                include_toc=markdown_data.get('include_toc', True),
                include_metadata=markdown_data.get('include_metadata', True),
                include_sources=markdown_data.get('include_sources', True),
                include_timestamps=markdown_data.get('include_timestamps', True),
                formatting=MarkdownFormattingConfig(**markdown_data.get('formatting', {})),
                templates=MarkdownTemplatesConfig(**markdown_data.get('templates', {}))
            ),
            file_naming=FileNamingConfig(**output_data.get('file_naming', {}))
        )
    
    def _parse_i18n_config(self, i18n_data: Dict[str, Any]) -> I18nConfig:
        """Parse internationalization configuration section."""
        return I18nConfig(
            default_language=i18n_data.get('default_language', 'zh-CN'),
            supported_languages=i18n_data.get('supported_languages', ['zh-CN', 'en-US', 'ja-JP']),
            language_settings={
                name: LanguageSettingsConfig(**settings)
                for name, settings in i18n_data.get('language_settings', {}).items()
            }
        )
    
    def _parse_development_config(self, development_data: Dict[str, Any]) -> DevelopmentConfig:
        """Parse development configuration section."""
        return DevelopmentConfig(
            debug_mode=development_data.get('debug_mode', False),
            verbose_logging=development_data.get('verbose_logging', False),
            enable_profiling=development_data.get('enable_profiling', False),
            testing=TestingConfig(**development_data.get('testing', {})),
            dev_tools=DevToolsConfig(**development_data.get('dev_tools', {}))
        )
    
    def _create_default_config(self):
        """Create default configuration file."""
        print(f"Creating default configuration file: {self.config_file}")
        
        # Create the default config.yml content
        default_config_content = """# DeepResearch 系统配置文件
# 配置文件格式：YAML

# LLM 模型配置
llm:
  # 默认 LLM 提供商
  default_provider: "openai"
  
  # OpenAI 配置
  openai:
    model: "gpt-4-turbo-preview"
    temperature: 0.7
    max_tokens: 4000
    timeout: 60
    
  # Anthropic Claude 配置
  claude:
    model: "claude-3-sonnet-20240229"
    temperature: 0.7
    max_tokens: 4000
    timeout: 60
    
  # Google Gemini 配置
  gemini:
    model: "gemini-pro"
    temperature: 0.7
    max_tokens: 4000
    timeout: 60
    
  # Ollama 本地模型配置
  ollama:
    base_url: "http://localhost:11434"
    model: "qwen3:14b"
    temperature: 0.7
    max_tokens: 4000
    timeout: 60
    
  # DeepSeek 配置
  deepseek:
    model: "deepseek-coder"
    temperature: 0.7
    max_tokens: 4000
    timeout: 60

# 搜索引擎配置
search:
  # 默认搜索引擎
  default_engine: "tavily"
  
  # 备用搜索引擎列表
  fallback_engines:
    - "duckduckgo"
    - "brave"
    - "google"
    - "bing"
  
  # 搜索参数
  max_results: 10
  timeout: 30
  
  # 搜索引擎特定配置
  engines:
    duckduckgo:
      region: "cn-zh"
      safe_search: "moderate"
    
    google:
      # 需要 SerpAPI Key
      country: "cn"
      language: "zh"
      
    bing:
      # 需要 Bing Search API Key
      market: "zh-CN"
      safe_search: "moderate"

# 文件存储配置
file_storage:
  # Google Drive 配置
  google_drive:
    credentials_file: "credentials.json"
    token_file: "token.json"
    scopes:
      - "https://www.googleapis.com/auth/drive.readonly"
      - "https://www.googleapis.com/auth/drive.file"
  
  # Dropbox 配置
  dropbox:
    # 通过环境变量配置 app_key, app_secret, access_token
    timeout: 30

# 系统配置
system:
  # 输出设置
  output_dir: "output"
  temp_dir: "temp"
  
  # 日志配置
  logging:
    level: "INFO"
    file: "deepresearch.log"
    format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    max_file_size: "10MB"
    backup_count: 5
  
  # 浏览器自动化配置
  browser:
    headless: true
    timeout: 30000  # 毫秒
    user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    viewport:
      width: 1920
      height: 1080
  
  # 代码执行配置
  code_execution:
    timeout: 60  # 秒
    max_output_length: 10000
    allowed_imports:
      - "pandas"
      - "numpy"
      - "matplotlib"
      - "seaborn"
      - "requests"
      - "json"
      - "csv"
      - "datetime"
      - "re"
      - "math"
      - "statistics"
    
    # 禁止的操作
    forbidden_operations:
      - "os.system"
      - "subprocess"
      - "eval"
      - "exec"
      - "__import__"
  
  # 研究配置
  research:
    # 提纲生成配置
    outline:
      max_depth: 3
      max_sections: 8
      max_subsections_per_section: 5
      default_language: "zh-CN"
      research_depth: "comprehensive"  # basic, standard, comprehensive
    
    # 任务拆分配置
    task_splitting:
      max_tasks_per_section: 5
      max_tasks_per_subsection: 3
      include_verification_tasks: true
      include_synthesis_tasks: true
      task_granularity: "medium"  # fine, medium, coarse
    
    # 内容写作配置
    content_writing:
      writing_style:
        tone: "academic"  # academic, professional, casual
        target_audience: "general"  # general, expert, beginner
        citation_style: "inline"  # inline, footnote, endnote
        include_examples: true
        include_statistics: true
      
      content_limits:
        max_length: 2000
        min_length: 300
      
      quality_control:
        include_sources: true
        fact_check: true
        use_templates: true
    
    # 规划配置
    planning:
      default_strategy: "adaptive"  # sequential, parallel, adaptive, priority
      max_parallel_tasks: 3
      enable_dynamic_replanning: true
      resource_optimization: true
      fallback_enabled: true
  
  # 性能配置
  performance:
    max_concurrent_requests: 5
    request_retry_count: 3
    request_retry_delay: 1  # 秒
    cache_enabled: true
    cache_ttl: 3600  # 秒
  
  # 安全配置
  security:
    enable_sandbox: true
    max_file_size: "50MB"
    allowed_file_types:
      - ".txt"
      - ".md"
      - ".csv"
      - ".json"
      - ".pdf"
      - ".docx"
    
    rate_limiting:
      requests_per_minute: 60
      requests_per_hour: 1000

# 工具配置
tools:
  # 搜索工具配置
  search_tool:
    enabled: true
    max_results_per_query: 10
    result_filtering: true
  
  # 代码执行工具配置
  code_tool:
    enabled: true
    execution_environment: "sandbox"
    memory_limit: "512MB"
  
  # 浏览器工具配置
  browser_tool:
    enabled: true
    max_pages_per_session: 10
    screenshot_enabled: true
  
  # 文件工具配置
  file_tool:
    enabled: true
    max_file_size: "10MB"
    auto_encoding_detection: true

# MCP (多能力规划) 配置
mcp:
  # 能力映射配置
  capability_mapping:
    search:
      tools: ["web_search"]
      priority: 1
    
    llm:
      tools: ["llm_generation"]
      priority: 5
    
    script:
      tools: ["python_executor"]
      priority: 4
    
    browser:
      tools: ["browser_automation"]
      priority: 6
    
    file:
      tools: ["file_reader"]
      priority: 2
    
    analysis:
      tools: ["python_executor", "data_analysis"]
      priority: 3
  
  # 执行策略配置
  execution:
    batch_size: 3
    timeout_per_batch: 300  # 秒
    failure_threshold: 0.3  # 30% 失败率触发重新规划
    
  # 性能跟踪配置
  performance_tracking:
    enabled: true
    track_execution_time: true
    track_success_rate: true
    track_resource_usage: true

# 输出格式配置
output:
  # Markdown 输出配置
  markdown:
    include_toc: true
    include_metadata: true
    include_sources: true
    include_timestamps: true
    
    # 格式化选项
    formatting:
      heading_style: "atx"  # atx (#) or setext (underline)
      code_block_style: "fenced"  # fenced (```) or indented
      emphasis_style: "asterisk"  # asterisk (*) or underscore (_)
      
    # 模板配置
    templates:
      report_template: "default"
      section_template: "academic"
      
  # 文件命名配置
  file_naming:
    pattern: "{topic}_{timestamp}"
    timestamp_format: "%Y%m%d_%H%M%S"
    max_filename_length: 100
    sanitize_filename: true

# 国际化配置
i18n:
  default_language: "zh-CN"
  supported_languages:
    - "zh-CN"
    - "en-US"
    - "ja-JP"
  
  # 语言特定配置
  language_settings:
    zh-CN:
      date_format: "%Y年%m月%d日"
      number_format: "chinese"
      
    en-US:
      date_format: "%B %d, %Y"
      number_format: "western"

# 开发和调试配置
development:
  debug_mode: false
  verbose_logging: false
  enable_profiling: false
  
  # 测试配置
  testing:
    mock_api_calls: false
    test_data_dir: "tests/data"
    
  # 开发工具配置
  dev_tools:
    auto_reload: false
    show_stack_traces: true
"""
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.write(default_config_content)
            print(f"✅ 默认配置文件已创建: {self.config_file}")
        except Exception as e:
            print(f"❌ 创建配置文件失败: {e}")
        
        # Load the default configuration
        self._load_default_config()
    
    def _load_default_config(self):
        """Load default configuration values."""
        # Default LLM config
        self.llm = LLMConfig(
            default_provider="openai",
            openai=LLMProviderConfig(model="gpt-4-turbo-preview"),
            claude=LLMProviderConfig(model="claude-3-sonnet-20240229"),
            gemini=LLMProviderConfig(model="gemini-pro"),
            ollama=LLMProviderConfig(
                model="qwen3:14b",
                base_url="http://localhost:11434"
            ),
            deepseek=LLMProviderConfig(model="deepseek-coder")
        )
        
        # Default search config
        self.search = SearchConfig()
        
        # Default file storage config
        self.file_storage = FileStorageConfig(
            google_drive=GoogleDriveConfig(),
            dropbox=DropboxConfig()
        )
        
        # Default system config
        self.system = SystemConfig(
            logging=LoggingConfig(),
            browser=BrowserConfig(),
            code_execution=CodeExecutionConfig(),
            research=ResearchConfig(
                outline=OutlineConfig(),
                task_splitting=TaskSplittingConfig(),
                content_writing=ContentWritingConfig(
                    writing_style=WritingStyleConfig(),
                    content_limits=ContentLimitsConfig(),
                    quality_control=QualityControlConfig()
                ),
                planning=PlanningConfig()
            ),
            performance=PerformanceConfig(),
            security=SecurityConfig()
        )
        
        # Default tools config
        self.tools = ToolsConfig()
        
        # Default MCP config
        self.mcp = MCPConfig()
        
        # Default output config
        self.output = OutputConfig()
        
        # Default i18n config
        self.i18n = I18nConfig()
        
        # Default development config
        self.development = DevelopmentConfig()
    
    def get_llm_config(self, provider: str = None) -> Dict[str, Any]:
        """Get LLM configuration for specified provider."""
        provider = provider or self.llm.default_provider
        
        provider_configs = {
            "openai": {
                "api_key": self.llm.openai_api_key,
                "model": self.llm.openai.model,
                "temperature": self.llm.openai.temperature,
                "max_tokens": self.llm.openai.max_tokens,
                "timeout": self.llm.openai.timeout,
            },
            "claude": {
                "api_key": self.llm.anthropic_api_key,
                "model": self.llm.claude.model,
                "temperature": self.llm.claude.temperature,
                "max_tokens": self.llm.claude.max_tokens,
                "timeout": self.llm.claude.timeout,
            },
            "gemini": {
                "api_key": self.llm.google_api_key,
                "model": self.llm.gemini.model,
                "temperature": self.llm.gemini.temperature,
                "max_tokens": self.llm.gemini.max_tokens,
                "timeout": self.llm.gemini.timeout,
            },
            "ollama": {
                "base_url": self.llm.ollama.base_url,
                "model": self.llm.ollama.model,
                "temperature": self.llm.ollama.temperature,
                "max_tokens": self.llm.ollama.max_tokens,
                "timeout": self.llm.ollama.timeout,
            },
            "deepseek": {
                "api_key": self.llm.deepseek_api_key,
                "model": self.llm.deepseek.model,
                "temperature": self.llm.deepseek.temperature,
                "max_tokens": self.llm.deepseek.max_tokens,
                "timeout": self.llm.deepseek.timeout,
            }
        }
        
        return provider_configs.get(provider, provider_configs["openai"])
    
    def validate_api_keys(self) -> Dict[str, bool]:
        """Validate which API keys are available."""
        return {
            "openai": bool(self.llm.openai_api_key),
            "claude": bool(self.llm.anthropic_api_key),
            "gemini": bool(self.llm.google_api_key),
            "deepseek": bool(self.llm.deepseek_api_key),
            "tavily": bool(self.search.tavily_api_key),
            "brave": bool(self.search.brave_search_api_key),
            "serpapi": bool(self.search.serpapi_key),
            "bing": bool(self.search.bing_search_key),
            "google_drive": bool(os.path.exists(self.file_storage.google_drive.credentials_file)),
            "dropbox": bool(self.file_storage.dropbox.app_key),
        }
    
    def reload_config(self):
        """Reload configuration from file."""
        self._load_config()
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration."""
        return {
            "llm_provider": self.llm.default_provider,
            "search_engine": self.search.default_engine,
            "output_dir": self.system.output_dir,
            "debug_mode": self.development.debug_mode,
            "api_keys_available": self.validate_api_keys(),
            "tools_enabled": {
                "search": self.tools.search_tool.enabled,
                "code": self.tools.code_tool.enabled,
                "browser": self.tools.browser_tool.enabled,
                "file": self.tools.file_tool.enabled,
            }
        }
    
    def get(self, key: str, default=None):
        """Get configuration value by key with default fallback."""
        try:
            # Support nested key access like "llm.default_provider"
            if "." in key:
                keys = key.split(".")
                value = self
                for k in keys:
                    if hasattr(value, k):
                        value = getattr(value, k)
                    else:
                        return default
                return value
            else:
                # Simple key access
                return getattr(self, key, default)
        except Exception:
            return default


# Global config instance
config = Config() 