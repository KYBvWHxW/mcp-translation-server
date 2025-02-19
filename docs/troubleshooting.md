# 故障排除指南

## 常见问题

### 1. 服务启动问题

#### 1.1 服务无法启动

**症状**
- 服务器启动时报错
- 进程立即退出

**可能原因**
1. 配置文件错误
2. 端口被占用
3. 权限问题
4. 依赖缺失

**解决方案**
1. 检查配置文件
```bash
# 确保配置文件存在
ls config.py

# 验证配置文件语法
python -c "import config"
```

2. 检查端口占用
```bash
# Linux/macOS
lsof -i :8080
# Windows
netstat -ano | findstr 8080
```

3. 检查权限
```bash
# 检查文件权限
ls -l config.py
ls -l resources/

# 检查日志目录权限
ls -l logs/
```

4. 验证依赖
```bash
pip install -r requirements.txt
```

#### 1.2 GPU 不可用

**症状**
- CUDA相关错误
- 服务默认使用CPU

**可能原因**
1. CUDA驱动未安装
2. CUDA版本不匹配
3. GPU内存不足

**解决方案**
1. 验证CUDA安装
```bash
nvidia-smi
```

2. 检查CUDA版本
```bash
python -c "import torch; print(torch.version.cuda)"
```

3. 监控GPU内存
```bash
watch -n 1 nvidia-smi
```

### 2. 翻译问题

#### 2.1 翻译质量差

**症状**
- 翻译结果不准确
- 输出不完整

**可能原因**
1. 模型未正确加载
2. 预处理错误
3. 资源文件损坏

**解决方案**
1. 验证模型加载
```python
from server import translation_server
print(translation_server.model.config)
```

2. 检查预处理
```python
# 开启详细日志
import logging
logging.basicConfig(level=logging.DEBUG)
```

3. 验证资源完整性
```bash
python scripts/verify_resources.py
```

#### 2.2 翻译超时

**症状**
- 请求响应时间长
- 超时错误

**可能原因**
1. 系统负载高
2. 批处理配置不当
3. 资源竞争

**解决方案**
1. 监控系统负载
```bash
top  # 或 htop
```

2. 调整批处理参数
```python
# config.py
BATCH_SIZE = 16  # 减小批处理大小
TIMEOUT = 30     # 增加超时时间
```

3. 检查资源使用
```bash
ps aux | grep python
```

### 3. 性能问题

#### 3.1 内存泄漏

**症状**
- 内存使用持续增长
- 服务变慢

**可能原因**
1. 缓存未清理
2. 资源未释放
3. 循环引用

**解决方案**
1. 监控内存使用
```bash
# 安装内存分析工具
pip install memory_profiler

# 运行分析
mprof run server.py
mprof plot
```

2. 手动触发垃圾回收
```python
import gc
gc.collect()
```

3. 检查引用
```python
# 安装objgraph
pip install objgraph

# 分析对象引用
import objgraph
objgraph.show_most_common_types()
```

#### 3.2 CPU 使用率高

**症状**
- CPU使用率持续高
- 系统响应慢

**可能原因**
1. 并发配置不当
2. 处理线程过多
3. 死循环

**解决方案**
1. 检查进程状态
```bash
top -H -p <pid>
```

2. 生成性能分析
```bash
# 安装性能分析工具
pip install py-spy

# 运行分析
py-spy record -o profile.svg --pid <pid>
```

3. 调整并发设置
```python
# config.py
WORKER_PROCESSES = 4
THREAD_POOL_SIZE = 8
```

### 4. 网络问题

#### 4.1 连接超时

**症状**
- API请求超时
- 连接被拒绝

**可能原因**
1. 网络配置错误
2. 防火墙限制
3. 负载均衡问题

**解决方案**
1. 检查网络配置
```bash
# 检查监听地址
netstat -tlpn | grep python

# 测试连接
curl -v http://localhost:8080/health
```

