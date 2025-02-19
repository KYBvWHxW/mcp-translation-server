# 详细安装指南

## 系统要求

### 硬件要求
- CPU: 4核或更多
- 内存: 8GB或更多
- 磁盘空间: 20GB可用空间
- GPU: NVIDIA GPU (推荐 CUDA 11.0+)

### 软件要求
- 操作系统: Linux (推荐 Ubuntu 20.04+) / macOS / Windows
- Python 3.9+
- CUDA Toolkit 11.0+ (如使用GPU)
- Docker (可选)
- Git

## 安装步骤

### 1. 环境准备

#### Linux/macOS
```bash
# 安装系统依赖
## Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
    python3-dev \
    python3-pip \
    git \
    build-essential \
    libssl-dev \
    libffi-dev

## macOS (使用Homebrew)
brew install python@3.9 git

# 安装virtualenv
pip3 install virtualenv
```

#### Windows
1. 下载并安装 [Python 3.9+](https://www.python.org/downloads/)
2. 下载并安装 [Git](https://git-scm.com/download/win)
3. 安装virtualenv:
```bash
pip install virtualenv
```

### 2. 克隆项目

```bash
git clone https://github.com/your-org/mcp-translation-server.git
cd mcp-translation-server
```

### 3. 创建虚拟环境

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
## Linux/macOS
source venv/bin/activate
## Windows
venv\Scripts\activate
```

### 4. 安装依赖

```bash
# 更新pip
pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt

# 如果使用GPU，安装CUDA支持
pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu113
```

### 5. 配置

1. 创建配置文件：
```bash
cp config.example.py config.py
```

2. 编辑 `config.py`，设置必要的配置项：
- API配置（主机、端口等）
- 模型配置
- 资源路径
- 缓存配置
- 监控配置

### 6. 准备语言资源

1. 下载预训练模型：
```bash
python scripts/download_models.py
```

2. 准备词典和语法规则：
```bash
python scripts/prepare_resources.py
```

### 7. 验证安装

1. 运行测试：
```bash
python -m pytest tests/
```

2. 启动服务器：
```bash
python server.py
```

3. 测试API：
```bash
curl -X POST http://localhost:8080/translate \
     -H "Content-Type: application/json" \
     -d '{"text": "amba boo", "direction": "m2c"}'
```

## Docker 安装

### 1. 安装 Docker

参考 [Docker 官方文档](https://docs.docker.com/get-docker/) 安装 Docker 和 Docker Compose。

### 2. 构建和运行

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d
```

## 常见问题

### 1. 内存不足
如果遇到内存不足的问题，可以：
- 减小批处理大小
- 使用较小的模型
- 增加系统swap空间

### 2. GPU 问题
- 确保已正确安装NVIDIA驱动
- 验证CUDA安装：`nvidia-smi`
- 检查PyTorch是否识别到GPU：
```python
import torch
print(torch.cuda.is_available())
```

### 3. 依赖冲突
如果遇到依赖冲突：
```bash
pip install -r requirements.txt --no-deps
pip install -r requirements.txt
```

## 升级指南

### 1. 备份
```bash
cp config.py config.backup.py
cp -r resources resources.backup
```

### 2. 更新代码
```bash
git pull origin main
```

### 3. 更新依赖
```bash
pip install -r requirements.txt --upgrade
```

### 4. 迁移配置
比较并合并配置文件的变更：
```bash
diff config.example.py config.backup.py
```

## 支持

如果在安装过程中遇到问题：
1. 查看 [故障排除指南](troubleshooting.md)
2. 在 [GitHub Issues](https://github.com/your-org/mcp-translation-server/issues) 搜索或提交问题
3. 联系技术支持：support@your-org.com
