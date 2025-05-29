# DeepResearch 安全最佳实践

## 🔒 安全概览

DeepResearch 采用多层安全架构，确保用户数据和系统安全：

- **数据加密**: 传输和存储全程加密
- **访问控制**: 细粒度权限管理
- **安全隔离**: Docker 沙箱执行环境
- **审计日志**: 完整的操作审计追踪

## 🛡️ 核心安全特性

### 1. 数据保护

#### 数据加密

```python
import cryptography
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

class DataEncryption:
    """数据加密管理器"""
    
    def __init__(self, password: str):
        self.password = password.encode()
        self.salt = os.urandom(16)
        self.key = self._derive_key()
        self.cipher = Fernet(self.key)
    
    def _derive_key(self) -> bytes:
        """派生加密密钥"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.password))
        return key
    
    def encrypt_data(self, data: str) -> str:
        """加密数据"""
        encrypted_data = self.cipher.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """解密数据"""
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted_data = self.cipher.decrypt(encrypted_bytes)
        return decrypted_data.decode()

# 使用示例
encryptor = DataEncryption("your-secure-password")

# 加密敏感配置
api_key = "sk-your-openai-api-key"
encrypted_key = encryptor.encrypt_data(api_key)
print(f"加密后的 API 密钥: {encrypted_key}")

# 解密使用
decrypted_key = encryptor.decrypt_data(encrypted_key)
```

#### 敏感数据处理

```python
import os
import json
from typing import Dict, Any
from pathlib import Path

class SecureConfig:
    """安全配置管理"""
    
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.encryption = DataEncryption(os.getenv("DEEPRESEARCH_MASTER_KEY", ""))
    
    def save_secure_config(self, config: Dict[str, Any]):
        """保存加密配置"""
        # 分离敏感和非敏感数据
        sensitive_keys = ["api_key", "secret", "password", "token"]
        secure_config = {}
        public_config = {}
        
        for key, value in config.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                secure_config[key] = self.encryption.encrypt_data(str(value))
            else:
                public_config[key] = value
        
        # 保存配置文件
        with open(self.config_path, 'w') as f:
            json.dump({
                "public": public_config,
                "secure": secure_config
            }, f, indent=2)
        
        # 设置文件权限 (仅所有者可读写)
        os.chmod(self.config_path, 0o600)
    
    def load_secure_config(self) -> Dict[str, Any]:
        """加载解密配置"""
        if not self.config_path.exists():
            return {}
        
        with open(self.config_path, 'r') as f:
            data = json.load(f)
        
        config = data.get("public", {})
        secure_data = data.get("secure", {})
        
        # 解密敏感数据
        for key, encrypted_value in secure_data.items():
            config[key] = self.encryption.decrypt_data(encrypted_value)
        
        return config
```

### 2. API 安全

#### API 密钥管理

```python
import hashlib
import secrets
import time
from typing import Optional, Dict
from dataclasses import dataclass

@dataclass
class APIKey:
    """API 密钥信息"""
    key_id: str
    key_hash: str
    permissions: list
    created_at: float
    expires_at: Optional[float] = None
    last_used: Optional[float] = None
    usage_count: int = 0

class APIKeyManager:
    """API 密钥管理器"""
    
    def __init__(self):
        self.keys: Dict[str, APIKey] = {}
        self.rate_limits: Dict[str, list] = {}
    
    def generate_api_key(self, permissions: list, expires_in: Optional[int] = None) -> str:
        """生成 API 密钥"""
        # 生成随机密钥
        key = f"dr_{secrets.token_urlsafe(32)}"
        key_id = hashlib.sha256(key.encode()).hexdigest()[:16]
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        # 计算过期时间
        expires_at = None
        if expires_in:
            expires_at = time.time() + expires_in
        
        # 存储密钥信息
        self.keys[key_hash] = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            permissions=permissions,
            created_at=time.time(),
            expires_at=expires_at
        )
        
        return key
    
    def validate_api_key(self, key: str) -> Optional[APIKey]:
        """验证 API 密钥"""
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        if key_hash not in self.keys:
            return None
        
        api_key = self.keys[key_hash]
        
        # 检查是否过期
        if api_key.expires_at and time.time() > api_key.expires_at:
            return None
        
        # 更新使用信息
        api_key.last_used = time.time()
        api_key.usage_count += 1
        
        return api_key
    
    def check_rate_limit(self, key_hash: str, limit: int = 100, window: int = 3600) -> bool:
        """检查速率限制"""
        current_time = time.time()
        
        if key_hash not in self.rate_limits:
            self.rate_limits[key_hash] = []
        
        # 清理过期的请求记录
        self.rate_limits[key_hash] = [
            req_time for req_time in self.rate_limits[key_hash]
            if current_time - req_time < window
        ]
        
        # 检查是否超过限制
        if len(self.rate_limits[key_hash]) >= limit:
            return False
        
        # 记录当前请求
        self.rate_limits[key_hash].append(current_time)
        return True
```

