# -*- coding: utf-8 -*-
"""
文件操作工具
基础层 - 纯工具，无业务逻辑
"""
import os
import json
import yaml
import pickle
from pathlib import Path
from typing import Any, Dict, List, Union


def ensure_dir(path: Union[str, Path]) -> Path:
    """确保目录存在"""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_json(file_path: Union[str, Path]) -> Dict[str, Any]:
    """加载 JSON 文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data: Dict[str, Any], file_path: Union[str, Path]) -> None:
    """保存数据到 JSON 文件"""
    ensure_dir(Path(file_path).parent)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_yaml(file_path: Union[str, Path]) -> Dict[str, Any]:
    """加载 YAML 文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def save_yaml(data: Dict[str, Any], file_path: Union[str, Path]) -> None:
    """保存数据到 YAML 文件"""
    ensure_dir(Path(file_path).parent)
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


def load_pickle(file_path: Union[str, Path]) -> Any:
    """加载 Pickle 文件"""
    with open(file_path, 'rb') as f:
        return pickle.load(f)


def save_pickle(data: Any, file_path: Union[str, Path]) -> None:
    """保存数据到 Pickle 文件"""
    ensure_dir(Path(file_path).parent)
    with open(file_path, 'wb') as f:
        pickle.dump(data, f)


def get_file_list(directory: Union[str, Path], 
                  extensions: List[str] = None,
                  recursive: bool = True) -> List[Path]:
    """获取目录下的文件列表"""
    directory = Path(directory)
    if not directory.exists():
        return []
    
    if extensions:
        extensions = [ext.lower() if ext.startswith('.') else f'.{ext.lower()}' 
                     for ext in extensions]
    
    files = []
    pattern = '**/*' if recursive else '*'
    
    for file_path in directory.glob(pattern):
        if file_path.is_file():
            if not extensions or file_path.suffix.lower() in extensions:
                files.append(file_path)
    
    return sorted(files)


def get_file_size(file_path: Union[str, Path]) -> int:
    """获取文件大小（字节）"""
    return Path(file_path).stat().st_size


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"