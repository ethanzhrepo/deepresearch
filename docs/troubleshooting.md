# DeepResearch 故障排除指南

## 🔍 常见问题诊断

### 快速诊断命令

```bash
# 检查系统配置
./run.sh config-check

# 运行安装测试
./run.sh test

# 查看系统日志
tail -f deepresearch.log

# 检查环境状态
./run.sh config-show
```

## 🚨 常见错误及解决方案

### 1. API 密钥相关错误

#### 错误：`Invalid API key`
```
❌ Error: Invalid API key for OpenAI
❌ Error: Authentication failed for Claude API
```

**解决方案：**
```bash
# 1. 检查密钥格式
echo $OPENAI_API_KEY | grep -E "^sk-[a-zA-Z0-9]{48}$"
echo $ANTHROPIC_API_KEY | grep -E "^sk-ant-[a-zA-Z0-9-]{95}$"

# 2. 验证密钥有效性
./run.sh config-check

# 3. 重新配置密钥
nano .env
```

**常见原因：**
- 密钥格式错误（缺少前缀、长度不对）
- 密钥已过期或被撤销
- 环境变量未正确设置
- 配置文件路径错误

#### 错误：`API quota exceeded`
```
❌ Error: You exceeded your current quota
❌ Error: Rate limit exceeded
```

**解决方案：**
```bash
# 1. 检查 API 使用量
# 访问对应服务商的控制台查看用量

# 2. 配置多个提供商
nano .env
# 添加备用 API 密钥

# 3. 调整请求频率
nano config.yml
# 增加 request_delay 配置
```

### 2. 网络连接问题

#### 错误：`Connection timeout`
```
❌ Error: Connection timeout after 30 seconds
❌ Error: Failed to connect to API endpoint
```

**解决方案：**
```bash
# 1. 检查网络连接
ping google.com
curl -I https://api.openai.com

# 2. 配置代理（如需要）
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=https://proxy.example.com:8080

# 3. 增加超时时间
nano config.yml
# 修改 timeout 配置
```

#### 错误：`SSL certificate verification failed`
```
❌ Error: SSL: CERTIFICATE_VERIFY_FAILED
```

**解决方案：**
```bash
# 1. 更新证书
# macOS
brew install ca-certificates

# Ubuntu/Debian
sudo apt-get update && sudo apt-get install ca-certificates

# 2. 临时禁用 SSL 验证（不推荐）
export PYTHONHTTPSVERIFY=0

# 3. 配置自定义证书路径
export SSL_CERT_FILE=/path/to/cacert.pem
```

### 3. 依赖和环境问题

#### 错误：`ModuleNotFoundError`
```
❌ ModuleNotFoundError: No module named 'openai'
❌ ModuleNotFoundError: No module named 'anthropic'
```

**解决方案：**
```bash
# 1. 检查 conda 环境
conda info --envs
conda activate deep-research-dev

# 2. 重新安装依赖
pip install -r requirements.txt

# 3. 检查 Python 路径
which python
python -c "import sys; print(sys.path)"

# 4. 重新运行安装脚本
./setup.sh
```

#### 错误：`Permission denied`
```
❌ PermissionError: [Errno 13] Permission denied: '/path/to/file'
```

**解决方案：**
```bash
# 1. 检查文件权限
ls -la output/ logs/ cache/

# 2. 修复权限
chmod 755 output/ logs/ cache/
chmod 644 .env config.yml

# 3. 检查目录所有者
sudo chown -R $USER:$USER ./
```

### 4. 内存和性能问题

#### 错误：`Out of memory`
```
❌ Error: Out of memory
❌ MemoryError: Unable to allocate array
```

**解决方案：**
```bash
# 1. 检查内存使用
free -h
top -p $(pgrep -f deepresearch)

# 2. 减少并发请求
nano config.yml
# 设置 max_concurrent_requests: 2

# 3. 清理缓存
rm -rf cache/*
rm -rf __pycache__/

# 4. 调整章节数量
./run.sh interactive "主题" --max-sections 4
```

#### 错误：`Process killed`
```
❌ Process was killed (signal 9)
❌ Worker process terminated unexpectedly
```

**解决方案：**
```bash
# 1. 检查系统资源
dmesg | grep -i "killed process"
journalctl -u deepresearch

# 2. 增加交换空间
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 3. 调整系统限制
ulimit -v 2097152  # 限制虚拟内存为 2GB
```

### 5. 工具执行问题

#### 错误：`Docker not found`
```
❌ Error: Docker daemon not running
❌ Error: Cannot connect to Docker socket
```

**解决方案：**
```bash
# 1. 启动 Docker
sudo systemctl start docker
sudo systemctl enable docker

# 2. 检查 Docker 状态
docker --version
docker ps

# 3. 配置用户权限
sudo usermod -aG docker $USER
newgrp docker

# 4. 使用本地执行环境
nano config.yml
# 设置 execution_environment: "local"
```