2. 验证防火墙
```bash
# Linux
sudo iptables -L

# 测试端口
nc -zv localhost 8080
```

3. 检查日志
```bash
tail -f logs/server.log
```

#### 4.2 并发连接问题

**症状**
- 连接数突增
- 连接被拒绝

**可能原因**
1. 连接限制太低
2. 资源耗尽
3. 连接未释放

**解决方案**
1. 调整系统限制
```bash
# 检查当前限制
ulimit -n

# 修改限制（临时）
ulimit -n 65535
```

2. 监控连接
```bash
netstat -an | grep ESTABLISHED | wc -l
```

3. 配置连接池
```python
# config.py
CONNECTION_POOL_SIZE = 100
CONNECTION_TIMEOUT = 5
```

### 5. 数据问题

#### 5.1 资源文件损坏

**症状**
- 资源加载失败
- 数据不完整

**可能原因**
1. 文件损坏
2. 权限问题
3. 磁盘问题

**解决方案**
1. 验证文件完整性
```bash
# 检查文件
md5sum resources/*

# 重新下载资源
python scripts/download_resources.py
```

2. 检查权限
```bash
ls -l resources/
chmod -R 644 resources/*
```

3. 检查磁盘
```bash
df -h
fsck /dev/sda1  # 请谨慎使用
```

#### 5.2 缓存问题

**症状**
- 缓存命中率低
- 缓存不一致

**可能原因**
1. 缓存配置不当
2. 缓存未更新
3. 缓存冲突

**解决方案**
1. 检查缓存配置
```python
# config.py
CACHE_SIZE = "1GB"
CACHE_TTL = 3600
```

2. 清理缓存
```python
# 手动清理
translation_server.cache.clear()

# 验证缓存状态
print(translation_server.cache.stats())
```

3. 监控缓存使用
```python
# 启用缓存监控
CACHE_MONITORING = True
```

## 日志收集

### 1. 系统日志

收集系统日志：
```bash
# 应用日志
tail -f logs/server.log

# 系统日志
journalctl -u mcp-translation-server

# Docker日志
docker logs mcp-translation-server
```

### 2. 性能日志

收集性能数据：
```bash
# CPU和内存使用
top -b -n 1 > system_status.log

# IO统计
iostat > io_stats.log

# 网络统计
netstat -s > network_stats.log
```

### 3. 错误报告

生成错误报告：
```bash
# 收集错误信息
python scripts/generate_error_report.py

# 导出诊断信息
python scripts/export_diagnostics.py
```

## 监控告警

### 1. 设置监控

配置 Prometheus 监控：
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'mcp-translation'
    static_configs:
      - targets: ['localhost:8080']
```

### 2. 配置告警

设置告警规则：
```yaml
# alerts.yml
groups:
  - name: translation-alerts
    rules:
      - alert: HighErrorRate
        expr: error_rate > 0.1
        for: 5m
```

### 3. 查看仪表盘

访问 Grafana 仪表盘：
- 系统性能指标
- 翻译质量指标
- 资源使用情况

## 应急处理

### 1. 服务降级

启用降级模式：
```python
# 降级配置
FALLBACK_MODE = True
LIGHTWEIGHT_MODEL = True
```

### 2. 紧急重启

安全重启服务：
```bash
# 优雅关闭
kill -SIGTERM <pid>

# 等待处理完成
sleep 30

# 重启服务
systemctl restart mcp-translation-server
```

### 3. 数据恢复

从备份恢复：
```bash
# 恢复配置
cp config.backup.py config.py

# 恢复资源
cp -r resources.backup/* resources/

# 验证恢复
python scripts/verify_resources.py
```

## 联系支持

如果问题无法解决：

1. 准备信息
   - 错误日志
   - 系统信息
   - 复现步骤

2. 联系方式
   - 提交 Issue: [GitHub Issues](https://github.com/your-org/mcp-translation-server/issues)
   - 邮件支持: support@your-org.com
   - 紧急热线: +1-xxx-xxx-xxxx
