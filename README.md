# CubQueue

<div align="center">
  <img src="logo.png" alt="CubQueue Logo" width="200">
</div>

CubQueue是一个Python构建的、轻量级的任务监控系统，使用命令行工具与RESTFul API交互，支持注册给定script，而后基于这些script提交任务，并管理它们产出的log、中间文件与结果文件。

## 特性

- 🚀 **轻量级设计**: 基于FastAPI和SQLite，部署简单
- 📝 **脚本管理**: 支持注册和管理Python脚本
- 🔄 **任务调度**: 异步任务执行和状态监控
- 📁 **文件管理**: 自动处理任务输入文件和输出结果
- 🌐 **多种接口**: 命令行工具、RESTful API和Python客户端库
- 📊 **实时监控**: 任务状态跟踪和日志查看

## 安装

### 系统要求

- Python 3.8+
- 支持的操作系统：Linux、macOS、Windows

### 从源码安装

```bash
git clone https://github.com/cubqueue/cubqueue.git
cd cubqueue
pip install -r requirements.txt
pip install -e .
```

### 使用pip安装

```bash
pip install cubqueue
```

## 快速开始

### 1. 启动服务器

```bash
# 启动守护进程
cubqueue start --base-dir /path/to/workspace --host 127.0.0.1 --port 8000 --daemon

# 或者前台运行
cubqueue start --base-dir /path/to/workspace --host 127.0.0.1 --port 8000
```

### 2. 注册脚本

```bash
cubqueue register --script /path/to/script.py --name my_script --desc "我的第一个脚本"
```

### 3. 提交任务

```bash
cubqueue submit --script my_script --arg-file /path/to/args.json --large-files /path/to/file1 --large-files /path/to/file2
```

### 4. 查看任务状态

```bash
# 查看所有任务
cubqueue list

# 查看特定任务状态
cubqueue status --task-id <task_id>

# 查看任务日志
cubqueue log --task-id <task_id>
```

## 使用方法

### 命令行工具

CubQueue提供了完整的命令行接口：

```bash
# 服务器管理
cubqueue start --base-dir /path/to/base/dir --host 127.0.0.1 --port 8000 --daemon
cubqueue stop --base-dir /path/to/base/dir

# 脚本管理
cubqueue register --script /path/to/script --name script_name --desc "description"
cubqueue namespace

# 任务管理
cubqueue submit --script script_name --arg-file /path/to/args.json --large-files /path/to/file1
cubqueue list
cubqueue status --task-id <task_id>
cubqueue log --task-id <task_id> --lines 100
cubqueue cancel --task-id <task_id>

# 文件下载
cubqueue download --task-id <task_id> --output-dir /path/to/output --metadata
cubqueue download --task-id <task_id> --output-dir /path/to/output --result
```

### Python客户端

```python
from cubqueue.client import CubQueueClient

# 创建客户端
client = CubQueueClient("http://localhost:8000")

# 注册脚本
client.register("my_script", "脚本描述", "/path/to/script.py")

# 查看已注册的脚本
scripts = client.list_scripts()

# 提交任务
task_id = client.submit_task("my_script", "/path/to/args.json", ["/path/to/file1"])

# 查看任务状态
status = client.get_task_status(task_id)

# 等待任务完成
result = client.wait_for_task(task_id)

# 查看任务日志
log_content = client.get_task_log(task_id, lines=100)

# 下载结果
client.download_task_result(task_id, "/path/to/output")
```

### RESTful API

CubQueue提供完整的RESTful API接口，详细文档请访问 `http://localhost:8000/docs`

## 工作目录结构

CubQueue使用以下目录结构：

```
base_dir/
├── scripts/                 # 注册的脚本文件
│   ├── script_name1.py
│   ├── script_name1.txt     # 脚本描述
│   └── ...
├── tasks/                   # 任务目录
│   ├── task_id1/
│   │   ├── files/           # 输入文件
│   │   ├── metadata/        # 中间文件
│   │   ├── output/          # 输出文件
│   │   ├── script_name.py   # 脚本副本
│   │   ├── arg_file.json    # 参数文件
│   │   └── log.txt          # 执行日志
│   └── ...
└── cubqueue.db              # SQLite数据库
```

## 脚本开发指南

### 环境变量

任务执行时，CubQueue会设置以下环境变量：

- `CUBQUEUE_TASK_ID`: 任务ID
- `CUBQUEUE_TASK_DIR`: 任务目录路径
- `CUBQUEUE_FILES_DIR`: 输入文件目录

注意：
- 脚本运行时的工作目录就是任务目录（`CUBQUEUE_TASK_DIR`）
- 输入文件路径在参数文件中已处理为相对路径（如 `files/uuid`），可直接使用
- 中间文件目录为 `metadata/`，输出文件目录为 `output/`
- 无需使用 `os.path.join` 拼接路径，直接使用相对路径即可

### 参数文件

参数文件使用JSON格式，支持文件占位符：

```json
{
    "input_files": ["<file1>", "<file2>"],
    "output_path": "result.txt",
    "parameters": {
        "threshold": 0.5,
        "iterations": 100
    }
}
```

### 示例脚本

```python
#!/usr/bin/env python3
import os
import json

# 读取参数文件
with open('arg_file.json', 'r') as f:
    args = json.load(f)

# 获取环境变量
task_id = os.environ['CUBQUEUE_TASK_ID']

# 处理输入文件（路径已经是相对路径）
input_files = args['input_files']
for file_path in input_files:
    print(f"处理文件: {file_path}")
    # 直接使用相对路径读取文件
    with open(file_path, 'r') as f:
        content = f.read()
        # 处理逻辑...

# 保存中间结果（使用相对路径）
with open('metadata/progress.txt', 'w') as f:
    f.write("处理进度: 50%")

# 保存最终结果（使用相对路径）
with open('output/result.txt', 'w') as f:
    f.write(content)
    f.write("任务完成")

print("任务执行完成")
```

## 配置

CubQueue支持通过环境变量或配置文件进行配置：

```bash
# 环境变量
export CUBQUEUE_BASE_DIR=/path/to/workspace
export CUBQUEUE_HOST=0.0.0.0
export CUBQUEUE_PORT=8000
export CUBQUEUE_MAX_CONCURRENT_TASKS=10
```

或创建 `.env` 文件：

```ini
CUBQUEUE_BASE_DIR=/path/to/workspace
CUBQUEUE_HOST=0.0.0.0
CUBQUEUE_PORT=8000
CUBQUEUE_MAX_CONCURRENT_TASKS=10
```

## 开发

### 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/cubqueue/cubqueue.git
cd cubqueue

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
pip install -e .
```

### 运行测试

```bash
pytest tests/
```

### 代码格式化

```bash
black cubqueue/
flake8 cubqueue/
```

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 贡献

欢迎提交Issue和Pull Request！

## 支持

如有问题，请提交Issue或联系开发团队。