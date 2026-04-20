#!/usr/bin/env python3
# coding: utf-8
"""
生成青岛理工大学课程资源前端页面
"""
import os
import json
import shutil
import time
from pathlib import Path, PurePosixPath
from urllib.parse import quote


RAW_BASE = "https://raw.githubusercontent.com/BinaryScent/QUT-COURSE/main"


def log(msg):
    print(msg, flush=True)


def to_posix(path_obj):
    return PurePosixPath(path_obj).as_posix()


def raw_url(repo_relative_path):
    return RAW_BASE + "/" + quote(to_posix(repo_relative_path), safe="/")


def collect_courses_from_dirs(courses_dir):
    courses_by_college = {}

    if not courses_dir.exists():
        log(f"  courses 目录不存在: {courses_dir}")
        return courses_by_college

    college_dirs = [d for d in courses_dir.iterdir() if d.is_dir()]
    log(f"  发现 {len(college_dirs)} 个学院目录")

    for college_dir in college_dirs:
        college_name = college_dir.name
        courses_by_college[college_name] = {}

        course_dirs = [d for d in college_dir.iterdir() if d.is_dir()]
        log(f"  学院 [{college_name}]: {len(course_dirs)} 个课程目录")

        for course_dir in course_dirs:
            dir_name = course_dir.name
            course_name = dir_name
            courses_by_college[college_name][course_name] = {
                "resources": {
                    "homeworks": [],
                    "labs": [],
                    "exams": [],
                    "notes": []
                }
            }

            for res_type in ['homeworks', 'labs', 'exams', 'notes']:
                res_dir = course_dir / res_type
                if res_dir.exists():
                    files = [f for f in res_dir.iterdir() if f.is_file() and not f.name.startswith('.')]
                    for f in files:
                        rel_path = f.relative_to(courses_dir)
                        courses_by_college[college_name][course_name]["resources"][res_type].append({
                            "name": f.name,
                            "description": "",
                            "url": raw_url(Path("courses") / rel_path)
                        })

    return courses_by_college


def collect_major_info(docs_dir):
    """收集专业和培养方案信息，新结构：学院 -> 专业 -> plans[]"""
    colleges_data = {}

    if not docs_dir.exists():
        log(f"  docs 目录不存在: {docs_dir}")
        return colleges_data

    grade_dirs = [d for d in sorted(docs_dir.iterdir()) if d.is_dir() and d.name.endswith('级')]
    log(f"  发现 {len(grade_dirs)} 个年级目录: {[d.name for d in grade_dirs]}")

    total_majors = 0
    total_courses = 0

    for grade_dir in grade_dirs:
        grade = grade_dir.name
        college_dirs = [d for d in grade_dir.iterdir() if d.is_dir()]
        log(f"  [{grade}] {len(college_dirs)} 个学院")

        for college_dir in college_dirs:
            college_name = college_dir.name.rsplit('-', 1)[0]

            if college_name not in colleges_data:
                colleges_data[college_name] = {
                    "id": college_name,
                    "name": college_name,
                    "majors": {},
                    "courses": {}
                }

            major_dirs = [d for d in college_dir.iterdir() if d.is_dir()]
            for major_dir in major_dirs:
                major_name = major_dir.name.rsplit('-', 1)[0]

                if major_name not in colleges_data[college_name]["majors"]:
                    colleges_data[college_name]["majors"][major_name] = {
                        "id": major_name,
                        "name": major_name,
                        "plans": []
                    }

                plan_file = ""
                for f in major_dir.iterdir():
                    if f.is_file() and f.name == "培养方案.pdf":
                        rel_path = f.relative_to(docs_dir.parent)
                        plan_file = raw_url(Path("utils") / "data" / rel_path)
                        break

                if plan_file:
                    colleges_data[college_name]["majors"][major_name]["plans"].append({
                        "grade": grade,
                        "file": plan_file
                    })

                courses_json = major_dir / "courses.json"
                if courses_json.exists():
                    try:
                        with open(courses_json, 'r', encoding='utf-8') as f:
                            course_list = json.load(f)
                        if isinstance(course_list, list):
                            for course in course_list:
                                course_name = course.get('kcmc', '')
                                course_type = course.get('kclbmc', '未分类')

                                if course_name:
                                    if course_name not in colleges_data[college_name]["courses"]:
                                        colleges_data[college_name]["courses"][course_name] = {
                                            "id": course_name,
                                            "name": course_name,
                                            "type": course_type,
                                            "resources": {
                                                "homeworks": [],
                                                "labs": [],
                                                "exams": [],
                                                "notes": []
                                            }
                                        }
                                        total_courses += 1
                    except Exception as e:
                        log(f"  警告: 解析 {courses_json} 失败: {e}")

                total_majors += 1

    log(f"  共收集 {total_majors} 个专业条目, {total_courses} 门课程")

    for college_name, college in colleges_data.items():
        college["majors"] = list(college["majors"].values())
        college["courses"] = list(college["courses"].values())

    return colleges_data