#### 错误：`Browser automation failed`
```
❌ Error: Chrome browser not found
❌ Error: WebDriver session failed
```

**解决方案：**
```bash
# 1. 安装浏览器
# Ubuntu/Debian
sudo apt-get install chromium-browser

# macOS
brew install --cask google-chrome

# 2. 安装 WebDriver
pip install chromedriver-autoinstaller

# 3. 配置无头模式
nano config.yml
# 设置 headless: true
```

### 6. 搜索引擎问题

#### 错误：`Search engine rate limited`
```
❌ Error: Too many requests to search engine
❌ Error: Search quota exceeded
```

**解决方案：**
```bash
# 1. 配置多个搜索引擎
nano .env
# 添加多个搜索 API 密钥

# 2. 调整搜索策略
nano config.yml
# 设置 rate_limit_delay: 5.0

# 3. 使用免费搜索引擎
# DuckDuckGo 不需要 API 密钥
```

## 🔧 高级故障排除

### 日志分析

#### 启用详细日志
```bash
# 1. 设置日志级别
export LOG_LEVEL=DEBUG

# 2. 启用调试模式
./run.sh interactive "主题" --debug

# 3. 查看分类日志
tail -f logs/search.log
tail -f logs/llm.log
tail -f logs/tools.log
```

#### 日志分析脚本
```python
#!/usr/bin/env python3
"""日志分析脚本"""

import re
import json
from collections import Counter
from datetime import datetime

def analyze_logs(log_file):
    """分析日志文件"""
    errors = []
    warnings = []
    performance_data = []
    
    with open(log_file, 'r') as f:
        for line in f:
            if 'ERROR' in line:
                errors.append(line.strip())
            elif 'WARNING' in line:
                warnings.append(line.strip())
            elif 'response_time' in line:
                # 提取性能数据
                match = re.search(r'response_time: ([\d.]+)', line)
                if match:
                    performance_data.append(float(match.group(1)))
    
    # 生成报告
    report = {
        'error_count': len(errors),
        'warning_count': len(warnings),
        'avg_response_time': sum(performance_data) / len(performance_data) if performance_data else 0,
        'common_errors': Counter([e.split(':')[0] for e in errors]).most_common(5)
    }
    
    return report

if __name__ == "__main__":
    report = analyze_logs('deepresearch.log')
    print(json.dumps(report, indent=2))
```

### 性能监控

#### 系统监控脚本
```bash
#!/bin/bash
# monitor.sh - 系统监控脚本

echo "=== DeepResearch 系统监控 ==="
echo "时间: $(date)"
echo

# CPU 使用率
echo "CPU 使用率:"
top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1

# 内存使用
echo "内存使用:"
free -h | grep Mem | awk '{print "使用: " $3 "/" $2 " (" $3/$2*100 "%)"}'

# 磁盘使用
echo "磁盘使用:"
df -h | grep -E "/$|/home"

# 进程状态
echo "DeepResearch 进程:"
ps aux | grep -E "(python|deepresearch)" | grep -v grep

# 网络连接
echo "网络连接:"
netstat -an | grep -E ":80|:443|:8000" | wc -l

# API 响应测试
echo "API 连接测试:"
curl -s -o /dev/null -w "%{http_code} %{time_total}s" https://api.openai.com/v1/models
```

### 配置验证

#### 配置验证脚本
```python
#!/usr/bin/env python3
"""配置验证脚本"""

import os
import yaml
import json
from pathlib import Path

def validate_config():
    """验证配置文件"""
    issues = []
    
    # 检查配置文件
    config_file = Path('config.yml')
    if not config_file.exists():
        issues.append("配置文件 config.yml 不存在")
    else:
        try:
            with open(config_file) as f:
                config = yaml.safe_load(f)
            
            # 验证必需配置
            required_sections = ['llm', 'search', 'tools', 'system']
            for section in required_sections:
                if section not in config:
                    issues.append(f"缺少配置节: {section}")
        
        except yaml.YAMLError as e:
            issues.append(f"配置文件语法错误: {e}")
    
    # 检查环境变量
    env_file = Path('.env')
    if not env_file.exists():
        issues.append("环境变量文件 .env 不存在")
    
    # 检查 API 密钥
    api_keys = {
        'OPENAI_API_KEY': r'^sk-[a-zA-Z0-9]{48}$',
        'ANTHROPIC_API_KEY': r'^sk-ant-[a-zA-Z0-9-]{95}$',
        'GOOGLE_API_KEY': r'^[a-zA-Z0-9_-]{39}$'
    }
    
    for key, pattern in api_keys.items():
        value = os.getenv(key)
        if value:
            import re
            if not re.match(pattern, value):
                issues.append(f"API 密钥格式错误: {key}")
    
    # 检查目录
    required_dirs = ['output', 'logs', 'cache']
    for dir_name in required_dirs:
        if not Path(dir_name).exists():
            issues.append(f"缺少目录: {dir_name}")
    
    return issues

if __name__ == "__main__":
    issues = validate_config()
    if issues:
        print("发现以下配置问题:")
        for issue in issues:
            print(f"❌ {issue}")
    else:
        print("✅ 配置验证通过")
```

