import random
import time
import json
from selenium import webdriver
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException

#edge_options = webdriver.EdgeOptions()
#edge_options.add_argument('--headless')
#edge_options.add_argument("--disable-blink-features=AutomationControlled")

try:
    with open('./config/chair_config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 从配置中读取参数
    USER_INFO = config['user_info']
    USERNAME = USER_INFO['student_id']
    PASSWORD = USER_INFO['password']
    STAR_CHAIR = config['chair']['star_chair']  # 星标座位列表
    floor = config['chair']['floor']  # 座位所在楼层
    area = config['chair']['area']  # 座位所在区域
except FileNotFoundError:
    print("错误：配置文件 config.json 未找到！请确保文件存在。")
    exit()
except json.JSONDecodeError:
    print("错误：配置文件 config.json 格式不正确，请检查！")
    exit()

account = USERNAME  
password = PASSWORD  
preferred_seat = STAR_CHAIR 
area_xpath_map = {
    #二楼
    '北楼二层外文库（东）': '//*[@id="north2east"]',
    '二层连廊及流通大厅': '//*[@id="north2elian"]',
    '北楼二层外文库（西）': '//*[@id="north2west"]',
    '南楼二层大厅': '//*[@id="south2"]',
    #三楼
    '北楼三层ILibrary-B（西）': '//*[@id="west3B"]',
    '大屏辅学空间': '//*[@id="eastnorthda"]',
    '南楼三层中段': '//*[@id="south3middle"]',
    '北楼三层ILibrary-A（东）': '//*[@id="east3A"]',
    #四楼
    '北楼四层西侧': '//*[@id="north4west"]',
    '北楼四层中间': '//*[@id="north4middle"]',
    '北楼四层东侧': '//*[@id="north4east"]',
    '北楼四层西南侧': '//*[@id="north4southwest"]',
    '北楼四层东南侧': '//*[@id="north4southeast"]',
}
url = 'http://www.lib.xjtu.edu.cn/'


def jump_ad(browser):
    time.sleep(2)
    close_button = browser.find_element(By.XPATH, '/html/body/div[5]/ul/li[1]/div/a[1]')
    close_button.click()
    time.sleep(1)

def login(browser):
    browser.find_element(By.XPATH, '//*[@id="header"]/div/div/div/div/div/div[1]/span').click()
    time.sleep(2)
    browser.find_element(By.XPATH, '//*[@id="form1"]/input[1]').send_keys(account)
    browser.find_element(By.XPATH, '//*[@id="form1"]/input[2]').send_keys(password)
    browser.find_element(By.XPATH, '//*[@id="account_login"]').click()
    time.sleep(2)

def get_all_seats_info(browser):
    """
    提取所有座位信息
    返回: {
        'available': ['D008', 'D009', ...],  # 可用座位列表
        'occupied': ['D007', 'D010', ...],   # 被占座位列表
        'all_seats': {'D008': 'available', 'D007': 'occupied', ...}  # 所有座位状态
    }
    """ 
    available_seats = []
    occupied_seats = []
    all_seats = {}
    
    try:
        # 查找所有座位按钮
        all_seat_elements = browser.find_elements(By.CSS_SELECTOR, ".btn-group a.btn")
        
        for seat_element in all_seat_elements:

            seat_id = seat_element.text.strip()
            
            if not seat_id:  
                continue
            
            class_name = seat_element.get_attribute('class') or ''
            href = seat_element.get_attribute('href') or ''
            disabled = seat_element.get_attribute('disabled')
            style = seat_element.get_attribute('style') or ''
            
            if 'btn-info' in class_name and 'javascript:void(0)' not in href and not disabled:
                available_seats.append(seat_id)
                all_seats[seat_id] = 'available'
            
            elif 'btn-default' in class_name or disabled or 'javascript:void(0)' in href:
                occupied_seats.append(seat_id)
                all_seats[seat_id] = 'occupied'
            
            else:
                all_seats[seat_id] = 'unknown'
        
        result = {
            'available': available_seats,
            'occupied': occupied_seats,
            'all_seats': all_seats
        }      
        return result
        
    except Exception as e:
        print(f"获取座位信息失败: {e}")
        return {
            'available': [],
            'occupied': [],
            'all_seats': {}
        }

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

def check_current_url(browser, target_url="http://rg.lib.xjtu.edu.cn:8086/my/"):
    current_url = browser.current_url       
    if current_url == target_url:
        print("✓ URL精确匹配")
        return True

    return False

def get_chair(browser):
    booking_entry = browser.find_element(By.XPATH, '//*[@id="grid2"]/div[1]/div/div[1]/div/div/p')
    if not safe_click(browser, booking_entry, "预约入口"):
                print("无法点击预约入口")
    time.sleep(2)
    browser.switch_to.window(browser.window_handles[-1])
    browser.find_element(By.XPATH, '/html/body/div[3]/div/div[1]/div[1]/div[2]/a').click() #点击预约座位
    time.sleep(2)
    if floor == '2':
        browser.find_element(By.XPATH, '//*[@id="tab-select"]/option[1]').click()
    elif floor == '3':
        browser.find_element(By.XPATH, '//*[@id="tab-select"]/option[2]').click()
    elif floor == '4':
        browser.find_element(By.XPATH, '//*[@id="tab-select"]/option[3]').click()
    else:
        print("Invalid floor number.")
        return
    time.sleep(0.5)
    area_xpath = area_xpath_map.get(area)
    if not area_xpath:
        print("Invalid area name.")
        return
    browser.find_element(By.XPATH, area_xpath).click() #选择区域
    time.sleep(0.5)
    seats_info = get_all_seats_info(browser)
    available_seats = seats_info['available']
    
    if not available_seats:
        print("No available seats in this area.")
        return
    available_preferred = [seat for seat in preferred_seat if seat in available_seats]
    if available_preferred:
        selected_seat = available_preferred[0]
        print(f"Preferred seat {selected_seat} is available. Selecting it.")
        seat_xpath = f"//a[text()='{selected_seat}']"
    else:
        print(f"Preferred seat {preferred_seat} is not available. Selecting a random available seat.")
        random_seat = random.choice(available_seats)
        selected_seat = random_seat
        seat_xpath = f"//a[text()='{random_seat}']"
    
   
    seat_element = browser.find_element(By.XPATH, seat_xpath)
    seat_element.click()
    time.sleep(5)
    if not check_current_url(browser):
        print("30分钟内无法再次预约，持续预约中...")
        while not check_current_url(browser):
            if floor == '2':
                browser.find_element(By.XPATH, '//*[@id="tab-select"]/option[1]').click()
            elif floor == '3':
                browser.find_element(By.XPATH, '//*[@id="tab-select"]/option[2]').click()
            elif floor == '4':
                browser.find_element(By.XPATH, '//*[@id="tab-select"]/option[3]').click()
            else:
                print("Invalid floor number.")
                return
            time.sleep(0.5)
            browser.find_element(By.XPATH, area_xpath).click() #选择区域
            time.sleep(0.5)
            seat_element = browser.find_element(By.XPATH, seat_xpath)
            seat_element.click()
            time.sleep(5)
            
    time.sleep(0.5)
    print(f"Successfully selected seat {selected_seat}.")

    
def main():
    try:
        driver = webdriver.Edge()
        driver.get(url)
        time.sleep(2)
        jump_ad(driver)
        login(driver)
        time.sleep(5)
        get_chair(driver)
        driver.quit()  # 关闭浏览器
        print("Chair selection completed.")
    except Exception as e:
        print(f"An error occurred: {e}")
    
if __name__ == "__main__":
    main()

