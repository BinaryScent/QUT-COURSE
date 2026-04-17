"""
青岛理工大学教务系统课程爬取脚本
按学院、专业依次获取：专业列表、课程信息、培养方案
"""

import os
import json
import time
import requests

# ============ 配置区域 (请自行修改) ============
# Cookie 登录（推荐）
# 登录后从浏览器开发者工具 → Application → Cookies 获取
JSESSIONID = "E67D5EB697D86BA16A6E35E05F0F9F44"
ROUTE = "4326bf261f250634ec9b0cb30239b1ab"

# 目标年级
YEAR = 2022

# 输出目录
OUTPUT_DIR = "./utils/my/docs"

# =========================================

# 学院配置 (jg_id)
COLLEGES = {
    "机械与汽车工程学院": "06",
    "建筑与城乡规划学院": "03",
    "环境与市政工程学院": "05",
    "信息与控制工程学院": "07",
    "理学院": "01",
    "商学院": "23",
    "人文与外国语学院": "08",
    "管理工程学院": "22",
    "城市建设学院": "4C02691300EFD7BAE0633203060A5DE2",
    "艺术与设计学院": "10",
    "信息管理学院": "4C0305FB530BDCD9E0633203060A9199",
}

# 基础配置
BASE_URL = "https://jxgl.qut.edu.cn/jwglxt"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "https://jxgl.qut.edu.cn",
    "Referer": "https://jxgl.qut.edu.cn/jwglxt/jxzxjhgl/jxzxjhck_cxJxzxjhckIndex.html?gnmkdm=N153540&layout=default",
}


def get_session():
    """创建带 Cookie 的会话"""
    session = requests.Session()
    session.headers.update(HEADERS)

    # 设置多个 Cookie
    if JSESSIONID:
        session.cookies.set("JSESSIONID", JSESSIONID)
    if ROUTE:
        session.cookies.set("route", ROUTE)

    # 先访问主页，建立会话
    try:
        session.get(f"{BASE_URL}/xtgl/index.html")
        session.get(f"{BASE_URL}/jxzxjhgl/jxzxjhck_cxJxzxjhckIndex.html")
    except:
        pass

    return session


def get_majors(session, jg_id, year=2022):
    """获取专业列表"""
    url = f"{BASE_URL}/jxzxjhgl/jxzxjhck_cxJxzxjhckIndex.html"
    params = {
        "doType": "query",
        "gnmkdm": "N153540",
    }

    data = {
        "jg_id": jg_id,
        "njdm_id": str(year),
        "dlbs": "",
        "zyh_id": "",
        "currentPage_cx": "",
        "_search": "false",
        "nd": str(int(time.time() * 1000)),
        "queryModel.showCount": "15",
        "queryModel.currentPage": "1",
        "queryModel.sortName": "",
        "queryModel.sortOrder": "asc",
        "time": "1"
    }

    try:
        resp = session.post(url, params=params, data=data)
        content_type = resp.headers.get('Content-Type', '')

        # 检查是否返回 HTML 错误页面
        if "text/html" in content_type:
            import re
            match = re.search(r'错误提示</title>.*?<span[^>]*>(.*?)</span>', resp.text, re.DOTALL)
            if match:
                error_msg = match.group(1).strip()
            else:
                error_msg = resp.text[resp.text.find('<body'):resp.text.find('</body>')][:300] if '<body' in resp.text else resp.text[:300]
            print(f"    DEBUG: 错误页面内容: {error_msg}")
            return []

        print(f"    DEBUG: status={resp.status_code}, content_type={content_type}")
        result = resp.json()

        items = result.get("items", [])
        majors = []
        for item in items:
            majors.append({
                "jxzxjhxx_id": item.get("jxzxjhxx_id", ""),
                "zymc": item.get("zymc", "").strip()
            })

        print(f"  → 获取到 {len(majors)} 个专业")
        return majors
    except Exception as e:
        print(f"  ✗ 获取专业列表失败: {e}")
        return []


