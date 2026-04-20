"""
课程目录创建脚本
自动扫描 docs 目录下所有 courses.json 文件，按学院和课程创建目录结构
支持增量扫描：基于文件内容哈希缓存，避免重复读取（跨用户共享）
"""

import os
import json
import hashlib
import argparse
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime

# 默认子目录
SUBDIRS = ['homeworks', 'labs', 'exams', 'notes']

# 配置路径
SCRIPT_DIR = Path(__file__).parent
DOCS_DIR = SCRIPT_DIR / 'docs'
COURSE_ROOT = SCRIPT_DIR.parent.parent / 'courses'  # 项目根目录
CACHE_FILE = SCRIPT_DIR / '.scan_cache.json'  # 扫描缓存文件
LOG_DIR = SCRIPT_DIR / 'logs'  # 日志目录
DETAIL_LOG = LOG_DIR / 'create_course.log'  # 详细日志文件
HISTORY_LOG = LOG_DIR / 'run_history.json'  # 运行历史文件

# Windows 文件名非法字符
INVALID_CHARS = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']


def sanitize_filename(name):
    """清理文件名中的非法字符"""
    for char in INVALID_CHARS:
        name = name.replace(char, '')
    return name.strip()


def setup_logging():
    """配置日志系统"""
    # 创建日志目录
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # 创建 logger
    logger = logging.getLogger('create_course')
    logger.setLevel(logging.DEBUG)
    
    # 避免重复添加 handler
    if logger.handlers:
        return logger
    
    # 详细日志 - 文件输出（带轮转）
    file_handler = RotatingFileHandler(
        DETAIL_LOG,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # 控制台输出
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('[%(levelname)s] %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger


def save_run_history(history_data):
    """保存运行历史到 JSON 文件"""
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # 读取现有历史记录
    history = []
    if os.path.exists(HISTORY_LOG):
        try:
            with open(HISTORY_LOG, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except (json.JSONDecodeError, Exception):
            history = []
    
    # 添加新记录
    history.append(history_data)
    
    # 只保留最近 100 条记录
    if len(history) > 100:
        history = history[-100:]
    
    # 保存
    with open(HISTORY_LOG, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def load_scan_cache():
    """加载扫描缓存"""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, Exception):
            return {}
    return {}


def save_scan_cache(cache_data):
    """保存扫描缓存"""
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)


def compute_file_hash(file_path):
    """计算文件内容的 MD5 哈希值"""
    md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            md5.update(chunk)
    return md5.hexdigest()


def filter_files_by_hash(json_files, cache, force=False):
    """根据文件内容哈希过滤文件，返回需要处理的文件列表"""
    if force:
        return json_files, len(json_files), 0
    
    new_or_modified = []
    skipped = 0
    
    for json_file in json_files:
        file_hash = compute_file_hash(json_file)
        cached_hash = cache.get(json_file)
        
        if cached_hash is None or file_hash != cached_hash:
            new_or_modified.append(json_file)
        else:
            skipped += 1
    
    return new_or_modified, len(new_or_modified), skipped


def scan_available_grades(docs_dir):
    """扫描可用的年级列表"""
    grades = []
    if not os.path.exists(docs_dir):
        return grades
    
    for item in sorted(os.listdir(docs_dir)):
        item_path = os.path.join(docs_dir, item)
        if os.path.isdir(item_path) and '级' in item:
            grades.append(item)
    
    return grades


def find_all_json_files(docs_dir, selected_grades=None):
    """递归查找所有 courses.json 文件
    
    Args:
        docs_dir: 文档根目录
        selected_grades: 可选，要扫描的年级列表。如果为None则扫描所有年级
    """
    json_files = []
    
    for root, dirs, files in os.walk(docs_dir):
        # 如果指定了年级，只扫描选中的年级目录
        if selected_grades:
            # 获取当前目录相对于docs_dir的路径
            rel_path = os.path.relpath(root, docs_dir)
            
            if rel_path == '.':
                # 在根目录，过滤掉未选中的年级目录，防止os.walk进入
                dirs[:] = [d for d in dirs if d in selected_grades]
            elif os.sep not in rel_path:
                # 这是年级目录，检查是否需要扫描
                if rel_path not in selected_grades:
                    # 不进入未选中的年级目录
                    del dirs[:]
                    continue
        
        for file in files:
            if file == 'courses.json':
                json_files.append(os.path.join(root, file))
    
    return json_files


def parse_json_files(json_files, cache):
    """解析所有 JSON 文件，提取课程信息"""
    courses_data = []
    processed_files = {}
    
    for json_file in json_files:
        print(f"正在解析: {json_file}")
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 记录文件内容哈希到缓存
            file_hash = compute_file_hash(json_file)
            processed_files[json_file] = file_hash
            
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
    
    return courses_data, processed_files


def create_course_directories(courses_data, course_root, subdirs, logger=None):
    """按学院和课程创建目录结构（增量模式）"""
    # 按学院分组，去重
    college_courses = {}
    for course_info in courses_data:
        college = course_info['college']
        if college not in college_courses:
            college_courses[college] = set()
        
        # 课程目录名：课程名称（清理非法字符）
        course_dir_name = sanitize_filename(course_info['course_name'])
        college_courses[college].add(course_dir_name)
    
    # 统计
    total_colleges = len(college_courses)
    total_courses = sum(len(courses) for courses in college_courses.values())
    new_colleges = 0
    new_courses = 0
    skipped_colleges = 0
    skipped_courses = 0
    new_college_names = []
    new_course_names = []
    
    print(f"\n共找到 {total_colleges} 个学院，{total_courses} 门课程\n")
    if logger:
        logger.info(f"共找到 {total_colleges} 个学院，{total_courses} 门课程")
    
    for college, courses in sorted(college_courses.items()):
        college_dir = os.path.join(course_root, college)
        college_exists = os.path.exists(college_dir)
        
        if college_exists:
            skipped_colleges += 1
            print(f"【{college}】(已存在，检查新课程...)")
        else:
            new_colleges += 1
            new_college_names.append(college)
            print(f"【{college}】(新学院)")
            if logger:
                logger.info(f"新建学院: {college}")
        
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
            new_course_names.append(course_dir_name)
            print(f"  [+] {course_dir_name}/ (新建)")
            if logger:
                logger.info(f"新建课程: {course_dir_name}")
    
    return {
        'total_colleges': total_colleges,
        'total_courses': total_courses,
        'new_colleges': new_colleges,
        'new_courses': new_courses,
        'skipped_colleges': skipped_colleges,
        'skipped_courses': skipped_courses,
        'new_college_names': new_college_names,
        'new_course_names': new_course_names
    }


def select_grades_interactive(grades):
    """交互式选择年级
    
    Returns:
        list: 选中的年级列表，如果选择全部则返回None
    """
    print("\n" + "=" * 60)
    print("年级选择")
    print("=" * 60)
    print(f"\n可用年级（共 {len(grades)} 个）:")
    for i, grade in enumerate(grades, 1):
        print(f"  {i}. {grade}")
    print(f"  0. 全部年级")
    
    while True:
        choice = input("\n请选择年级（输入编号，多个年级用空格分隔，直接回车选择全部）: ").strip()
        
        # 直接回车或输入0，选择全部
        if not choice or choice == '0':
            print("已选择: 全部年级")
            return None
        
        # 解析输入的编号
        try:
            indices = [int(x) for x in choice.split()]
            
            # 验证编号范围
            valid_indices = [i for i in indices if 1 <= i <= len(grades)]
            
            if not valid_indices:
                print(f"错误: 请输入 1-{len(grades)} 之间的数字")
                continue
            
            # 检查是否有无效编号
            invalid_indices = [i for i in indices if i < 0 or i > len(grades)]
            if invalid_indices:
                print(f"警告: 编号 {invalid_indices} 无效，已忽略")
            
            selected = [grades[i-1] for i in valid_indices]
            print(f"已选择: {', '.join(selected)}")
            return selected
            
        except ValueError:
            print("错误: 请输入有效的数字")


def main():
    parser = argparse.ArgumentParser(description='课程目录创建工具')
    parser.add_argument('--force', '-f', action='store_true', help='强制重新扫描所有文件（忽略缓存）')
    parser.add_argument('--clear-cache', action='store_true', help='清除缓存后退出')
    parser.add_argument('--year', '-y', nargs='+', help='指定要扫描的年级（如: --year 2022级 2023级）')
    parser.add_argument('--non-interactive', '-n', action='store_true', help='非交互式运行，使用默认配置')
    parser.add_argument('--subdirs', nargs='+', help='自定义子目录（如: --subdirs homeworks labs exams notes）')
    parser.add_argument('--root', help='课程根目录')
    args = parser.parse_args()
    
    # 初始化日志系统
    logger = setup_logging()
    
    # 清除缓存模式
    if args.clear_cache:
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)
            logger.info("已清除缓存文件")
            print(f"已清除缓存文件: {CACHE_FILE}")
        else:
            print("缓存文件不存在")
        return
    
    logger.info("=" * 40)
    logger.info("脚本启动")
    logger.info(f"命令行参数: force={args.force}, year={args.year}")
    
    print("=" * 60)
    print("课程目录创建工具")
    print("=" * 60)
    
    # 检查 docs 目录是否存在
    if not os.path.exists(DOCS_DIR):
        logger.error(f"找不到 docs 目录: {DOCS_DIR}")
        print(f"错误: 找不到 docs 目录: {DOCS_DIR}")
        return
    
    # 扫描可用年级
    available_grades = scan_available_grades(DOCS_DIR)
    
    if not available_grades:
        logger.error("未找到任何年级目录")
        print("错误: 未找到任何年级目录")
        return
    
    logger.info(f"可用年级: {', '.join(available_grades)}")
    
    # 确定要扫描的年级
    selected_grades = None
    
    if args.year:
        # 命令行指定了年级
        selected_grades = args.year
        print(f"\n命令行指定年级: {', '.join(selected_grades)}")
        logger.info(f"命令行指定年级: {', '.join(selected_grades)}")
        
        # 验证年级是否存在
        valid_grades = [g for g in selected_grades if g in available_grades]
        invalid_grades = [g for g in selected_grades if g not in available_grades]
        
        if invalid_grades:
            logger.warning(f"以下年级不存在: {', '.join(invalid_grades)}")
            print(f"警告: 以下年级不存在: {', '.join(invalid_grades)}")
        
        if not valid_grades:
            logger.error("指定的年级都不存在")
            print("错误: 指定的年级都不存在")
            return
        
        selected_grades = valid_grades
    elif args.non_interactive:
        # 非交互式，选择全部年级
        selected_grades = None
        print(f"\n非交互式模式: 选择全部年级")
        logger.info(f"非交互式模式: 选择全部年级")
    else:
        # 交互式选择年级
        selected_grades = select_grades_interactive(available_grades)
        logger.info(f"选择年级: {', '.join(selected_grades) if selected_grades else '全部年级'}")
    
    # 加载缓存
    cache = load_scan_cache()
    logger.info(f"缓存加载完成，共 {len(cache)} 条记录")
    
    # 查找 JSON 文件（根据选择的年级）
    print(f"\n正在扫描: {DOCS_DIR}")
    if selected_grades:
        print(f"扫描范围: {', '.join(selected_grades)}")
    
    json_files = find_all_json_files(DOCS_DIR, selected_grades)
    logger.info(f"扫描完成，找到 {len(json_files)} 个 courses.json 文件")
    
    if not json_files:
        logger.warning("未找到任何 courses.json 文件")
        print("未找到任何 courses.json 文件")
        return
    
    print(f"找到 {len(json_files)} 个 courses.json 文件\n")
    
    # 根据文件内容哈希过滤文件
    files_to_process, new_count, skipped_count = filter_files_by_hash(json_files, cache, args.force)
    
    if skipped_count > 0 and not args.force:
        logger.info(f"缓存命中: {skipped_count} 个文件未修改，已跳过")
        print(f"缓存命中: {skipped_count} 个文件未修改，已跳过")
    
    if not files_to_process:
        logger.info("所有文件都已处理过，无需重复扫描")
        print("所有文件都已处理过，无需重复扫描")
        print(f"使用 --force 参数可强制重新扫描")
        return
    
    logger.info(f"需要处理: {new_count} 个文件")
    print(f"需要处理: {new_count} 个文件\n")
    
    # 解析 JSON 文件
    courses_data, processed_files = parse_json_files(files_to_process, cache)
    logger.info(f"解析完成，提取 {len(courses_data)} 条课程数据")
    
    if not courses_data:
        logger.warning("未提取到任何课程数据")
        print("未提取到任何课程数据")
        return
    
    # 更新缓存
    cache.update(processed_files)
    save_scan_cache(cache)
    logger.info(f"缓存已更新: {len(processed_files)} 条记录")
    print(f"\n缓存已更新: {CACHE_FILE}")
    
    # 输入子目录配置
    if args.subdirs:
        subdirs = args.subdirs
        print(f"\n命令行指定子目录: {' '.join(subdirs)}")
        logger.info(f"命令行指定子目录: {' '.join(subdirs)}")
    elif args.non_interactive:
        subdirs = SUBDIRS
        print(f"\n非交互式模式: 使用默认子目录 {' '.join(subdirs)}")
        logger.info(f"非交互式模式: 使用默认子目录 {' '.join(subdirs)}")
    else:
        subdirs_input = input(f"\n子目录（空格分隔，默认: {' '.join(SUBDIRS)}): ").strip()
        if subdirs_input:
            subdirs = subdirs_input.split()
        else:
            subdirs = SUBDIRS
    
    # 输入课程根目录
    if args.root:
        course_root = args.root
        print(f"\n命令行指定课程根目录: {course_root}")
        logger.info(f"命令行指定课程根目录: {course_root}")
    elif args.non_interactive:
        course_root = str(COURSE_ROOT)
        print(f"\n非交互式模式: 使用默认课程根目录 {course_root}")
        logger.info(f"非交互式模式: 使用默认课程根目录 {course_root}")
    else:
        root_input = input(f"\n课程根目录（默认: {COURSE_ROOT}）: ").strip()
        if root_input:
            course_root = root_input
        else:
            course_root = str(COURSE_ROOT)
    
    # 创建目录
    print("\n" + "=" * 60)
    print("开始创建目录...")
    print("=" * 60 + "\n")
    
    logger.info("开始创建目录")
    stats = create_course_directories(courses_data, course_root, subdirs, logger)
    
    # 保存运行历史
    history_data = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'selected_grades': selected_grades if selected_grades else ['全部年级'],
        'total_files': len(json_files),
        'cached_files': skipped_count,
        'processed_files': new_count,
        'total_colleges': stats['total_colleges'],
        'total_courses': stats['total_courses'],
        'new_colleges': stats['new_colleges'],
        'new_courses': stats['new_courses'],
        'skipped_colleges': stats['skipped_colleges'],
        'skipped_courses': stats['skipped_courses'],
        'new_college_names': stats['new_college_names'],
        'new_course_names': stats['new_course_names'],
        'course_root': course_root,
        'subdirs': subdirs
    }
    save_run_history(history_data)
    logger.info("运行历史已保存")
    
    print("\n" + "=" * 60)
    print("完成！统计信息：")
    print(f"  扫描年级: {', '.join(selected_grades) if selected_grades else '全部年级'}")
    print(f"  扫描文件: {new_count} 个新增/修改，{skipped_count} 个跳过")
    print(f"  总学院数: {stats['total_colleges']}")
    print(f"  总课程数: {stats['total_courses']}")
    print(f"  新建学院: {stats['new_colleges']}")
    print(f"  新建课程: {stats['new_courses']}")
    print(f"  跳过学院: {stats['skipped_colleges']}")
    print(f"  跳过课程: {stats['skipped_courses']}")
    print(f"保存位置: {course_root}")
    print("=" * 60)
    
    logger.info(f"脚本完成 - 总学院: {stats['total_colleges']}, 总课程: {stats['total_courses']}, 新建学院: {stats['new_colleges']}, 新建课程: {stats['new_courses']}")


if __name__ == "__main__":
    main()