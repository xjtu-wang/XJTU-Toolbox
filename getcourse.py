import requests
import time
import json
import datetime
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# =================================================================
# 阶段一：从 config.json 文件加载配置
# =================================================================
try:
    with open('./config/course_config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 从配置中读取参数
    USER_INFO = config['user_info']
    TIMING_SETTINGS = config['timing_settings']
    TARGET_COURSE_ATTRS = config['target_course'] #课程ID命名方式 例如2024-2025 第三个学期 加上课程编号 班级号的课程ID为 202420253CORE10010301
    MY_STUDENT_ID = USER_INFO['student_id']
    MY_PASSWORD = USER_INFO['password']
    TARGET_TIME_STR = TIMING_SETTINGS['target_time']
    RETRY_KEYWORDS = TIMING_SETTINGS.get('retry_keywords', ["该课程超过课容量", "名额", "已满", "未到选课时间"])  # 默认重试关键词

    
    print("配置加载成功！目标课程:", TARGET_COURSE_ATTRS['teachingClassId'])

except FileNotFoundError:
    print("错误：配置文件 config.json 未找到！请确保文件存在。")
    exit()
except json.JSONDecodeError:
    print("错误：配置文件 config.json 格式不正确，请检查！")
    exit()

def main():
    # 主门户登录URL
    main_login_url = 'https://xkfw.xjtu.edu.cn/'

    # =================================================================
    # 阶段一：使用Selenium登录并获取Cookies
    # =================================================================
    print("启动浏览器，准备通过Selenium登录主门户...")
    edge_options = webdriver.EdgeOptions()
    #edge_options.add_argument('--headless') # 如果你不需要看到浏览器界面，可以启用无头模式
    driver = webdriver.Edge(options=edge_options)
    driver.get(main_login_url)

    # --- 在这里，你需要编写Selenium代码来定位输入框和按钮，并完成登录 ---
    # 等待用户名输入框加载完成
    wait = WebDriverWait(driver, 30) # 等待最多30秒
    username_field = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="vue_main"]/div[2]/div[2]/div/div[4]/div/div[2]/div[1]/div/form/div[1]/div/div/input'))) 
    password_field = driver.find_element(By.XPATH, '//*[@id="vue_main"]/div[2]/div[2]/div/div[4]/div/div[2]/div[1]/div/form/div[2]/div/div/input') 
    login_button = driver.find_element(By.XPATH, '//*[@id="vue_main"]/div[2]/div[2]/div/div[4]/div/div[2]/div[1]/div/form/div[3]/div/button') 

    username_field.send_keys(MY_STUDENT_ID)
    password_field.send_keys(MY_PASSWORD)
    login_button.click()

    # 登录后，等待页面跳转到选课系统，并确保页面加载了包含"选课"字样的标题
    print("登录成功，等待跳转到选课系统...")
    wait.until(EC.title_contains("选课"))
    print("已成功进入选课系统！")


    # --- 关键一步：从Selenium中提取Cookies ---
    print("正在从浏览器中提取Cookies...")
    cookies = driver.get_cookies()
    driver.quit() # Selenium的任务已完成，关闭浏览器

    # =================================================================
    # 阶段二：将Cookies迁移到Requests，并执行后续高速操作
    # =================================================================
    # 创建一个requests session
    session = requests.Session()

    # 将从Selenium获得的cookies加入到requests的session中
    for cookie in cookies:
        session.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])

    print("Cookies迁移成功，后续操作将由Requests接管。")
    # 为了调试，我们先假设一个token，实际运行时它应该是动态获取的
    token = "1b030150-696d-4575-ad36-1ccfe155fad2" # 这是一个示例token

    # 我们将动态地构建Referer URL
    referer_url = f"https://xkfw.xjtu.edu.cn/xsxkapp/sys/xsxkapp/*default/grablessons.do?token={token}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        'Content-Type': 'application/json;charset=UTF-8',
        'Accept': 'application/json, text/javascript, */*; q=0.01', # 模仿浏览器，更保险
        'X-Requested-With': 'XMLHttpRequest', 
        'Referer': referer_url 
    }
    session.headers.update(headers)

    sso_token_url = 'https://xkfw.xjtu.edu.cn/xsxkapp/sys/xsxkapp/student/register.do?number={MY_STUDENT_ID}' # <--- 猜想的URL，你需要验证
    print("阶段一：正在进行单点登录并获取Token...")
    try:
        response_token = session.get(sso_token_url)
        token = response_token.json()['data']['token']
        print(f"获取到Token: {token}")
    except Exception as e:
        print(f"获取Token可能已不再需要或方式改变: {e}")
        token = "" # 暂时置空


    # --- 阶段三：进入选课主界面 ---
    # 携带Token访问抢课主页，这一步是模拟“点击开始选课”
    start_selection_url = f"https://xkfw.xjtu.edu.cn/xsxkapp/sys/xsxkapp/*default/grablessons.do?token={token}"
    print("\n阶段三：正在进入选课主界面...")
    try:
        response_start = session.get(start_selection_url)
        response_start.raise_for_status()
        print("阶段三：成功进入选课主界面，万事俱备！")

    except requests.exceptions.RequestException as e:
        print(f"阶段三请求失败: {e}")
        exit()

    # --- 抢课循环 ---
    # 可以在这里设置一个循环，在抢课开始前几秒不断尝试
    # time.sleep(抢课开始时间 - 当前时间 - 5)

    # --- 2.3 定时等待 ---
    start_time = datetime.datetime.strptime(TARGET_TIME_STR, "%Y-%m-%d %H:%M:%S")
    print(f"\n脚本已准备就绪，将会在 {TARGET_TIME_STR} 自动开始执行抢课...")
    while datetime.datetime.now() < start_time:
        time.sleep(0.1) # 每0.1秒检查一次时间

    print("\n时间到！开始抢课！")

    # --- 阶段四：执行最终选课请求 (调试版本) ---
    submit_url = 'https://xkfw.xjtu.edu.cn/xsxkapp/sys/xsxkapp/elective/volunteer.do' # 你验证过的URL

    referer_url = f"https://xkfw.xjtu.edu.cn/xsxkapp/sys/xsxkapp/*default/grablessons.do?token={token}"
    final_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', #内容类型是表单
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'X-Requested-With': 'XMLHttpRequest',
        'token': token, #增加自定义的token头
        'Referer': referer_url
    }
    # 更新session的headers
    session.headers.update(final_headers)

    final_payload_data = {
        "operationType": "1",
        "studentCode": MY_STUDENT_ID,
        "electiveBatchCode": TARGET_COURSE_ATTRS['electiveBatchCode'],
        "teachingClassId": TARGET_COURSE_ATTRS['teachingClassId'],
        "isMajor": TARGET_COURSE_ATTRS['isMajor'],
        "campus": TARGET_COURSE_ATTRS['campus'],
        "teachingClassType": TARGET_COURSE_ATTRS['teachingClassType'],
        "isAlternate": TARGET_COURSE_ATTRS['isAlternate']
    }
    final_form_data = {
        'addParam': json.dumps({"data": final_payload_data}, separators=(',', ':'))
    }

    print("\n阶段四：准备在抢课开始时发送最终选课指令！")
    while True:
        try:
            response_submit = session.post(submit_url, data=final_form_data, timeout=5)

            # --- 新增的调试代码 ---
            print(f"服务器返回的HTTP状态码: {response_submit.status_code}")
            print("---------- 服务器返回的原始内容开始 ----------")
            print(response_submit.text) # 打印出服务器返回的所有文本内容
            print("----------- 服务器返回的原始内容结束 -----------")
            # --- 调试代码结束 ---

            # 检查状态码，如果不是200就没必要尝试解析JSON了
            response_submit.raise_for_status() 

            # 尝试解析JSON
            result = response_submit.json()

            print("="*20 + " 抢课结果 " + "="*20)
            print(result)
            print("="*50)
            if result.get('code') == '1':
                print(f"✅ ✅ ✅ 恭喜！课程 {TARGET_COURSE_ATTRS['teachingClassId']} 可能已抢到！服务器返回成功！")
                break
            else:
                error_msg = result.get('msg', '无具体错误信息')
                # 判断是否是因容量不足而失败
                if any(keyword in str(error_msg) for keyword in RETRY_KEYWORDS):
                    print(f"❌ 课程容量不足，将在随机延时后重试... ({error_msg})")
                    time.sleep(random.uniform(0.1, 0.2)) # 随机延时0.1-0.2秒，防止请求过于规律
                else:
                    # 如果是其他错误（如课程冲突、前置课程不满足等），则直接失败
                    print(f"❌ ❌ ❌ 抢课失败，非容量问题，停止重试。服务器返回：{error_msg}")
                    break # 停止循环


        except json.JSONDecodeError:
            print("\n[错误分析]：服务器返回的内容不是有效的JSON格式。请检查上面打印出的“原始内容”，查看具体的HTML错误信息。最可能的原因是：当前未到选课时间。")
        except requests.exceptions.RequestException as e:
            print(f"\n[错误分析]：阶段四最终请求失败: {e}")

if __name__ == "__main__":
    main()
    