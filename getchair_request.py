import requests
import time
import json
import datetime
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException

try:
    with open('./config/chair_config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 从配置中读取参数
    USER_INFO = config['user_info']
    USERNAME = USER_INFO['student_id']
    PASSWORD = USER_INFO['password']
    STAR_CHAIR = config['chair']['star_chair']  # 星标座位列表
except FileNotFoundError:
    print("错误：配置文件 config.json 未找到！请确保文件存在。")
    exit()
except json.JSONDecodeError:
    print("错误：配置文件 config.json 格式不正确，请检查！")
    exit()

MY_STUDENT_ID = USERNAME
MY_PASSWORD = PASSWORD

def get_star_chair_area(chair_id):
    #根据座位首字母判断
    if chair_id.startswith("A"or "B"):
        return "north2elian"
    elif chair_id.startswith("D" or "E"):
        return "north2east"
    elif chair_id.startswith("C"):
        return "south2"
    elif chair_id.startswith("N"):
        return "north2west"
    elif chair_id.startswith("Y"):
        return "west3B"
    elif chair_id.startswith("P"):
        return "eastnorthda"
    elif chair_id.startswith("X"):
        return "east3A"
    elif chair_id.startswith("K" or "L" or "M"):
        return "north4west"
    elif chair_id.startswith( "J"):
        return "north4middle"
    elif chair_id.startswith("H" or "F" or "G"):
        return "north4east"
    elif chair_id.startswith("Q"):
        return "north4southwest"
    elif chair_id.startswith("T"):
        return "north4southeast"
    else:
        return  "south3middlen"
def get_star_chair_url(chair_id):
    #首先获得座位所属区域，然后拼接成例如url = "http://rg.lib.xjtu.edu.cn:8086/seat/?kid=Y002&sp=west3B"
    area = get_star_chair_area(chair_id)
    if area:
        return f"http://rg.lib.xjtu.edu.cn:8086/seat/?kid={chair_id}&sp={area}"
    return None

def jump_ad(browser):
    try:
        time.sleep(5)  # 等待广告加载
        wait = WebDriverWait(browser, 10)
        close_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a.btn-skip')))
        close_button.click()
    except TimeoutException:
                # 保存截图，看看无头模式下页面到底长什么样
        screenshot_path = 'headless_error.png'
        browser.save_screenshot(screenshot_path)
        print(f"已保存当前页面截图到 {screenshot_path}，请查看图片分析原因。")
        print("广告关闭按钮未能在规定时间内加载")

def login(browser):
    time.sleep(2)  # 等待页面加载
    wait = WebDriverWait(browser, 10)
    wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="header"]/div/div/div/div/div/div[1]/span'))).click()
    browser.find_element(By.XPATH, '//*[@id="vue_main"]/div[2]/div[2]/div/div[4]/div/div[2]/div[1]/div/form/div[1]/div/div/input').send_keys(USERNAME)
    browser.find_element(By.XPATH, '//*[@id="vue_main"]/div[2]/div[2]/div/div[4]/div/div[2]/div[1]/div/form/div[2]/div/div/input').send_keys(PASSWORD)
    browser.find_element(By.XPATH, '//*[@id="vue_main"]/div[2]/div[2]/div/div[4]/div/div[2]/div[1]/div/form/div[3]/div/button').click()
    time.sleep(2)
    try:
        # 设置一个较短的等待时间，比如3秒。
        # 因为如果这个警告页面不出现，我们不希望脚本卡在这里太久。
        short_wait = WebDriverWait(browser, 3)
        
        # 我们通过按钮上的文字来定位“仍然发送”这个按钮
        send_anyway_button_xpath = "//*[text()='仍然发送']"
        
        print("检查是否存在'不安全提交'警告页面...")
        
        # 等待“仍然发送”按钮变为可点击状态
        send_anyway_button = short_wait.until(
            EC.element_to_be_clickable((By.XPATH, send_anyway_button_xpath))
        )
        
        # 如果找到了按钮，就点击它
        print("警告页面已出现，正在点击 '仍然发送'...")
        send_anyway_button.click()
        print("已点击 '仍然发送'，继续执行脚本。")

    except TimeoutException:
        # 如果在3秒内没有找到“仍然发送”按钮，说明没有出现警告页面
        # 这是一个正常情况，脚本会捕获超时异常，然后什么都不做，继续执行
        print("未出现'不安全提交'警告，脚本继续正常执行。")
        pass

