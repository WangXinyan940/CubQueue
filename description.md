# CubQueue项目描述

CubQueue是一个Python构建的、轻量级的任务监控系统，使用命令行工具与RESTFul API交互，支持注册给定script，而后基于这些script提交任务，并管理它们产出的log、中间文件与结果文件。

## CubQueue的命令行使用

### 启动守护进程

```bash
# 以守护进程模式启动
cubqueue start --base-dir /path/to/base/dir --host 127.0.0.1 --port 8000 --daemon

# 或者前台运行
cubqueue start --base-dir /path/to/base/dir --host 127.0.0.1 --port 8000
```

### 关闭守护进程

```bash
cubqueue stop --base-dir /path/to/base/dir
```

### 注册script

```bash
cubqueue register --script /path/to/script --name script_name --desc "script description"
```

注意script name需要是唯一的，且只能包含字母、数字与下划线。

### 查看注册的script

```bash
cubqueue namespace
```

### 提交任务

```bash
cubqueue submit --script script_name --arg-file /path/to/arg/file.json --large-files /path/to/file1 --large-files /path/to/file2
```
其中--large-files参数用于指定需要上传到CubQueue服务器的大文件，每个文件需要单独使用--large-files参数指定。这些文件会被上传到CubQueue服务器的一个独立文件夹中，拥有各自的uuid。任务运行时可以通过arg file中的占位符（<file1>、<file2>等）识别它们。

一个arg file例子：

```json
{
    "polymers": ["<file1>", "<file2>"],
    "ligand": "<file3>",
    "other_arg1": "other_value1",
    "other_arg2": "other_value2"
}
```

### 查看任务列表

```bash
cubqueue list
```

### 查看任务状态

```bash
cubqueue status --task-id task_id
```

### 查看任务log 

```bash
cubqueue log --task-id task_id --lines 100
```

注意：--lines参数默认为100行，可以根据需要调整。

### 下载任务中间文件夹

```bash
cubqueue download --task-id task_id --output-dir /path/to/output/dir --metadata
```

### 下载任务结果文件

```bash
cubqueue download --task-id task_id --output-dir /path/to/output/dir --result
```

### 取消任务

```bash
cubqueue cancel --task-id task_id
```

## CubQueue的RESTFul API使用

### 注册script

```python
requests.post(
    "http://localhost:8000/api/script",
    data={
        "name": "script_name",
        "desc": "script description"
    },
    files={
        "script": open("/path/to/script", "rb")
    }
)
```

### 查看注册的script

```python
requests.get("http://localhost:8000/api/script")
```

### 提交任务

```python
requests.post(
    "http://localhost:8000/api/task",
    data={
        "script_name": "script_name"
    },
    files={
        "arg_file": open("/path/to/arg/file.json", "rb"),
        "file1": open("/path/to/file1", "rb"),
        "file2": open("/path/to/file2", "rb")
    }
)
```

### 查看任务列表

```python
requests.get("http://localhost:8000/api/task")
```

### 查看任务状态

```python
requests.get("http://localhost:8000/api/task/task_id")
```

### 查看任务log

```python
requests.get("http://localhost:8000/api/task/task_id/log")
```

### 下载任务中间文件夹

```python
requests.get("http://localhost:8000/api/task/task_id/metadata")
```

### 下载任务结果文件

```python
requests.get("http://localhost:8000/api/task/task_id/result")
```

### 取消任务

```python
requests.delete("http://localhost:8000/api/task/task_id")
```

## CubQueue的Python Client API使用

基于RESTFul API的Python Client

```python
from cubqueue.client import CubQueueClient

# 创建客户端
client = CubQueueClient("http://localhost:8000")

# 注册script
client.register("script_name", "script description", "/path/to/script")

# 查看注册的script
scripts = client.list_scripts()

# 提交任务
task_id = client.submit_task("script_name", "/path/to/arg/file.json", ["/path/to/file1", "/path/to/file2"])

# 查看任务列表
tasks = client.list_tasks()

# 查看任务状态
status = client.get_task_status(task_id)

# 查看任务log
log_content = client.get_task_log(task_id, lines=100)

# 下载任务中间文件夹
client.download_task_metadata(task_id, "/path/to/output/dir")

# 下载任务结果文件
client.download_task_result(task_id, "/path/to/output/dir")

# 取消任务
client.cancel_task(task_id)

# 等待任务完成（如果需要）
result = client.wait_for_task(task_id)
```

## CubQueue工作目录的设计规范

工作目录下有如下文件夹：
```
base_dir/
├── scripts/
│   ├── script_name1.py
│   ├── script_name1.txt
│   ├── script_name2.py
│   ├── script_name2.txt
├── tasks/
│   ├── task_id1/
│   │   ├── files/
│   │   │   ├── file1
│   │   │   ├── file2
│   │   ├── metadata/
│   │   ├── output/
│   │   ├── script_name1.py
│   │   ├── arg_file.json
│   │   ├── log.txt
│   ├── task_id2/
├── cubqueue.db
```

- scripts文件夹用于存储注册的script，每个script对应一个.py文件与一个.txt文件，.py文件为script的实际代码，.txt文件为script的描述。
- tasks文件夹用于存储提交的任务，每个任务对应一个文件夹，文件夹名即为任务的id。
- cubqueue.db为CubQueue的数据库文件，用于存储任务的元数据。

## CubQueue内任务的设计规范

一个任务由一个script、一个arg file、三个文件夹（files、metadata、output）组成。
- script：任务运行时使用的script，是注册时script的拷贝。
- arg file：任务运行时使用的参数文件，是提交时上传的arg file的拷贝。
- files文件夹：用于存储任务提交时上传的大文件，每个文件对应一个uuid。
- metadata文件夹：用于存储任务中间产生的元数据。
- output文件夹：用于存储任务的结果文件。