def get_courses_by_major(session, jxzxjhxx_id):
    """获取课程信息（分页）"""
    url = f"{BASE_URL}/jxzxjhgl/jxzxjhkcxx_cxJxzxjhkcxxIndex.html"
    params = {
        "doType": "query",
        "gnmkdm": "N153540",
    }

    all_courses = []
    page = 1
    page_size = 15

    while True:
        data = {
            "jyxdxnm": "",
            "jyxdxqm": "",
            "yxxdxnm": "",
            "yxxdxqm": "",
            "shzt": "",
            "kch": "",
            "jxzxjhxx_id": jxzxjhxx_id,
            "xdlx": "",
            "_search": "false",
            "nd": str(int(time.time() * 1000)),
            "queryModel.showCount": str(page_size),
            "queryModel.currentPage": str(page),
            "queryModel.sortName": "jyxdxnm,jyxdxqm,kch",
            "queryModel.sortOrder": "asc",
            "time": "2"
        }

        try:
            resp = session.post(url, params=params, data=data)
            result = resp.json()

            items = result.get("items", [])
            if not items:
                break

            all_courses.extend(items)

            # 检查是否还有更多页
            total = result.get("totalResult", 0)
            if len(all_courses) >= total:
                break

            page += 1
            time.sleep(0.3)  # 避免请求过快

        except Exception as e:
            print(f"    ✗ 第 {page} 页获取失败: {e}")
            break

    return all_courses


def download_training_plan(session, jxzxjhxx_id, save_path):
    """下载培养方案 PDF"""
    url = f"{BASE_URL}/jxzxjhgl/jxzxjhxxwh_cxDyJxzxjhxx.html"
    params = {
        "jxzxjhxx_id": jxzxjhxx_id,
        "gnmkdm": "N153540",
    }

    try:
        resp = session.get(url, params=params, allow_redirects=True)

        # 检查是否是 PDF
        content_type = resp.headers.get("Content-Type", "")
        if "pdf" in content_type.lower() or resp.headers.get("Content-Disposition", ""):
            # 确保目录存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            with open(save_path, "wb") as f:
                f.write(resp.content)

            print(f"    ✓ 培养方案已保存: {save_path}")
            return True
        else:
            # 可能返回的是 HTML（登录过期等）
            print(f"    ✗ 培养方案下载失败，可能是登录过期")
            print(f"      响应类型: {content_type}")
            return False

    except Exception as e:
        print(f"    ✗ 培养方案下载失败: {e}")
        return False


def save_json(data, filepath):
    """保存 JSON 文件"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    print("=" * 60)
    print("青岛理工大学 - 教务系统课程爬取")
    print(f"目标年级: {YEAR}")
    print(f"输出目录: {OUTPUT_DIR}")
    print("=" * 60)

    session = get_session()

    # 遍历每个学院
    for college_name, jg_id in COLLEGES.items():
        print(f"\n【{college_name}】jg_id={jg_id}")

        # 获取专业列表
        majors = get_majors(session, jg_id, YEAR)

        if not majors:
            print(f"  ✗ 该学院没有找到 {YEAR} 级专业")
            continue

        # 创建学院目录
        college_dir = os.path.join(OUTPUT_DIR, college_name)
        os.makedirs(college_dir, exist_ok=True)

        # 遍历每个专业
        for major in majors:
            jxzxjhxx_id = major["jxzxjhxx_id"]
            zymc = major["zymc"]

            if not jxzxjhxx_id or not zymc:
                continue

            # 专业目录
            major_dir = os.path.join(college_dir, zymc)
            os.makedirs(major_dir, exist_ok=True)

            print(f"  └─ {zymc}")

            # 1. 获取课程信息
            print(f"      → 获取课程信息...")
            courses = get_courses_by_major(session, jxzxjhxx_id)
            print(f"      → 共 {len(courses)} 门课程")

            # 保存课程 JSON
            if courses:
                courses_path = os.path.join(major_dir, "courses.json")
                save_json(courses, courses_path)
                print(f"      ✓ 课程已保存")
            else:
                print(f"      ✗ 无课程数据")

            # 2. 下载培养方案
            print(f"      → 下载培养方案...")
            pdf_path = os.path.join(major_dir, "培养方案.pdf")
            download_training_plan(session, jxzxjhxx_id, pdf_path)

            # 避免请求过快
            time.sleep(0.5)

    print("\n" + "=" * 60)
    print("完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()