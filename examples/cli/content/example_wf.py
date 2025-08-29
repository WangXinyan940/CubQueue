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
content_list = []
for file_path in input_files:
    print(f"处理文件: {file_path}")
    # 直接使用相对路径读取文件
    with open(file_path, 'r') as f:
        content = f.read()
        content_list.append(content)
        # 处理逻辑...

# 保存中间结果（使用相对路径）
with open('metadata/progress.txt', 'w') as f:
    f.write(content_list[0])
    f.write("处理进度: 50%")

# 保存最终结果（使用相对路径）
with open('output/result.txt', 'w') as f:
    f.write(content_list[1])
    f.write("任务完成")

print("任务执行完成")