def merge_data(colleges_data, courses_by_college):
    """合并课程资源到新结构，支持跨学院匹配"""
    merged_count = 0
    total_courses = 0
    
    all_course_resources = {}
    for college_name, college_courses in courses_by_college.items():
        for course_name, course_data in college_courses.items():
            if course_name not in all_course_resources:
                all_course_resources[course_name] = course_data["resources"]
    
    for college_name, college in colleges_data.items():
        for course in college["courses"]:
            course_name = course["name"]
            total_courses += 1
            
            if course_name in all_course_resources:
                course["resources"] = all_course_resources[course_name]
                merged_count += 1

    log(f"  合并了 {merged_count}/{total_courses} 门课程的资源")

    result = {
        "colleges": list(colleges_data.values())
    }
    return result


def copy_web_files(web_src, web_dest):
    dest_dir = Path(web_dest)
    dest_dir.mkdir(parents=True, exist_ok=True)

    src_dir = Path(web_src)
    if src_dir.exists():
        files = [f for f in src_dir.iterdir() if f.is_file()]
        log(f"  复制 {len(files)} 个文件: {web_src} -> {web_dest}")
        for f in files:
            shutil.copy2(f, dest_dir / f.name)
            log(f"    {f.name}")

        dirs = [d for d in src_dir.iterdir() if d.is_dir()]
        for d in dirs:
            dest_sub = dest_dir / d.name
            if dest_sub.exists():
                shutil.rmtree(dest_sub)
            shutil.copytree(d, dest_sub)
            log(f"    目录: {d.name}/")


def copy_dir_with_progress(src, dest, label):
    if dest.exists():
        log(f"  清理旧目录: {dest}")
        shutil.rmtree(dest)

    if not src.exists():
        log(f"  源目录不存在，跳过: {src}")
        return

    file_count = sum(1 for _ in src.rglob('*') if _.is_file())
    log(f"  复制 {label}: {src} -> {dest} ({file_count} 个文件)")

    copied = 0
    def copy_func(src_file, dst_file):
        nonlocal copied
        shutil.copy2(src_file, dst_file)
        copied += 1
        if copied % 50 == 0 or copied == file_count:
            log(f"    进度: {copied}/{file_count}")

    shutil.copytree(src, dest, copy_function=copy_func)
    log(f"  {label} 复制完成: {copied} 个文件")


def main():
    base_dir = Path(__file__).parent.parent
    docs_dir = base_dir / 'utils' / 'data' / 'docs'
    web_src = base_dir / 'web'
    web_dest = base_dir / 'docs'
    courses_dir = base_dir / 'courses'

    log("=" * 50)
    log("青岛理工大学课程资源 - 前端页面生成")
    log("=" * 50)
    log(f"项目根目录: {base_dir}")
    log(f"docs 目录:   {docs_dir}")
    log(f"courses 目录: {courses_dir}")
    log(f"输出目录:    {web_dest}")
    log("")

    t0 = time.time()

    log("[1/4] 收集课程资源...")
    t1 = time.time()
    courses_by_college = collect_courses_from_dirs(courses_dir)
    log(f"  耗时: {time.time() - t1:.2f}s")
    log("")

    log("[2/4] 收集专业信息...")
    t2 = time.time()
    colleges_data = collect_major_info(docs_dir)
    log(f"  耗时: {time.time() - t2:.2f}s")
    log("")

    log("[3/4] 合并数据...")
    t3 = time.time()
    course_data = merge_data(colleges_data, courses_by_college)
    log(f"  耗时: {time.time() - t3:.2f}s")
    log("")

    log("[4/4] 生成 data.js...")
    t4 = time.time()
    data_js = web_src / 'data.js'
    with open(data_js, 'w', encoding='utf-8') as f:
        f.write(f"const qutData = {json.dumps(course_data, ensure_ascii=False, indent=2)};\n")
        f.write("\nlet currentCollege = null;\n")
        f.write("let currentGrade = null;\n")
        f.write("let currentMajor = null;\n")
        f.write("let currentCourse = null;\n")
    data_js_size = data_js.stat().st_size
    log(f"  data.js 大小: {data_js_size / 1024:.1f} KB")

    copy_web_files(str(web_src), str(web_dest))
    log(f"  耗时: {time.time() - t4:.2f}s")
    log("")

    total_time = time.time() - t0
    log("=" * 50)
    log(f"生成完成！总耗时: {total_time:.2f}s")
    log(f"目标目录: {web_dest}")
    log(f"学院数: {len(course_data['colleges'])}")
    log("=" * 50)
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