def safe_click(browser, element, description="元素"):
    """安全点击函数，处理元素被遮挡的情况"""
    try:
        # 方法1: 普通点击
        element.click()
        print(f"普通点击成功: {description}")
        return True
    except ElementClickInterceptedException:
        try:
            print(f"元素被遮挡，尝试滚动到元素位置: {description}")
            # 方法2: 滚动到元素位置再点击
            browser.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
            time.sleep(1)
            element.click()
            print(f"滚动后点击成功: {description}")
            return True
        except:
            try:
                print(f"尝试JavaScript点击: {description}")
                # 方法3: JavaScript点击
                browser.execute_script("arguments[0].click();", element)
                print(f"JavaScript点击成功: {description}")
                return True
            except Exception as e:
                print(f"所有点击方法都失败: {description}, 错误: {e}")
                return False

main_login_url = "http://www.lib.xjtu.edu.cn/"


def main():
    edge_options = webdriver.EdgeOptions()
    edge_options.add_argument('--headless')  # 如果不需要可视化界面，可以启用无头模式
    edge_options.add_argument('--no-sandbox')  # 禁用沙盒模式
    edge_options.add_argument('--disable-dev-shm-usage')  # 禁用共享内存
    edge_options.add_argument('--allow-insecure-localhost') 
    edge_options.add_argument('--ignore-ssl-errors')
    #伪造浏览器UA
    #edge_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0")
    # 创建浏览器实例
    driver = webdriver.Edge(edge_options) # 或者使用 webdriver.Chrome()
    #设置最长等待时间为30秒
    wait = WebDriverWait(driver, 30)
    driver.get(main_login_url)
    #wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="header"]/div/div/div/div/div/div[1]/span'))).click()
    jump_ad(driver)  # 跳过广告
    login(driver)
    time.sleep(5)  # 等待登录完成
    booking_entry = driver.find_element(By.XPATH, '//*[@id="grid2"]/div[1]/div/div[1]/div/div/p')
    safe_click(driver, booking_entry, "我要预约")
    time.sleep(2)
    driver.switch_to.window(driver.window_handles[-1])
    time.sleep(2)  # 等待新窗口加载

    # --- 关键一步：从Selenium中提取Cookies ---
    print("正在从浏览器中提取Cookies...")
    cookies = driver.get_cookies()
    formatted_cookies_list = []
    for cookie in cookies:
        formatted_cookies_list.append(f"{cookie['name']}={cookie['value']}")

    final_cookie_string = "; ".join(formatted_cookies_list)
    driver.quit() # Selenium的任务已完成，关闭浏览器

    url = get_star_chair_url(STAR_CHAIR[0])  # 获取第一个星标座位的预约链接
    # 2. 请求头 (与之前相同)
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cache-Control": "no-cache",
        # 【重要】如果脚本失败，最可能的原因是 Cookie 过期了。请重新登录网站并替换这里的 Cookie 值。
        "Cookie": final_cookie_string, # 请务必使用您自己最新的有效 Cookie
        "Pragma": "no-cache",
        "Proxy-Connection": "keep-alive",
        "Referer": "http://rg.lib.xjtu.edu.cn:8086/seat/",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    }

    # 预期成功的跳转目标 URL 的一部分
    # 请根据您自己预约成功后的实际 URL 进行调整
    SUCCESS_URL_PART = "/seat/my/"

    try:
        # 发送请求。allow_redirects=True 是默认行为，这里显式写出以强调。
        response = requests.get(url, headers=headers, verify=False, allow_redirects=True)

        print(f"请求已发送，服务器最终响应状态码: {response.status_code}")
        print(f"请求发起的原始URL: {url}")
        print(f"请求结束后的最终URL: {response.url}")
        print("-" * 20)

        if SUCCESS_URL_PART in response.url:
            print("[判断结果]: 预约成功！")
        else:
            #无限重复发包
            while True:
                #循环发送所有座位url
                url = get_star_chair_url(random.choice(STAR_CHAIR))
                current_chair = url.split('kid=')[1].split('&')[0]
                response = requests.get(url, headers=headers, verify=False, allow_redirects=True)
                if SUCCESS_URL_PART in response.url:
                    print(f"[判断结果]: 预约成功！座位是 {current_chair}")
                    break
                else:
                    print(f"预约失败,请求已发送，服务器响应状态码: {response.status_code},座位是 {current_chair}")
                time.sleep(random.uniform(0.1, 0.3))  # 随机延迟1到3秒后重试

    except requests.exceptions.RequestException as e:
        print(f"请求过程中发生网络错误: {e}")

if __name__ == "__main__":
    main()