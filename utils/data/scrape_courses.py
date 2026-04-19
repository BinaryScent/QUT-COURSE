"""
青岛理工大学教务系统课程爬取脚本

功能说明：
    按学院、专业依次获取专业列表、课程信息和培养方案PDF。
    支持三种登录方式：
        1. 学号密码自动登录（RSA加密）
        2. 从cookie.json文件加载Cookie
        3. 使用脚本中配置的Cookie

使用方法：
    python scrape_courses.py
"""

import os
import re
import json
import time
import base64
from typing import Optional, Dict, List, Tuple

import requests
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5

# ============================================
# 配置区域
# ============================================

# 脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 手动Cookie配置（方式3使用）
# 获取方法：浏览器登录 → F12 → Application → Cookies
JSESSIONID = ""
ROUTE = ""

# Cookie持久化文件路径
COOKIE_FILE = os.path.join(SCRIPT_DIR, "cookie.json")

# 学院配置 (名称: jg_id)
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
    "Referer": f"{BASE_URL}/jxzxjhgl/jxzxjhck_cxJxzxjhckIndex.html?gnmkdm=N153540&layout=default",
}

# 请求配置
REQUEST_TIMEOUT = 30  # 请求超时时间（秒）
PAGE_SIZE = 15  # 分页查询每页条数
REQUEST_DELAY = 0.3  # 请求间隔（秒）
VERIFY_TEXT_MIN_LENGTH = 100  # 验证响应最小长度

# ============================================