#### 请求验证和授权

```python
from functools import wraps
from flask import request, jsonify, g
import jwt
from datetime import datetime, timedelta

class SecurityMiddleware:
    """安全中间件"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.api_key_manager = APIKeyManager()
    
    def require_api_key(self, permissions: list = None):
        """API 密钥验证装饰器"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # 获取 API 密钥
                auth_header = request.headers.get('Authorization')
                if not auth_header or not auth_header.startswith('Bearer '):
                    return jsonify({'error': 'Missing or invalid API key'}), 401
                
                api_key = auth_header.split(' ')[1]
                
                # 验证密钥
                key_info = self.api_key_manager.validate_api_key(api_key)
                if not key_info:
                    return jsonify({'error': 'Invalid API key'}), 401
                
                # 检查权限
                if permissions:
                    if not all(perm in key_info.permissions for perm in permissions):
                        return jsonify({'error': 'Insufficient permissions'}), 403
                
                # 检查速率限制
                if not self.api_key_manager.check_rate_limit(key_info.key_hash):
                    return jsonify({'error': 'Rate limit exceeded'}), 429
                
                # 将密钥信息添加到请求上下文
                g.api_key_info = key_info
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator
    
    def generate_jwt_token(self, user_id: str, permissions: list) -> str:
        """生成 JWT 令牌"""
        payload = {
            'user_id': user_id,
            'permissions': permissions,
            'exp': datetime.utcnow() + timedelta(hours=24),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_jwt_token(self, token: str) -> Optional[dict]:
        """验证 JWT 令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
```

### 3. 系统安全

#### Docker 安全配置

```dockerfile
# 安全的 Dockerfile 配置
FROM python:3.11-slim

# 创建非 root 用户
RUN groupadd -r deepresearch && useradd -r -g deepresearch deepresearch

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 设置文件权限
RUN chown -R deepresearch:deepresearch /app
RUN chmod -R 755 /app

# 切换到非 root 用户
USER deepresearch

# 暴露端口
EXPOSE 8000

# 启动应用
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 容器安全策略

```yaml
# docker-compose.security.yml
version: '3.8'

services:
  deepresearch:
    build: .
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    read_only: true
    tmpfs:
      - /tmp:noexec,nosuid,size=100m
    volumes:
      - ./data:/app/data:ro
      - ./logs:/app/logs:rw
    environment:
      - PYTHONDONTWRITEBYTECODE=1
      - PYTHONUNBUFFERED=1
    networks:
      - deepresearch_network
    restart: unless-stopped
    
  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - deepresearch
    networks:
      - deepresearch_network

networks:
  deepresearch_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

#### 系统加固

```bash
#!/bin/bash
# system_hardening.sh - 系统安全加固脚本

# 设置防火墙规则
setup_firewall() {
    echo "配置防火墙..."
    
    # 清除现有规则
    iptables -F
    iptables -X
    iptables -t nat -F
    iptables -t nat -X
    
    # 设置默认策略
    iptables -P INPUT DROP
    iptables -P FORWARD DROP
    iptables -P OUTPUT ACCEPT
    
    # 允许本地回环
    iptables -A INPUT -i lo -j ACCEPT
    iptables -A OUTPUT -o lo -j ACCEPT
    
    # 允许已建立的连接
    iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
    
    # 允许 SSH (修改为非标准端口)
    iptables -A INPUT -p tcp --dport 2222 -j ACCEPT
    
    # 允许 HTTP/HTTPS
    iptables -A INPUT -p tcp --dport 80 -j ACCEPT
    iptables -A INPUT -p tcp --dport 443 -j ACCEPT
    
    # 保存规则
    iptables-save > /etc/iptables/rules.v4
}

# 配置 fail2ban
setup_fail2ban() {
    echo "配置 fail2ban..."
    
    cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = 2222

[nginx-http-auth]
enabled = true

[nginx-limit-req]
enabled = true
EOF
    
    systemctl enable fail2ban
    systemctl start fail2ban
}

# 系统更新和安全补丁
update_system() {
    echo "更新系统..."
    apt update && apt upgrade -y
    apt autoremove -y
    
    # 启用自动安全更新
    echo 'Unattended-Upgrade::Automatic-Reboot "false";' >> /etc/apt/apt.conf.d/50unattended-upgrades
}

# 执行加固
setup_firewall
setup_fail2ban
update_system

echo "系统安全加固完成！"
```