## 🛠️ 修复工具

### 自动修复脚本

```bash
#!/bin/bash
# auto_fix.sh - 自动修复脚本

echo "🔧 DeepResearch 自动修复工具"
echo "================================"

# 修复目录权限
echo "修复目录权限..."
mkdir -p output logs cache
chmod 755 output logs cache
chmod 644 .env config.yml 2>/dev/null || true

# 清理缓存
echo "清理缓存..."
rm -rf cache/*
rm -rf __pycache__/
find . -name "*.pyc" -delete

# 重新安装依赖
echo "检查依赖..."
if ! python -c "import openai" 2>/dev/null; then
    echo "重新安装依赖..."
    pip install -r requirements.txt
fi

# 检查 Docker
if command -v docker >/dev/null 2>&1; then
    if ! docker ps >/dev/null 2>&1; then
        echo "启动 Docker..."
        sudo systemctl start docker 2>/dev/null || true
    fi
fi

# 验证配置
echo "验证配置..."
python -c "
import yaml
try:
    with open('config.yml') as f:
        yaml.safe_load(f)
    print('✅ 配置文件有效')
except Exception as e:
    print(f'❌ 配置文件错误: {e}')
"

echo "修复完成！"
```

### 重置脚本

```bash
#!/bin/bash
# reset.sh - 系统重置脚本

echo "⚠️  这将重置 DeepResearch 到初始状态"
read -p "确认继续? (y/N): " confirm

if [[ $confirm == [yY] ]]; then
    echo "重置系统..."
    
    # 停止所有进程
    pkill -f deepresearch 2>/dev/null || true
    
    # 清理数据
    rm -rf output/* logs/* cache/*
    rm -rf __pycache__/ .pytest_cache/
    
    # 重新安装
    ./setup.sh
    
    echo "✅ 系统重置完成"
else
    echo "取消重置"
fi
```

## 📞 获取帮助

### 社区支持

- **GitHub Issues**: [报告问题](https://github.com/your-repo/deepresearch/issues)
- **讨论区**: [GitHub Discussions](https://github.com/your-repo/deepresearch/discussions)
- **文档**: [在线文档](https://deepresearch.readthedocs.io)

### 问题报告模板

```markdown
## 问题描述
简要描述遇到的问题

## 复现步骤
1. 执行命令: `./run.sh interactive "主题"`
2. 选择选项: ...
3. 出现错误: ...

## 错误信息
```
粘贴完整的错误信息
```

## 环境信息
- 操作系统: macOS 14.0
- Python 版本: 3.11.5
- DeepResearch 版本: 2.0.0
- 安装方式: conda

## 配置信息
```yaml
# 相关配置片段（请移除敏感信息）
```

## 日志信息
```
# 相关日志片段
```
```

### 调试信息收集

```bash
#!/bin/bash
# collect_debug_info.sh - 收集调试信息

echo "收集 DeepResearch 调试信息..."

DEBUG_DIR="debug_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$DEBUG_DIR"

# 系统信息
echo "收集系统信息..."
{
    echo "=== 系统信息 ==="
    uname -a
    echo
    echo "=== Python 版本 ==="
    python --version
    echo
    echo "=== 已安装包 ==="
    pip list
    echo
    echo "=== 环境变量 ==="
    env | grep -E "(OPENAI|ANTHROPIC|GOOGLE|SERPAPI)" | sed 's/=.*/=***/'
} > "$DEBUG_DIR/system_info.txt"

# 配置文件
echo "收集配置文件..."
cp config.yml "$DEBUG_DIR/" 2>/dev/null || echo "config.yml 不存在"
cp .env "$DEBUG_DIR/env_template.txt" 2>/dev/null && sed -i 's/=.*/=***/' "$DEBUG_DIR/env_template.txt"

# 日志文件
echo "收集日志文件..."
cp deepresearch.log "$DEBUG_DIR/" 2>/dev/null || echo "日志文件不存在"
cp -r logs/ "$DEBUG_DIR/" 2>/dev/null || echo "logs 目录不存在"

# 运行测试
echo "运行诊断测试..."
./run.sh config-check > "$DEBUG_DIR/config_check.txt" 2>&1
./run.sh test > "$DEBUG_DIR/test_results.txt" 2>&1

# 打包
echo "打包调试信息..."
tar -czf "${DEBUG_DIR}.tar.gz" "$DEBUG_DIR"
rm -rf "$DEBUG_DIR"

echo "✅ 调试信息已保存到: ${DEBUG_DIR}.tar.gz"
echo "请将此文件附加到问题报告中"
```

---

**遇到问题不要慌，按照指南逐步排查！** 🔍✨ 