def save_cookies_to_file(jsessionid: str, route: str) -> None:
    """
    保存Cookie到JSON文件

    Args:
        jsessionid: JSESSIONID Cookie值
        route: ROUTE Cookie值
    """
    cookie_data = {
        "JSESSIONID": jsessionid,
        "route": route,
        "update_time": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    os.makedirs(os.path.dirname(COOKIE_FILE), exist_ok=True)
    with open(COOKIE_FILE, "w", encoding="utf-8") as f:
        json.dump(cookie_data, f, ensure_ascii=False, indent=2)

    print(f"  ✓ Cookie已保存到: {COOKIE_FILE}")


def load_cookies_from_file() -> Tuple[Optional[str], Optional[str]]:
    """
    从JSON文件加载Cookie

    Returns:
        (jsessionid, route) 元组，加载失败返回 (None, None)
    """
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
        return None, None
    except Exception as e:
        print(f"  → 加载Cookie文件失败: {e}")
        return None, None


def b64tohex(b64str: str) -> str:
    """
    将Base64字符串转换为十六进制字符串

    Args:
        b64str: Base64编码字符串

    Returns:
        十六进制字符串
    """
    return base64.b64decode(b64str).hex()


def hex2b64(hexstr: str) -> str:
    """
    将十六进制字符串转换为Base64字符串

    Args:
        hexstr: 十六进制字符串

    Returns:
        Base64编码字符串
    """
    return base64.b64encode(bytes.fromhex(hexstr)).decode('utf-8')


def encrypt_password(password: str, modulus_b64: str, exponent_b64: str) -> str:
    """
    使用RSA公钥加密密码（PKCS#1 v1.5填充）

    Args:
        password: 明文密码
        modulus_b64: Base64编码的RSA模数
        exponent_b64: Base64编码的RSA指数

    Returns:
        Base64编码的加密密码
    """
    modulus_hex = b64tohex(modulus_b64)
    exponent_hex = b64tohex(exponent_b64)

    n = int(modulus_hex, 16)
    e = int(exponent_hex, 16)

    key = RSA.construct((n, e))
    cipher = PKCS1_v1_5.new(key)

    encrypted = cipher.encrypt(password.encode('utf-8'))

    return hex2b64(encrypted.hex())


def get_public_key(session: requests.Session) -> Tuple[Optional[str], Optional[str]]:
    """
    从教务系统获取RSA公钥参数

    Args:
        session: requests会话对象

    Returns:
        (modulus, exponent) 元组，获取失败返回 (None, None)
    """
    url = f"{BASE_URL}/xtgl/login_getPublicKey.html"
    params = {"time": str(int(time.time() * 1000))}

    try:
        resp = session.get(url, params=params, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("modulus"), data.get("exponent")
        return None, None
    except Exception as e:
        print(f"  ✗ 获取公钥失败: {e}")
        return None, None


def extract_csrf_token(session: requests.Session, debug: bool = False) -> Optional[str]:
    """
    访问登录页面提取CSRF Token

    Args:
        session: requests会话对象
        debug: 是否开启调试模式

    Returns:
        CSRF Token字符串，提取失败返回None
    """
    login_page_url = f"{BASE_URL}/xtgl/login_slogin.html"
    params = {"time": str(int(time.time() * 1000))}

    try:
        resp = session.get(login_page_url, params=params, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        
        if debug:
            print(f"  → 登录页面状态码: {resp.status_code}")
        
        token_match = re.search(r'name="csrftoken"\s+value="([^"]+)"', resp.text)
        return token_match.group(1) if token_match else None
    except Exception as e:
        print(f"  ✗ 获取CSRF Token失败: {e}")
        return None


def verify_login(session: requests.Session, debug: bool = False) -> bool:
    """
    验证登录是否成功

    Args:
        session: requests会话对象
        debug: 是否开启调试模式

    Returns:
        登录验证是否成功
    """
    verify_url = f"{BASE_URL}/xtgl/index_initMenu.html"
    try:
        resp = session.get(verify_url, timeout=REQUEST_TIMEOUT, allow_redirects=False)
        
        if debug:
            print(f"  → 验证请求状态码: {resp.status_code}")
        
        return resp.status_code == 200 and len(resp.text) > VERIFY_TEXT_MIN_LENGTH
    except Exception:
        return False


def login_to_system(username: str, password: str, debug: bool = False) -> Optional[requests.Session]:
    """
    通过学号和密码登录教务系统

    登录流程：
        1. 获取RSA公钥
        2. 加密密码
        3. 获取CSRF Token
        4. 发送登录请求
        5. 验证登录结果

    Args:
        username: 学号
        password: 密码
        debug: 是否开启调试模式

    Returns:
        登录成功的Session对象，失败返回None
    """
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

        # 3. 获取CSRF Token
        print("  → 正在获取CSRF Token...")
        csrftoken = extract_csrf_token(session, debug)

        if not csrftoken:
            print("  ✗ 未找到CSRF Token")
            return None

        if debug:
            print(f"  → csrftoken: {csrftoken[:20]}...")

        # 4. 发送登录请求
        login_url = f"{BASE_URL}/xtgl/login_slogin.html"
        login_params = {"time": str(int(time.time() * 1000))}

        login_data = {
            "csrftoken": csrftoken,
            "language": "zh_CN",
            "yhm": username,
            "mm": encrypted_password,
        }

        session.headers.update({
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://jxgl.qut.edu.cn",
            "Referer": f"{login_url}?time={login_params['time']}",
        })

        if debug:
            print(f"  → 登录URL: {login_url}")
            print(f"  → URL参数: {login_params}")
            print(f"  → 表单数据: {list(login_data.keys())}")

        resp = session.post(
            login_url,
            params=login_params,
            data=login_data,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=False
        )

        if debug:
            print(f"  → 响应状态码: {resp.status_code}")
            print(f"  → 响应头: {dict(resp.headers)}")
            print(f"  → 响应长度: {len(resp.text)}")
            print(f"  → 登录后Cookies: {dict(session.cookies)}")

        # 5. 检查登录结果
        login_success = resp.status_code in [301, 302, 303]

        if not login_success:
            jsessionid = session.cookies.get("JSESSIONID", "")
            route = session.cookies.get("route", "")

            if jsessionid and route:
                if debug:
                    print(f"  → JSESSIONID: {jsessionid}")
                    print(f"  → ROUTE: {route}")
                login_success = verify_login(session, debug)

        if login_success:
            jsessionid = session.cookies.get("JSESSIONID", "")
            route = session.cookies.get("route", "")

            print("\n✓ 登录成功！")
            print(f"  JSESSIONID: {jsessionid}")
            print(f"  ROUTE: {route}")

            save_cookies_to_file(jsessionid, route)
            print("\n提示：Cookie已自动保存，下次可直接选择方式2使用")
            return session
        else:
            print("\n✗ 登录失败")
            print("建议：使用方式2手动获取Cookie")
            return None

    except Exception as e:
        print(f"✗ 登录过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_session_with_cookies(jsessionid: str, route: str) -> requests.Session:
    """
    创建带Cookie的会话并初始化

    Args:
        jsessionid: JSESSIONID Cookie值
        route: ROUTE Cookie值

    Returns:
        配置好的Session对象
    """
    session = requests.Session()
    session.headers.update(HEADERS)
    session.cookies.set("JSESSIONID", jsessionid)
    session.cookies.set("route", route)

    # 访问主页建立会话
    try:
        session.get(f"{BASE_URL}/xtgl/index.html", timeout=REQUEST_TIMEOUT)
        session.get(f"{BASE_URL}/jxzxjhgl/jxzxjhck_cxJxzxjhckIndex.html", timeout=REQUEST_TIMEOUT)
    except Exception:
        pass

    return session


def parse_response_error(resp: requests.Response) -> str:
    """
    解析错误响应中的错误信息

    Args:
        resp: requests响应对象

    Returns:
        错误信息字符串
    """
    try:
        match = re.search(r'错误提示</title>.*?<span[^>]*>(.*?)</span>', resp.text, re.DOTALL)
        if match:
            return match.group(1).strip()
        if '<body' in resp.text:
            body_start = resp.text.find('<body')
            body_end = resp.text.find('</body>')
            return resp.text[body_start:body_end][:300]
        return resp.text[:300]
    except Exception:
        return "未知错误"


def get_majors(session: requests.Session, jg_id: str, year: int) -> List[Dict]:
    """
    获取指定学院和年级的专业列表

    Args:
        session: requests会话对象
        jg_id: 学院ID
        year: 年级

    Returns:
        专业列表，每项包含 jxzxjhxx_id 和 zymc
    """
    url = f"{BASE_URL}/jxzxjhgl/jxzxjhck_cxJxzxjhckIndex.html"
    params = {"doType": "query", "gnmkdm": "N153540"}

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
        resp = session.post(url, params=params, data=data, timeout=REQUEST_TIMEOUT)

        if resp.status_code != 200:
            print(f"    ✗ 请求失败，状态码: {resp.status_code}")
            print(f"    → 可能是Cookie已过期，请重新登录获取新的Cookie")
            return []

        content_type = resp.headers.get('Content-Type', '')
        if "text/html" in content_type:
            error_msg = parse_response_error(resp)
            print(f"    ✗ 返回了HTML页面而非JSON数据")
            print(f"    → 错误信息: {error_msg}")
            print(f"    → 可能是Cookie已过期或权限不足")
            return []

        if not resp.text or not resp.text.strip():
            print(f"    ✗ 响应内容为空")
            return []

        result = resp.json()
        items = result.get("items", [])

        majors = [
            {
                "jxzxjhxx_id": item.get("jxzxjhxx_id", ""),
                "zymc": item.get("zymc", "").strip()
            }
            for item in items
        ]

        print(f"  → 获取到 {len(majors)} 个专业")
        return majors

    except requests.exceptions.JSONDecodeError:
        print(f"    ✗ 响应数据解析失败，可能不是有效的JSON")
        return []
    except Exception as e:
        print(f"  ✗ 获取专业列表失败: {e}")
        return []


def get_courses_by_major(session: requests.Session, jxzxjhxx_id: str) -> List[Dict]:
    """
    获取指定专业的所有课程信息（自动分页）

    Args:
        session: requests会话对象
        jxzxjhxx_id: 教学计划信息ID

    Returns:
        课程信息列表
    """
    url = f"{BASE_URL}/jxzxjhgl/jxzxjhkcxx_cxJxzxjhkcxxIndex.html"
    params = {"doType": "query", "gnmkdm": "N153540"}

    all_courses = []
    page = 1

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
            "queryModel.showCount": str(PAGE_SIZE),
            "queryModel.currentPage": str(page),
            "queryModel.sortName": "jyxdxnm,jyxdxqm,kch",
            "queryModel.sortOrder": "asc",
            "time": "2"
        }

        try:
            resp = session.post(url, params=params, data=data, timeout=REQUEST_TIMEOUT)
            result = resp.json()

            items = result.get("items", [])
            if not items:
                break

            all_courses.extend(items)

            total = result.get("totalResult", 0)
            if len(all_courses) >= total:
                break

            page += 1
            time.sleep(REQUEST_DELAY)

        except Exception as e:
            print(f"    ✗ 第 {page} 页获取失败: {e}")
            break

    return all_courses


def download_training_plan(session: requests.Session, jxzxjhxx_id: str, save_path: str) -> bool:
    """
    下载指定专业的培养方案PDF

    Args:
        session: requests会话对象
        jxzxjhxx_id: 教学计划信息ID
        save_path: 保存路径

    Returns:
        下载是否成功
    """
    url = f"{BASE_URL}/jxzxjhgl/jxzxjhxxwh_cxDyJxzxjhxx.html"
    params = {"jxzxjhxx_id": jxzxjhxx_id, "gnmkdm": "N153540"}

    try:
        resp = session.get(url, params=params, timeout=REQUEST_TIMEOUT, allow_redirects=True)

        content_type = resp.headers.get("Content-Type", "")
        is_pdf = "pdf" in content_type.lower() or resp.headers.get("Content-Disposition")

        if is_pdf:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(resp.content)
            print(f"    ✓ 培养方案已保存: {save_path}")
            return True
        else:
            print(f"    ✗ 培养方案下载失败，可能是登录过期")
            print(f"      响应类型: {content_type}")
            return False

    except Exception as e:
        print(f"    ✗ 培养方案下载失败: {e}")
        return False


def save_json(data: dict, filepath: str) -> None:
    """
    保存数据到JSON文件

    Args:
        data: 要保存的数据
        filepath: 保存路径
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_user_input_year() -> int:
    """
    获取用户输入的年级

    Returns:
        有效的年级年份
    """
    print("\n请输入要爬取的年级：")
    print("示例：2022、2023、2024")

    while True:
        year_input = input("年级: ").strip()
        if year_input and year_input.isdigit() and len(year_input) == 4:
            return int(year_input)
        print("错误：请输入有效的4位数字年份（如2022）！")


def get_login_choice() -> str:
    """
    获取用户选择的登录方式

    Returns:
        登录方式选项 ("1", "2", "3")
    """
    print("\n请选择登录方式：")
    print("  1 - 输入学号和密码自动登录（推荐）")
    print("  2 - 从cookie.json文件加载Cookie")
    print("  3 - 使用脚本中配置的JSESSIONID和ROUTE")
    print("\n提示：")
    print("  - 方式1：自动获取Cookie，首次使用推荐")
    print("  - 方式2：使用通过方式1自动保存的Cookie，快捷方便")
    print("  - 方式3：需要在脚本中手动填写Cookie值")
    print("  - 如果教务系统有验证码，请选择方式2或3")

    choice = input("\n请输入选项数字 (1/2/3，默认为1): ").strip()
    return choice if choice in ["1", "2", "3"] else "1"


def authenticate_session(choice: str) -> Optional[requests.Session]:
    """
    根据用户选择进行身份验证

    Args:
        choice: 登录方式 ("1", "2", "3")

    Returns:
        验证成功的Session对象，失败返回None
    """
    if choice == "1":
        return authenticate_with_credentials()
    elif choice == "2":
        return authenticate_with_file_cookie()
    else:
        return authenticate_with_config_cookie()


def authenticate_with_credentials() -> Optional[requests.Session]:
    """使用学号密码认证"""
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
    return login_to_system(username, password, debug=True)


def authenticate_with_file_cookie() -> Optional[requests.Session]:
    """使用文件中的Cookie认证"""
    jsessionid, route = load_cookies_from_file()

    if jsessionid and route:
        print("\n使用从文件加载的Cookie登录...")
        return create_session_with_cookies(jsessionid, route)
    else:
        print("\n错误：未找到有效的Cookie文件！")
        print("请先选择方式1登录获取Cookie")
        return None


def authenticate_with_config_cookie() -> Optional[requests.Session]:
    """使用脚本配置的Cookie认证"""
    if JSESSIONID and ROUTE:
        print("\n使用脚本中配置的Cookie登录...")
        return create_session_with_cookies(JSESSIONID, ROUTE)
    else:
        print("\n错误：脚本中的JSESSIONID和ROUTE未配置！")
        print("请在脚本配置区域填写你的Cookie信息：")
        print('  JSESSIONID = "你的JSESSIONID值"')
        print('  ROUTE = "你的ROUTE值"')
        print("\n获取方法：")
        print("  1. 浏览器登录教务系统")
        print("  2. 按F12打开开发者工具")
        print("  3. Application → Cookies → 复制JSESSIONID和ROUTE")
        return None


def process_major(session: requests.Session, major: Dict, major_dir: str) -> None:
    """
    处理单个专业：获取课程信息和下载培养方案

    Args:
        session: requests会话对象
        major: 专业信息字典
        major_dir: 专业目录路径
    """
    jxzxjhxx_id = major["jxzxjhxx_id"]
    zymc = major["zymc"]

    if not jxzxjhxx_id or not zymc:
        return

    print(f"  └─ {zymc}")

    # 获取课程信息
    print(f"      → 获取课程信息...")
    courses = get_courses_by_major(session, jxzxjhxx_id)
    print(f"      → 共 {len(courses)} 门课程")

    if courses:
        courses_path = os.path.join(major_dir, "courses.json")
        save_json(courses, courses_path)
        print(f"      ✓ 课程已保存")
    else:
        print(f"      ✗ 无课程数据")

    # 下载培养方案
    print(f"      → 下载培养方案...")
    pdf_path = os.path.join(major_dir, "培养方案.pdf")
    download_training_plan(session, jxzxjhxx_id, pdf_path)


def process_college(session: requests.Session, college_name: str, jg_id: str, output_dir: str, year: int) -> None:
    """
    处理单个学院：获取专业列表并处理每个专业

    Args:
        session: requests会话对象
        college_name: 学院名称
        jg_id: 学院ID
        output_dir: 输出目录路径
        year: 年级
    """
    print(f"\n【{college_name}】jg_id={jg_id}")

    majors = get_majors(session, jg_id, year)

    if not majors:
        print(f"  ✗ 该学院没有找到 {year} 级专业")
        return

    college_dir = os.path.join(output_dir, f"{college_name}-{year}")
    os.makedirs(college_dir, exist_ok=True)

    for major in majors:
        zymc = major["zymc"]
        major_dir = os.path.join(college_dir, f"{zymc}-{year}")
        os.makedirs(major_dir, exist_ok=True)

        process_major(session, major, major_dir)
        time.sleep(REQUEST_DELAY)


def main() -> None:
    """主函数：程序入口"""
    print("=" * 60)
    print("青岛理工大学 - 教务系统课程爬取")
    print("=" * 60)

    # 获取年级
    year = get_user_input_year()
    print(f"\n已选择年级: {year}")

    # 设置输出目录
    output_dir = os.path.join(SCRIPT_DIR, "docs", f"{year}级")
    print(f"输出目录: {output_dir}")

    # 身份验证
    choice = get_login_choice()
    session = authenticate_session(choice)

    if not session:
        return

    # 遍历学院和专业
    for college_name, jg_id in COLLEGES.items():
        process_college(session, college_name, jg_id, output_dir, year)

    print("\n" + "=" * 60)
    print("完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