## 🔐 访问控制

### 1. 基于角色的访问控制 (RBAC)

```python
from enum import Enum
from typing import Set, Dict, List
from dataclasses import dataclass

class Permission(Enum):
    """权限枚举"""
    RESEARCH_CREATE = "research:create"
    RESEARCH_READ = "research:read"
    RESEARCH_UPDATE = "research:update"
    RESEARCH_DELETE = "research:delete"
    CONFIG_READ = "config:read"
    CONFIG_WRITE = "config:write"
    ADMIN_ACCESS = "admin:access"
    USER_MANAGE = "user:manage"

class Role(Enum):
    """角色枚举"""
    GUEST = "guest"
    USER = "user"
    PREMIUM = "premium"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

@dataclass
class User:
    """用户信息"""
    user_id: str
    username: str
    email: str
    roles: Set[Role]
    permissions: Set[Permission]
    is_active: bool = True

class RBACManager:
    """基于角色的访问控制管理器"""
    
    def __init__(self):
        self.role_permissions = {
            Role.GUEST: {
                Permission.RESEARCH_READ,
            },
            Role.USER: {
                Permission.RESEARCH_CREATE,
                Permission.RESEARCH_READ,
                Permission.RESEARCH_UPDATE,
                Permission.CONFIG_READ,
            },
            Role.PREMIUM: {
                Permission.RESEARCH_CREATE,
                Permission.RESEARCH_READ,
                Permission.RESEARCH_UPDATE,
                Permission.RESEARCH_DELETE,
                Permission.CONFIG_READ,
                Permission.CONFIG_WRITE,
            },
            Role.ADMIN: {
                Permission.RESEARCH_CREATE,
                Permission.RESEARCH_READ,
                Permission.RESEARCH_UPDATE,
                Permission.RESEARCH_DELETE,
                Permission.CONFIG_READ,
                Permission.CONFIG_WRITE,
                Permission.USER_MANAGE,
                Permission.ADMIN_ACCESS,
            },
            Role.SUPER_ADMIN: set(Permission),  # 所有权限
        }
    
    def get_user_permissions(self, user: User) -> Set[Permission]:
        """获取用户权限"""
        permissions = set(user.permissions)
        
        # 添加角色权限
        for role in user.roles:
            permissions.update(self.role_permissions.get(role, set()))
        
        return permissions
    
    def check_permission(self, user: User, permission: Permission) -> bool:
        """检查用户权限"""
        if not user.is_active:
            return False
        
        user_permissions = self.get_user_permissions(user)
        return permission in user_permissions
    
    def require_permission(self, permission: Permission):
        """权限检查装饰器"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                user = g.get('current_user')
                if not user or not self.check_permission(user, permission):
                    return jsonify({'error': 'Insufficient permissions'}), 403
                return f(*args, **kwargs)
            return decorated_function
        return decorator
```

### 2. 多因素认证 (MFA)

```python
import pyotp
import qrcode
from io import BytesIO
import base64

class MFAManager:
    """多因素认证管理器"""
    
    def __init__(self):
        self.issuer_name = "DeepResearch"
    
    def generate_secret(self, user_id: str) -> str:
        """生成 MFA 密钥"""
        return pyotp.random_base32()
    
    def generate_qr_code(self, user_email: str, secret: str) -> str:
        """生成 QR 码"""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_email,
            issuer_name=self.issuer_name
        )
        
        # 生成 QR 码
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # 转换为 base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    def verify_token(self, secret: str, token: str) -> bool:
        """验证 TOTP 令牌"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
    
    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """生成备用码"""
        return [secrets.token_hex(4).upper() for _ in range(count)]
```

## 🛡️ 网络安全

### 1. HTTPS 配置

```nginx
# nginx.conf - 安全的 Nginx 配置
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL 证书配置
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # SSL 安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # 安全头
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;
    
    # 速率限制
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;
    
    location / {
        proxy_pass http://deepresearch:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

### 2. 网络监控

```python
import psutil
import time
from collections import defaultdict
from typing import Dict, List
import logging

