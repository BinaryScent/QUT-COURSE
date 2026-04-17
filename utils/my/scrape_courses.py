"""
青岛理工大学教务系统课程爬取脚本
按学院、专业依次获取：专业列表、课程信息、培养方案
"""

import os
import json
import time
import requests
import sys
import base64
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5

# 获取脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ============ 配置区域 (请自行修改) ============
# 手动Cookie登录（可选，如果不提供学号密码则使用此方式）
# 登录后从浏览器开发者工具 → Application → Cookies 获取
JSESSIONID = ""
ROUTE = ""

# Cookie持久化文件路径（保存在脚本同级目录）
COOKIE_FILE = os.path.join(SCRIPT_DIR, "cookie.json")

# 输出目录（保存在脚本同级目录）
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "docs")

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


def save_cookies_to_file(jsessionid, route):
    """保存Cookie到文件"""
    cookie_data = {
        "JSESSIONID": jsessionid,
        "route": route,
        "update_time": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    os.makedirs(os.path.dirname(COOKIE_FILE), exist_ok=True)
    with open(COOKIE_FILE, "w", encoding="utf-8") as f:
        json.dump(cookie_data, f, ensure_ascii=False, indent=2)
    
    print(f"  ✓ Cookie已保存到: {COOKIE_FILE}")


def load_cookies_from_file():
    """从文件加载Cookie"""
    if not os.path.exists(COOKIE_FILE):
        return None, None
    
    try:
        with open(COOKIE_FILE, "r", encoding="utf-8") as f:
            cookie_data = json.load(f)
        
        jsessionid = cookie_data.get("JSESSIONID", "")
        route = cookie_data.get("route", "")
        update_time = cookie_data.get("update_time", "")
        
        if jsessionid and route:
            print(f"  → 从文件加载Cookie (更新时间: {update_time})")
            return jsessionid, route
        else:
            return None, None
    except Exception as e:
        print(f"  → 加载Cookie文件失败: {e}")
        return None, None


def b64tohex(b64str):
    """将Base64字符串转换为十六进制字符串"""
    return base64.b64decode(b64str).hex()


def hex2b64(hexstr):
    """将十六进制字符串转换为Base64字符串"""
    return base64.b64encode(bytes.fromhex(hexstr)).decode('utf-8')


def encrypt_password(password, modulus_b64, exponent_b64):
    """使用RSA加密密码"""
    # 将Base64格式的公钥参数转换为十六进制
    modulus_hex = b64tohex(modulus_b64)
    exponent_hex = b64tohex(exponent_b64)
    
    # 构建RSA公钥
    # n = modulus, e = exponent
    n = int(modulus_hex, 16)
    e = int(exponent_hex, 16)
    
    # 创建RSA公钥对象
    key = RSA.construct((n, e))
    
    # 使用PKCS#1 v1.5填充加密
    cipher = PKCS1_v1_5.new(key)
    
    # 加密密码（需要先编码为字节）
    password_bytes = password.encode('utf-8')
    encrypted = cipher.encrypt(password_bytes)
    
    # 转换为十六进制字符串
    encrypted_hex = encrypted.hex()
    
    # 转换为Base64（与JavaScript的hex2b64一致）
    encrypted_b64 = hex2b64(encrypted_hex)
    
    return encrypted_b64


def get_public_key(session):
    """从教务系统获取RSA公钥"""
    url = f"{BASE_URL}/xtgl/login_getPublicKey.html"
    params = {"time": str(int(time.time() * 1000))}
    
    try:
        resp = session.get(url, params=params)
        if resp.status_code == 200:
            data = resp.json()
            modulus = data.get("modulus", "")
            exponent = data.get("exponent", "")
            return modulus, exponent
        else:
            return None, None
    except Exception as e:
        print(f"  ✗ 获取公钥失败: {e}")
        return None, None


def login_to_system(username, password, debug=False):
    """通过学号和密码登录教务系统，获取Cookie"""
    print("\n正在登录教务系统...")
    
    session = requests.Session()
    session.headers.update(HEADERS)
    
    try:
        # 1. 获取RSA公钥
        print("  → 正在获取加密公钥...")
        modulus, exponent = get_public_key(session)
        
        if not modulus or not exponent:
            print("  ✗ 获取公钥失败")
            return None
        
        if debug:
            print(f"  → 公钥modulus: {modulus[:30]}...")
            print(f"  → 公钥exponent: {exponent}")
        
        # 2. 加密密码
        print("  → 正在加密密码...")
        encrypted_password = encrypt_password(password, modulus, exponent)
        
        if debug:
            print(f"  → 加密后密码: {encrypted_password[:30]}...")
        
        # 3. 访问登录页面获取csrftoken
        login_page_url = f"{BASE_URL}/xtgl/login_slogin.html"
        params = {"time": str(int(time.time() * 1000))}
        resp = session.get(login_page_url, params=params, allow_redirects=True)
        
        if debug:
            print(f"  → 登录页面状态码: {resp.status_code}")
        
        # 4. 提取csrftoken
        import re
        token_match = re.search(r'name="csrftoken"\s+value="([^"]+)"', resp.text)
        csrftoken = token_match.group(1) if token_match else None
        
        if not csrftoken:
            print("  ✗ 未找到csrftoken")
            return None
        
        if debug:
            print(f"  → csrftoken: {csrftoken[:20]}...")
        
        # 5. 构建登录请求
        login_url = f"{BASE_URL}/xtgl/login_slogin.html"
        login_params = {"time": str(int(time.time() * 1000))}
        
        login_data = {
            "csrftoken": csrftoken,
            "language": "zh_CN",
            "yhm": username,
            "mm": encrypted_password,  # 使用加密后的密码
        }
        
        if debug:
            print(f"  → 登录URL: {login_url}")
            print(f"  → URL参数: {login_params}")
            print(f"  → 表单数据: {list(login_data.keys())}")
        
        # 更新请求头
        session.headers.update({
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://jxgl.qut.edu.cn",
            "Referer": f"{login_url}?time={login_params['time']}",
        })
        
        resp = session.post(login_url, params=login_params, data=login_data, allow_redirects=False)
        
        if debug:
            print(f"  → 响应状态码: {resp.status_code}")
            print(f"  → 响应头: {dict(resp.headers)}")
            print(f"  → 响应长度: {len(resp.text)}")
            print(f"  → 登录后Cookies: {dict(session.cookies)}")
        
        # 6. 检查登录是否成功
        login_success = False
        
        # 方式1：检查重定向
        if resp.status_code in [301, 302, 303]:
            login_success = True
            print("✓ 检测到重定向，登录成功")
        
        # 方式2：检查Cookie
        jsessionid = session.cookies.get("JSESSIONID", "")
        route = session.cookies.get("route", "")
        
        if jsessionid and route:
            if debug:
                print(f"  → JSESSIONID: {jsessionid}")
                print(f"  → ROUTE: {route}")
            
            # 验证Cookie是否有效
            verify_url = f"{BASE_URL}/xtgl/index_initMenu.html"
            verify_resp = session.get(verify_url, allow_redirects=False)
            
            if debug:
                print(f"  → 验证请求状态码: {verify_resp.status_code}")
            
            if verify_resp.status_code == 200 and len(verify_resp.text) > 100:
                login_success = True
                print("✓ 登录验证成功！")
            else:
                print("✗ 登录验证失败")
        
        if login_success:
            print("\n获取到的Cookie信息：")
            print(f"  JSESSIONID: {jsessionid}")
            print(f"  ROUTE: {route}")
            
            # 保存Cookie到文件
            save_cookies_to_file(jsessionid, route)
            
            print("\n提示：Cookie已自动保存，下次可直接选择方式2使用")
            return session
        else:
            print("\n✗ 自动登录失败")
            print("\n建议：使用方式2手动获取Cookie")
            return None
            
    except Exception as e:
        print(f"✗ 登录过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_session(username=None, password=None):
    """创建带Cookie的会话"""
    # 如果提供了用户名和密码，尝试登录
    if username and password:
        session = login_to_system(username, password, True)
        if session:
            return session
        else:
            print("登录失败，程序退出")
            exit(1)
    
    # 否则使用手动配置的Cookie（兼容旧方式）
    print("\n使用手动配置的Cookie...")
    session = requests.Session()
    session.headers.update(HEADERS)

    # 设置多个Cookie
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

        # 检查非200状态码
        if resp.status_code != 200:
            print(f"    ✗ 请求失败，状态码: {resp.status_code}")
            print(f"    → 可能是Cookie已过期，请重新登录获取新的Cookie")
            return []

        # 检查是否返回 HTML 错误页面
        if "text/html" in content_type:
            import re
            match = re.search(r'错误提示</title>.*?<span[^>]*>(.*?)</span>', resp.text, re.DOTALL)
            if match:
                error_msg = match.group(1).strip()
            else:
                error_msg = resp.text[resp.text.find('<body'):resp.text.find('</body>')][:300] if '<body' in resp.text else resp.text[:300]
            print(f"    ✗ 返回了HTML页面而非JSON数据")
            print(f"    → 错误信息: {error_msg}")
            print(f"    → 可能是Cookie已过期或权限不足")
            return []

        # 检查响应内容是否为空
        if not resp.text or len(resp.text.strip()) == 0:
            print(f"    ✗ 响应内容为空")
            return []

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
    print("=" * 60)

    # 获取用户输入年级
    print("\n请输入要爬取的年级：")
    print("示例：2022、2023、2024")
    
    year_input = input("年级: ").strip()
    
    while not year_input or not year_input.isdigit() or len(year_input) != 4:
        print("错误：请输入有效的4位数字年份（如2022）！")
        year_input = input("请重新输入年级: ").strip()
    
    YEAR = int(year_input)
    print(f"\n已选择年级: {YEAR}")
    
    # 设置输出目录（带年级）
    OUTPUT_DIR = os.path.join(SCRIPT_DIR, "docs", f"{YEAR}级")
    print(f"输出目录: {OUTPUT_DIR}")

    # 获取用户输入
    print("\n请选择登录方式：")
    print("  1 - 输入学号和密码自动登录（推荐）")
    print("  2 - 从cookie.json文件加载Cookie")
    print("  3 - 使用脚本中配置的JSESSIONID和ROUTE")
    print("\n提示：")
    print("  - 方式1：自动获取Cookie，首次使用推荐")
    print("  - 方式2：使用通过方式1自动保存的Cookie，快捷方便")
    print("  - 方式3：需要在脚本第21-22行手动填写Cookie值")
    print("  - 如果教务系统有验证码，请选择方式2或3")
    
    choice = input("\n请输入选项数字 (1/2/3，默认为1): ").strip()
    
    # 如果用户直接回车，默认为1
    if choice == "":
        choice = "1"
    
    if choice == "1":
        print("\n" + "-" * 60)
        print("请输入你的教务系统登录信息：")
        print("-" * 60)
        
        username = input("学号: ").strip()
        
        while not username:
            print("错误：学号不能为空！")
            username = input("请重新输入学号: ").strip()
        
        print("\n现在输入密码：")
        print("提示：PyCharm控制台不支持密码隐藏，密码会明文显示")
        print("      输入完成后直接按回车键即可")
        password = input("密码: ").strip()
        
        while not password:
            print("错误：密码不能为空！")
            password = input("请重新输入密码: ").strip()
        
        print("\n正在验证登录信息...")
        session = get_session(username, password)
    elif choice == "2":
        # 从文件加载Cookie
        file_jsessionid, file_route = load_cookies_from_file()
        
        if file_jsessionid and file_route:
            print("\n使用从文件加载的Cookie登录...")
            JSESSIONID = file_jsessionid
            ROUTE = file_route
            session = get_session()
        else:
            print("\n错误：未找到有效的Cookie文件！")
            print("请先选择方式1登录获取Cookie")
            return
    elif choice == "3":
        # 使用脚本中配置的Cookie
        if JSESSIONID and ROUTE:
            print("\n使用脚本中配置的Cookie登录...")
            session = get_session()
        else:
            print("\n错误：脚本中的JSESSIONID和ROUTE未配置！")
            print("请在脚本第21-22行填写你的Cookie信息：")
            print("  JSESSIONID = \"你的JSESSIONID值\"")
            print("  ROUTE = \"你的ROUTE值\"")
            print("\n获取方法：")
            print("  1. 浏览器登录教务系统")
            print("  2. 按F12打开开发者工具")
            print("  3. Application → Cookies → 复制JSESSIONID和ROUTE")
            return
    else:
        print("\n错误：无效的选项！")
        print("请重新运行脚本，选择1、2或3")
        return

    # 遍历每个学院
    for college_name, jg_id in COLLEGES.items():
        print(f"\n【{college_name}】jg_id={jg_id}")

        # 获取专业列表
        majors = get_majors(session, jg_id, YEAR)

        if not majors:
            print(f"  ✗ 该学院没有找到 {YEAR} 级专业")
            continue

        # 创建学院目录（带年级）
        college_dir = os.path.join(OUTPUT_DIR, f"{college_name}-{YEAR}")
        os.makedirs(college_dir, exist_ok=True)

        # 遍历每个专业
        for major in majors:
            jxzxjhxx_id = major["jxzxjhxx_id"]
            zymc = major["zymc"]

            if not jxzxjhxx_id or not zymc:
                continue

            # 专业目录（带年级）
            major_dir = os.path.join(college_dir, f"{zymc}-{YEAR}")
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