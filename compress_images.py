#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import argparse
from PIL import Image


def compress_png(input_path, output_path, quality=50):
    """
    使用pngquant压缩PNG图片
    
    Args:
        input_path: 输入图片路径
        output_path: 输出图片路径
        quality: 压缩质量 (1-100)
    """
    try:
        # pngquant质量范围是0-100，使用两个值表示质量范围
        quality_min = max(quality - 10, 0)
        quality_max = quality
        
        # 调用pngquant命令
        result = subprocess.run(
            [
                'pngquant',
                '--quality', f'{quality_min}-{quality_max}',
                '--speed', '3',  # 中等速度，平衡压缩率和速度
                '--strip',
                '--force',
                '--output', output_path,
                input_path
            ],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            # 如果pngquant成功，再用optipng进行无损压缩优化
            subprocess.run(
                ['optipng', '-o2', '-strip', 'all', '-quiet', output_path],
                capture_output=True
            )
            print(f"PNG压缩成功: {os.path.basename(input_path)} -> {os.path.basename(output_path)}")
        else:
            print(f"PNG压缩失败 {os.path.basename(input_path)}: {result.stderr}")
    except Exception as e:
        print(f"PNG压缩失败 {os.path.basename(input_path)}: {e}")


def compress_jpeg(input_path, output_path, quality=50):
    """
    使用jpegoptim压缩JPEG图片
    
    Args:
        input_path: 输入图片路径
        output_path: 输出图片路径
        quality: 压缩质量 (1-100)
    """
    try:
        # 确保输入文件存在且不为空
        if not os.path.exists(input_path) or os.path.getsize(input_path) == 0:
            print(f"输入文件不存在或为空: {os.path.basename(input_path)}")
            return
            
        # 如果输入和输出路径不同，先复制文件
        if input_path != output_path:
            import shutil
            shutil.copy2(input_path, output_path)
        
        # 使用jpegoptim压缩文件
        result = subprocess.run(
            ['jpegoptim', '--strip-all', '--max', str(quality), '--force', '--quiet', output_path],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"JPEG压缩成功: {os.path.basename(input_path)} -> {os.path.basename(output_path)}")
        else:
            print(f"JPEG压缩失败 {os.path.basename(input_path)}: {result.stderr}")
            # 如果出现错误，确保删除可能生成的空文件
            if os.path.exists(output_path) and os.path.getsize(output_path) == 0:
                os.remove(output_path)
    except Exception as e:
        print(f"JPEG压缩失败 {os.path.basename(input_path)}: {e}")
        # 如果出现异常，确保删除可能生成的空文件
        if os.path.exists(output_path) and os.path.getsize(output_path) == 0:
            os.remove(output_path)


def resize_image(input_path, output_path, max_size=400):
    """
    调整图片尺寸并保持比例
    
    Args:
        input_path: 输入图片路径
        output_path: 输出图片路径
        max_size: 最大宽高限制 (px)
    """
    try:
        with Image.open(input_path) as img:
            # 计算新尺寸
            width, height = img.size
            if width <= max_size and height <= max_size:
                # 尺寸已合适，直接复制
                img.save(output_path, quality=85, optimize=True)
                return True
            
            # 计算缩放比例
            if width > height:
                new_width = max_size
                new_height = int((height / width) * max_size)
            else:
                new_height = max_size
                new_width = int((width / height) * max_size)
            
            # 调整尺寸
            resized_img = img.resize((new_width, new_height), Image.LANCZOS)
            
            # 保存调整后的图片
            resized_img.save(output_path, quality=85, optimize=True)
            print(f"图片调整尺寸成功: {os.path.basename(input_path)} -> {os.path.basename(output_path)}")
            return True
    except Exception as e:
        print(f"图片调整尺寸失败 {os.path.basename(input_path)}: {e}")
        return False


def compress_image(input_path, output_path, quality=50):
    """
    根据图片类型选择合适的压缩工具
    
    Args:
        input_path: 输入图片路径
        output_path: 输出图片路径
        quality: 压缩质量 (1-100)
    """
    # 获取文件扩展名
    ext = os.path.splitext(input_path)[1].lower()
    
    # 根据扩展名选择压缩工具
    if ext in ('.jpg', '.jpeg'):
        compress_jpeg(input_path, output_path, quality)
    elif ext == '.png':
        compress_png(input_path, output_path, quality)
    else:
        print(f"不支持的图片格式: {os.path.basename(input_path)}")


def process_images(input_dir, q50_dir, thumb_dir, quality=50, max_thumb_size=400):
    """
    处理图片：压缩到q50目录，同时生成缩略图到thumb目录
    
    Args:
        input_dir: 输入目录路径
        q50_dir: 高质量压缩输出目录路径
        thumb_dir: 缩略图输出目录路径
        quality: 压缩质量 (1-100)
        max_thumb_size: 缩略图最大宽高限制 (px)
    """
    # 支持的图片格式
    supported_formats = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
    
    # 创建输出目录
    for dir_path in [q50_dir, thumb_dir]:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"创建目录: {dir_path}")
    
    # 遍历输入目录
    for filename in os.listdir(input_dir):
        # 检查文件是否为图片
        if filename.lower().endswith(supported_formats):
            input_path = os.path.join(input_dir, filename)
            q50_path = os.path.join(q50_dir, filename)
            thumb_path = os.path.join(thumb_dir, filename)
            
            # 文件校验：如果q50和thumb目录都已有同名文件，则跳过
            if os.path.exists(q50_path) and os.path.exists(thumb_path):
                print(f"跳过已存在的文件: {filename}")
                continue
            
            try:
                # 如果q50目录没有该文件，进行压缩
                if not os.path.exists(q50_path):
                    print(f"处理高质量压缩: {filename}")
                    compress_image(input_path, q50_path, quality)
                
                # 如果thumb目录没有该文件，生成缩略图
                if not os.path.exists(thumb_path):
                    print(f"处理缩略图生成: {filename}")
                    # 先调整尺寸
                    resize_image(input_path, thumb_path, max_thumb_size)
                    # 再进行压缩优化
                    compress_image(thumb_path, thumb_path, quality)
            except Exception as e:
                print(f"处理文件失败 {filename}: {e}")


if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='图片批量压缩工具')
    parser.add_argument('-i', '--input', default='blog', help='输入图片目录 (默认: blog)')
    parser.add_argument('-q', '--quality', type=int, default=50, help='压缩质量 (1-100, 默认: 50)')
    parser.add_argument('-t', '--thumb-size', type=int, default=400, help='缩略图最大尺寸 (px, 默认: 400)')
    parser.add_argument('-f', '--fast', action='store_true', help='快速压缩模式 (默认: 平衡模式)')
    
    args = parser.parse_args()
    
    # 如果是快速模式，调整参数
    if args.fast:
        # 这里可以根据需要添加快速模式的参数调整
        print("使用快速压缩模式")
    
    # 定义输出目录
    q50_dir = 'q50'
    thumb_dir = 'thumb'
    
    # 处理图片
    process_images(args.input, q50_dir, thumb_dir, args.quality, args.thumb_size)