class NetworkMonitor:
    """网络安全监控"""
    
    def __init__(self):
        self.connection_counts = defaultdict(int)
        self.suspicious_ips = set()
        self.blocked_ips = set()
        self.logger = logging.getLogger(__name__)
    
    def monitor_connections(self):
        """监控网络连接"""
        connections = psutil.net_connections(kind='inet')
        current_connections = defaultdict(int)
        
        for conn in connections:
            if conn.status == 'ESTABLISHED' and conn.raddr:
                remote_ip = conn.raddr.ip
                current_connections[remote_ip] += 1
        
        # 检测异常连接
        for ip, count in current_connections.items():
            if count > 50:  # 单个 IP 连接数过多
                self.logger.warning(f"Suspicious activity from IP: {ip} ({count} connections)")
                self.suspicious_ips.add(ip)
                
                if count > 100:  # 严重异常，加入黑名单
                    self.block_ip(ip)
        
        self.connection_counts = current_connections
    
    def block_ip(self, ip: str):
        """阻止 IP 访问"""
        if ip not in self.blocked_ips:
            self.blocked_ips.add(ip)
            self.logger.error(f"Blocking IP: {ip}")
            
            # 添加 iptables 规则
            import subprocess
            try:
                subprocess.run(['iptables', '-A', 'INPUT', '-s', ip, '-j', 'DROP'], 
                             check=True)
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Failed to block IP {ip}: {e}")
    
    def unblock_ip(self, ip: str):
        """解除 IP 阻止"""
        if ip in self.blocked_ips:
            self.blocked_ips.remove(ip)
            self.logger.info(f"Unblocking IP: {ip}")
            
            # 删除 iptables 规则
            import subprocess
            try:
                subprocess.run(['iptables', '-D', 'INPUT', '-s', ip, '-j', 'DROP'], 
                             check=True)
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Failed to unblock IP {ip}: {e}")
```

## 📋 安全检查清单

### 部署前安全检查

- [ ] **密钥管理**
  - [ ] 所有 API 密钥已加密存储
  - [ ] 使用环境变量管理敏感配置
  - [ ] 定期轮换 API 密钥
  - [ ] 实施密钥访问审计

- [ ] **网络安全**
  - [ ] 启用 HTTPS/TLS 加密
  - [ ] 配置防火墙规则
  - [ ] 实施速率限制
  - [ ] 设置网络监控

- [ ] **系统安全**
  - [ ] 使用非 root 用户运行应用
  - [ ] 启用容器安全策略
  - [ ] 定期更新系统补丁
  - [ ] 配置入侵检测

- [ ] **访问控制**
  - [ ] 实施 RBAC 权限控制
  - [ ] 启用多因素认证
  - [ ] 配置会话管理
  - [ ] 设置访问审计

- [ ] **数据保护**
  - [ ] 敏感数据加密
  - [ ] 实施数据备份
  - [ ] 配置数据清理策略
  - [ ] 遵循数据保护法规

### 运行时安全监控

```python
import schedule
import time
from datetime import datetime

class SecurityMonitor:
    """安全监控系统"""
    
    def __init__(self):
        self.network_monitor = NetworkMonitor()
        self.api_key_manager = APIKeyManager()
        self.logger = logging.getLogger(__name__)
    
    def daily_security_check(self):
        """每日安全检查"""
        self.logger.info("开始每日安全检查...")
        
        # 检查过期的 API 密钥
        expired_keys = self.check_expired_api_keys()
        if expired_keys:
            self.logger.warning(f"发现 {len(expired_keys)} 个过期的 API 密钥")
        
        # 检查异常访问模式
        self.analyze_access_patterns()
        
        # 检查系统资源使用
        self.check_system_resources()
        
        self.logger.info("每日安全检查完成")
    
    def check_expired_api_keys(self) -> List[str]:
        """检查过期的 API 密钥"""
        current_time = time.time()
        expired_keys = []
        
        for key_hash, api_key in self.api_key_manager.keys.items():
            if api_key.expires_at and current_time > api_key.expires_at:
                expired_keys.append(key_hash)
        
        # 清理过期密钥
        for key_hash in expired_keys:
            del self.api_key_manager.keys[key_hash]
        
        return expired_keys
    
    def analyze_access_patterns(self):
        """分析访问模式"""
        # 分析 API 调用频率
        # 检测异常访问时间
        # 识别可疑的用户行为
        pass
    
    def check_system_resources(self):
        """检查系统资源"""
        # CPU 使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > 90:
            self.logger.warning(f"CPU 使用率过高: {cpu_percent}%")
        
        # 内存使用率
        memory = psutil.virtual_memory()
        if memory.percent > 90:
            self.logger.warning(f"内存使用率过高: {memory.percent}%")
        
        # 磁盘使用率
        disk = psutil.disk_usage('/')
        if disk.percent > 90:
            self.logger.warning(f"磁盘使用率过高: {disk.percent}%")
    
    def start_monitoring(self):
        """启动安全监控"""
        # 每日安全检查
        schedule.every().day.at("02:00").do(self.daily_security_check)
        
        # 每小时网络监控
        schedule.every().hour.do(self.network_monitor.monitor_connections)
        
        # 运行调度器
        while True:
            schedule.run_pending()
            time.sleep(60)

