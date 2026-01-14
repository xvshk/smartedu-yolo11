#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
课堂行为检测系统 - 主程序入口
表现层 - 程序入口，用户交互
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.presentation.cli.detection_cli import main as cli_main
from backend.foundation.utils.logger import get_logger

logger = get_logger('main')


def main():
    """主程序入口"""
    logger.info("课堂行为检测系统启动")
    
    try:
        # 调用 CLI 主函数
        exit_code = cli_main()
        logger.info(f"程序执行完成，退出码: {exit_code}")
        return exit_code
    except KeyboardInterrupt:
        logger.info("用户中断程序执行")
        return 130
    except Exception as e:
        logger.error(f"程序执行出错: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())