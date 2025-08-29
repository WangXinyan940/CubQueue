#!/usr/bin/env python3
"""CubQueue命令行工具主入口"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Optional

from ..client import CubQueueClient
from ..core.config import get_config
from ..server.daemon import DaemonManager

# 版本信息
__version__ = "1.0.0"


def cmd_start(args):
    """启动CubQueue服务器"""
    try:
        daemon_manager = DaemonManager(args.base_dir, args.host, args.port)
        if args.daemon:
            daemon_manager.start_daemon()
            print(f"CubQueue守护进程已启动 (http://{args.host}:{args.port})")
        else:
            daemon_manager.start_server()
    except Exception as e:
        print(f"启动失败: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_stop(args):
    """停止CubQueue服务器"""
    try:
        daemon_manager = DaemonManager(args.base_dir)
        daemon_manager.stop_daemon()
        print("CubQueue服务器已停止")
    except Exception as e:
        print(f"停止失败: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_register(args):
    """注册脚本"""
    try:
        client = CubQueueClient(f"http://{args.host}:{args.port}")
        client.register(args.name, args.desc, args.script)
        print(f"脚本 '{args.name}' 注册成功")
    except Exception as e:
        print(f"注册失败: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_namespace(args):
    """查看已注册的脚本"""
    try:
        client = CubQueueClient(f"http://{args.host}:{args.port}")
        scripts = client.namespace()
        if scripts:
            print("已注册的脚本:")
            for script in scripts:
                print(f"  - {script['name']}: {script['description']}")
        else:
            print("暂无已注册的脚本")
    except Exception as e:
        print(f"查询失败: {e}", file=sys.stderr)
        sys.exit(1)

def cmd_list(args):
    """查看任务列表"""
    print("查看任务列表...")
    try:
        client = CubQueueClient(f"http://{args.host}:{args.port}")
        tasks = client.list_tasks()
        if tasks:
            print("任务列表:")
            for task in tasks:
                print(
                    f"  - {task['id']}: {task['script_name']} ({task['status']})"
                )
        else:
            print("暂无任务")
    except Exception as e:
        print(f"查询失败: {e}", file=sys.stderr)
        sys.exit(1)

def cmd_submit(args):
    """提交任务"""
    try:
        print("提交任务...")
        client = CubQueueClient(f"http://{args.host}:{args.port}")
        print(f"提交任务: {args.script}")
        large_files = args.large_files if args.large_files else []
        task_id = client.submit_task(args.script, args.arg_file, large_files)
        print(f"任务提交成功，任务ID: {task_id}")
    except Exception as e:
        print(f"提交失败: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_status(args):
    """查看任务状态"""
    try:
        client = CubQueueClient(f"http://{args.host}:{args.port}")
        task_status = client.get_task_status(args.task_id)
        print(f"任务 {args.task_id} 状态: {task_status['status']}")
        if "message" in task_status:
            print(f"消息: {task_status['message']}")
    except Exception as e:
        print(f"查询失败: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_log(args):
    """查看任务日志"""
    try:
        client = CubQueueClient(f"http://{args.host}:{args.port}")
        log_content = client.get_task_log(args.task_id, args.lines)
        print(log_content)
    except Exception as e:
        print(f"查询失败: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_download(args):
    """下载任务文件"""
    try:
        client = CubQueueClient(f"http://{args.host}:{args.port}")
        if args.metadata:
            client.download_task_metadata(args.task_id, args.output_dir)
            print(f"中间文件已下载到: {args.output_dir}")
        if args.result:
            client.download_task_result(args.task_id, args.output_dir)
            print(f"结果文件已下载到: {args.output_dir}")
        if not args.metadata and not args.result:
            print("请指定 --metadata 或 --result 参数")
    except Exception as e:
        print(f"下载失败: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_cancel(args):
    """取消任务"""
    try:
        client = CubQueueClient(f"http://{args.host}:{args.port}")
        client.cancel_task(args.task_id)
        print(f"任务 {args.task_id} 已取消")
    except Exception as e:
        print(f"取消失败: {e}", file=sys.stderr)
        sys.exit(1)


def create_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        prog='cubqueue',
        description='CubQueue - 轻量级任务监控系统'
    )
    parser.add_argument('--version', action='version', version=f'cubqueue {__version__}')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # start 命令
    start_parser = subparsers.add_parser('start', help='启动CubQueue服务器')
    start_parser.add_argument('--base-dir', required=True, help='工作目录路径')
    start_parser.add_argument('--host', default='127.0.0.1', help='服务器主机地址')
    start_parser.add_argument('--port', type=int, default=8000, help='服务器端口')
    start_parser.add_argument('--daemon', action='store_true', help='以守护进程模式启动')
    start_parser.set_defaults(func=cmd_start)
    
    # stop 命令
    stop_parser = subparsers.add_parser('stop', help='停止CubQueue服务器')
    stop_parser.add_argument('--base-dir', required=True, help='工作目录路径')
    stop_parser.set_defaults(func=cmd_stop)
    
    # register 命令
    register_parser = subparsers.add_parser('register', help='注册脚本')
    register_parser.add_argument('--script', required=True, help='脚本文件路径')
    register_parser.add_argument('--name', required=True, help='脚本名称')
    register_parser.add_argument('--desc', required=True, help='脚本描述')
    register_parser.add_argument('--host', default='127.0.0.1', help='服务器主机地址')
    register_parser.add_argument('--port', type=int, default=8000, help='服务器端口')
    register_parser.set_defaults(func=cmd_register)
    
    # namespace 命令
    namespace_parser = subparsers.add_parser('namespace', help='查看已注册的脚本')
    namespace_parser.add_argument('--host', default='127.0.0.1', help='服务器主机地址')
    namespace_parser.add_argument('--port', type=int, default=8000, help='服务器端口')
    namespace_parser.set_defaults(func=cmd_namespace)
    
    # list 命令
    list_parser = subparsers.add_parser('list', help='查看任务列表')
    list_parser.add_argument('--host', default='127.0.0.1', help='服务器主机地址')
    list_parser.add_argument('--port', type=int, default=8000, help='服务器端口')
    list_parser.set_defaults(func=cmd_list)
    
    # submit 命令
    submit_parser = subparsers.add_parser('submit', help='提交任务')
    submit_parser.add_argument('--script', required=True, help='脚本名称')
    submit_parser.add_argument('--arg-file', required=True, help='参数文件路径')
    submit_parser.add_argument('--large-files', action='append', help='大文件路径（可多次使用）')
    submit_parser.add_argument('--host', default='127.0.0.1', help='服务器主机地址')
    submit_parser.add_argument('--port', type=int, default=8000, help='服务器端口')
    submit_parser.set_defaults(func=cmd_submit)
    
    # status 命令
    status_parser = subparsers.add_parser('status', help='查看任务状态')
    status_parser.add_argument('--task-id', required=True, help='任务ID')
    status_parser.add_argument('--host', default='127.0.0.1', help='服务器主机地址')
    status_parser.add_argument('--port', type=int, default=8000, help='服务器端口')
    status_parser.set_defaults(func=cmd_status)
    
    # log 命令
    log_parser = subparsers.add_parser('log', help='查看任务日志')
    log_parser.add_argument('--task-id', required=True, help='任务ID')
    log_parser.add_argument('--lines', type=int, default=100, help='显示的日志行数')
    log_parser.add_argument('--host', default='127.0.0.1', help='服务器主机地址')
    log_parser.add_argument('--port', type=int, default=8000, help='服务器端口')
    log_parser.set_defaults(func=cmd_log)
    
    # download 命令
    download_parser = subparsers.add_parser('download', help='下载任务文件')
    download_parser.add_argument('--task-id', required=True, help='任务ID')
    download_parser.add_argument('--output-dir', required=True, help='输出目录')
    download_parser.add_argument('--metadata', action='store_true', help='下载中间文件')
    download_parser.add_argument('--result', action='store_true', help='下载结果文件')
    download_parser.add_argument('--host', default='127.0.0.1', help='服务器主机地址')
    download_parser.add_argument('--port', type=int, default=8000, help='服务器端口')
    download_parser.set_defaults(func=cmd_download)
    
    # cancel 命令
    cancel_parser = subparsers.add_parser('cancel', help='取消任务')
    cancel_parser.add_argument('--task-id', required=True, help='任务ID')
    cancel_parser.add_argument('--host', default='127.0.0.1', help='服务器主机地址')
    cancel_parser.add_argument('--port', type=int, default=8000, help='服务器端口')
    cancel_parser.set_defaults(func=cmd_cancel)
    
    return parser


def main():
    """主入口函数"""
    parser = create_parser()
    args = parser.parse_args()
    
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