# 启动安全监控
if __name__ == "__main__":
    monitor = SecurityMonitor()
    monitor.start_monitoring()
```

## 🚨 事件响应

### 安全事件处理流程

```python
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Any
import json

class IncidentSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SecurityIncident:
    """安全事件"""
    incident_id: str
    severity: IncidentSeverity
    title: str
    description: str
    source_ip: str
    timestamp: float
    affected_resources: List[str]
    status: str = "open"
    response_actions: List[str] = None

class IncidentResponse:
    """安全事件响应"""
    
    def __init__(self):
        self.incidents: Dict[str, SecurityIncident] = {}
        self.response_playbooks = {
            "brute_force": self.handle_brute_force,
            "ddos": self.handle_ddos,
            "unauthorized_access": self.handle_unauthorized_access,
            "data_breach": self.handle_data_breach,
        }
    
    def create_incident(self, incident_type: str, **kwargs) -> SecurityIncident:
        """创建安全事件"""
        incident_id = f"INC_{int(time.time())}"
        
        incident = SecurityIncident(
            incident_id=incident_id,
            **kwargs
        )
        
        self.incidents[incident_id] = incident
        
        # 自动响应
        if incident_type in self.response_playbooks:
            self.response_playbooks[incident_type](incident)
        
        return incident
    
    def handle_brute_force(self, incident: SecurityIncident):
        """处理暴力破解攻击"""
        # 1. 立即阻止源 IP
        self.block_ip(incident.source_ip)
        
        # 2. 增强认证要求
        self.enable_enhanced_auth()
        
        # 3. 通知管理员
        self.notify_admins(incident)
        
        incident.response_actions = [
            f"Blocked IP: {incident.source_ip}",
            "Enhanced authentication enabled",
            "Administrators notified"
        ]
    
    def handle_ddos(self, incident: SecurityIncident):
        """处理 DDoS 攻击"""
        # 1. 启用 DDoS 防护
        self.enable_ddos_protection()
        
        # 2. 限制连接数
        self.apply_connection_limits()
        
        # 3. 联系 CDN 提供商
        self.contact_cdn_provider(incident)
        
        incident.response_actions = [
            "DDoS protection enabled",
            "Connection limits applied",
            "CDN provider contacted"
        ]
    
    def handle_unauthorized_access(self, incident: SecurityIncident):
        """处理未授权访问"""
        # 1. 撤销相关会话
        self.revoke_sessions(incident.affected_resources)
        
        # 2. 强制密码重置
        self.force_password_reset(incident.affected_resources)
        
        # 3. 审计访问日志
        self.audit_access_logs()
        
        incident.response_actions = [
            "Sessions revoked",
            "Password reset enforced",
            "Access logs audited"
        ]
    
    def handle_data_breach(self, incident: SecurityIncident):
        """处理数据泄露"""
        # 1. 立即隔离受影响系统
        self.isolate_systems(incident.affected_resources)
        
        # 2. 保存证据
        self.preserve_evidence()
        
        # 3. 通知相关方
        self.notify_stakeholders(incident)
        
        # 4. 启动法律程序
        self.initiate_legal_procedures()
        
        incident.response_actions = [
            "Systems isolated",
            "Evidence preserved",
            "Stakeholders notified",
            "Legal procedures initiated"
        ]
```

---

**通过全面的安全措施，确保 DeepResearch 系统和用户数据的安全！** 🔒✨ 