"""
课程目录创建脚本
自动扫描 docs 目录下所有 courses.json 文件，按学院和课程创建目录结构
"""

import os
import json
from pathlib import Path

# 默认子目录
SUBDIRS = ['homeworks', 'labs', 'exams', 'notes']

# 配置路径
SCRIPT_DIR = Path(__file__).parent
DOCS_DIR = SCRIPT_DIR / 'docs'
COURSE_ROOT = SCRIPT_DIR.parent.parent  # 项目根目录

# Windows 文件名非法字符
INVALID_CHARS = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']


def sanitize_filename(name):
    """清理文件名中的非法字符"""
    for char in INVALID_CHARS:
        name = name.replace(char, '')
    return name.strip()


def find_all_json_files(docs_dir):
    """递归查找所有 courses.json 文件"""
    json_files = []
    for root, dirs, files in os.walk(docs_dir):
        for file in files:
            if file == 'courses.json':
                json_files.append(os.path.join(root, file))
    return json_files


def parse_json_files(json_files):
    """解析所有 JSON 文件，提取课程信息"""
    courses_data = []
    
    for json_file in json_files:
        print(f"正在解析: {json_file}")
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                for item in data:
                    college = item.get('kkbmmc', '').strip()
                    course_type = item.get('kclbmc', '').strip()
                    course_name = item.get('kcmc', '').strip()
                    
                    if college and course_name:
                        courses_data.append({
                            'college': college,
                            'course_type': course_type if course_type else '未分类',
                            'course_name': course_name
                        })
            else:
                print(f"  警告: {json_file} 不是列表格式，跳过")
                
        except json.JSONDecodeError as e:
            print(f"  错误: JSON 解析失败 - {e}")
        except Exception as e:
            print(f"  错误: 读取文件失败 - {e}")
    
    return courses_data


def create_course_directories(courses_data, course_root, subdirs):
    """按学院和课程创建目录结构（增量模式）"""
    # 按学院分组，去重
    college_courses = {}
    for course_info in courses_data:
        college = course_info['college']
        if college not in college_courses:
            college_courses[college] = set()
        
        # 课程目录名：课程名称-课程类型（清理非法字符）
        course_dir_name = sanitize_filename(f"{course_info['course_name']}-{course_info['course_type']}")
        college_courses[college].add(course_dir_name)
    
    # 统计
    total_colleges = len(college_courses)
    total_courses = sum(len(courses) for courses in college_courses.values())
    new_colleges = 0
    new_courses = 0
    skipped_colleges = 0
    skipped_courses = 0
    
    print(f"\n共找到 {total_colleges} 个学院，{total_courses} 门课程\n")
    
    for college, courses in sorted(college_courses.items()):
        college_dir = os.path.join(course_root, college)
        college_exists = os.path.exists(college_dir)
        
        if college_exists:
            skipped_colleges += 1
            print(f"【{college}】(已存在，检查新课程...)")
        else:
            new_colleges += 1
            print(f"【{college}】(新学院)")
        
        for course_dir_name in sorted(courses):
            course_path = os.path.join(college_dir, course_dir_name)
            
            # 检查课程目录是否已存在
            if os.path.exists(course_path):
                skipped_courses += 1
                print(f"  ○ {course_dir_name}/ (已存在，跳过)")
                continue
            
            # 创建新课程目录
            os.makedirs(course_path, exist_ok=True)
            
            # 创建子目录并添加 .gitkeep 文件
            for subdir in subdirs:
                subdir_path = os.path.join(course_path, subdir)
                os.makedirs(subdir_path, exist_ok=True)
                
                # 创建 .gitkeep 文件使 Git 跟踪空目录
                gitkeep_path = os.path.join(subdir_path, '.gitkeep')
                if not os.path.exists(gitkeep_path):
                    with open(gitkeep_path, 'w', encoding='utf-8') as f:
                        pass  # 创建空文件
            
            new_courses += 1
            print(f"  ✓ {course_dir_name}/ (新建)")
    
    return {
        'total_colleges': total_colleges,
        'total_courses': total_courses,
        'new_colleges': new_colleges,
        'new_courses': new_courses,
        'skipped_colleges': skipped_colleges,
        'skipped_courses': skipped_courses
    }


def main():
    print("=" * 60)
    print("课程目录创建工具")
    print("=" * 60)
    
    # 检查 docs 目录是否存在
    if not os.path.exists(DOCS_DIR):
        print(f"错误: 找不到 docs 目录: {DOCS_DIR}")
        return
    
    # 查找所有 JSON 文件
    print(f"\n正在扫描: {DOCS_DIR}")
    json_files = find_all_json_files(DOCS_DIR)
    
    if not json_files:
        print("未找到任何 courses.json 文件")
        return
    
    print(f"找到 {len(json_files)} 个 courses.json 文件\n")
    
    # 解析 JSON 文件
    courses_data = parse_json_files(json_files)
    
    if not courses_data:
        print("未提取到任何课程数据")
        return
    
    # 输入子目录配置
    subdirs_input = input(f"\n子目录（空格分隔，默认: {' '.join(SUBDIRS)}): ").strip()
    if subdirs_input:
        subdirs = subdirs_input.split()
    else:
        subdirs = SUBDIRS
    
    # 输入课程根目录
    root_input = input(f"\n课程根目录（默认: {COURSE_ROOT}）: ").strip()
    if root_input:
        course_root = root_input
    else:
        course_root = str(COURSE_ROOT)
    
    # 创建目录
    print("\n" + "=" * 60)
    print("开始创建目录...")
    print("=" * 60 + "\n")
    
    stats = create_course_directories(courses_data, course_root, subdirs)
    
    print("\n" + "=" * 60)
    print("完成！统计信息：")
    print(f"  总学院数: {stats['total_colleges']}")
    print(f"  总课程数: {stats['total_courses']}")
    print(f"  新建学院: {stats['new_colleges']}")
    print(f"  新建课程: {stats['new_courses']}")
    print(f"  跳过学院: {stats['skipped_colleges']}")
    print(f"  跳过课程: {stats['skipped_courses']}")
    print(f"保存位置: {course_root}")
    print("=" * 60)


if __name__ == "__main__":
    main()