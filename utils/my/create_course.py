"""
简单的课程目录创建脚本
"""

import os
import json

# 默认子目录
SUBDIRS = ['homeworks', 'labs', 'exams', 'notes']

def main():
    print("=" * 40)
    
    # 从 JSON 文件读取数据
    json_file = input("请输入 JSON 文件路径 (默认: './utils/my/docs/courses.json'): ").strip()
    if not json_file:
        json_file = './utils/my/docs/courses.json'
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"错误: 找不到文件 {json_file}")
        return
    except json.JSONDecodeError as e:
        print(f"错误: JSON 解析失败 - {e}")
        return
    
    # 输入子目录配置
    subdirs_input = input(f"子目录（空格分隔，默认: {' '.join(SUBDIRS)}): ").strip()
    if subdirs_input:
        subdirs = subdirs_input.split()
    else:
        subdirs = SUBDIRS
    
    # 按学院分组创建目录
    for item in data:
        college = item.get('kkbmmc', '').strip()
        course_name = item.get('kcmc', '').strip()
        
        if not college or not course_name:
            print(f"警告: 跳过无效数据 - {item}")
            continue
        
        # 构建路径
        course_path = os.path.join(COURSE_ROOT, college, course_name)
        
        # 创建目录
        print(f"\n创建课程目录: {course_path}")
        os.makedirs(course_path, exist_ok=True)
        
        # 创建课程子目录
        for subdir in subdirs:
            dir_path = os.path.join(course_path, subdir)
            os.makedirs(dir_path, exist_ok=True)
            print(f"  ✓ {subdir}/")

if __name__ == "__main__":
    # 设置课程根目录
    COURSE_ROOT = input("请输入课程根目录路径 (默认: .): ").strip()
    if not COURSE_ROOT:
        COURSE_ROOT = "."
    
    main()