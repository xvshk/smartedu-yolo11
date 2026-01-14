# -*- coding: utf-8 -*-
"""
检测模块 CLI 接口
处理检测相关的命令行参数和用户交互
符合Presentation层职责：仅处理用户交互，通过Service层访问业务逻辑
"""
import argparse
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.service import get_detection_service, configure_default_services


def create_detection_parser():
    """创建检测相关的命令行解析器"""
    parser = argparse.ArgumentParser(description='课堂行为检测系统 CLI')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 训练命令
    train_parser = subparsers.add_parser('train', help='训练模型')
    train_parser.add_argument('--data', required=True, help='训练数据路径')
    train_parser.add_argument('--epochs', type=int, default=100, help='训练轮数')
    train_parser.add_argument('--batch-size', type=int, default=16, help='批次大小')
    train_parser.add_argument('--output', default='./runs', help='输出目录')
    
    # 评估命令
    eval_parser = subparsers.add_parser('evaluate', help='评估模型')
    eval_parser.add_argument('--model', required=True, help='模型路径')
    eval_parser.add_argument('--data', required=True, help='测试数据路径')
    eval_parser.add_argument('--output', default='./evaluation', help='评估结果输出目录')
    
    # 检测命令
    detect_parser = subparsers.add_parser('detect', help='检测图像或视频')
    detect_parser.add_argument('--source', required=True, help='输入源（图像/视频路径）')
    detect_parser.add_argument('--model', required=True, help='模型路径')
    detect_parser.add_argument('--output', default='./detection_results', help='检测结果输出目录')
    detect_parser.add_argument('--conf', type=float, default=0.5, help='置信度阈值')
    
    return parser


def handle_train_command(args):
    """处理训练命令"""
    print(f"开始训练模型...")
    print(f"数据路径: {args.data}")
    print(f"训练轮数: {args.epochs}")
    print(f"批次大小: {args.batch_size}")
    print(f"输出目录: {args.output}")
    
    # 通过service层访问业务逻辑
    # TODO: 实现训练服务接口
    print("注意：训练功能需要通过Service层重构")
    print("✅ 训练命令已接收（待实现）")
    return 0


def handle_evaluate_command(args):
    """处理评估命令"""
    print(f"开始评估模型...")
    print(f"模型路径: {args.model}")
    print(f"测试数据: {args.data}")
    print(f"输出目录: {args.output}")
    
    # 通过service层访问业务逻辑
    # TODO: 实现评估服务接口
    print("注意：评估功能需要通过Service层重构")
    print("✅ 评估命令已接收（待实现）")
    return 0


def handle_detect_command(args):
    """处理检测命令"""
    print(f"开始检测...")
    print(f"输入源: {args.source}")
    print(f"模型路径: {args.model}")
    print(f"输出目录: {args.output}")
    print(f"置信度阈值: {args.conf}")
    
    try:
        # 配置服务容器
        configure_default_services()
        
        # 获取检测服务
        detection_service = get_detection_service()
        
        # TODO: 实现文件/视频检测接口
        print("注意：检测功能需要完善Service层接口")
        print("✅ 检测命令已接收（待实现）")
        return 0
        
    except Exception as e:
        print(f"❌ 检测失败: {e}")
        return 1
    
    try:
        # 这里应该调用检测业务逻辑
        # 暂时打印信息
        print("✅ 检测完成!")
        print(f"结果已保存到: {args.output}")
    except Exception as e:
        print(f"❌ 检测失败: {e}")
        return 1
    
    return 0


def main():
    """CLI 主入口"""
    parser = create_detection_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # 根据命令调用相应的处理函数
    if args.command == 'train':
        return handle_train_command(args)
    elif args.command == 'evaluate':
        return handle_evaluate_command(args)
    elif args.command == 'detect':
        return handle_detect_command(args)
    else:
        print(f"未知命令: {args.command}")
        return 1


if __name__ == '__main__':
    sys.exit(main())