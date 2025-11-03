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

LOGIN_URL = "https://ehall.xjtu.edu.cn/new/index.html?browser=no"
EVALUATION_PAGE_URL = "https://ehall.xjtu.edu.cn/portal/html/select_role.html?appId=5856333445645704"

try:
    with open('./config/assess_config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 从配置中读取参数
    USER_INFO = config['user_info']
    USERNAME = USER_INFO['student_id']
    PASSWORD = USER_INFO['password']
    SUGGESTION_TEXT = config['comment']['suggestion_text']


except FileNotFoundError:
    print("错误：配置文件 config.json 未找到！请确保文件存在。")
    exit()
except json.JSONDecodeError:
    print("错误：配置文件 config.json 格式不正确，请检查！")
    exit()

POST_LOGIN_ELEMENT_SELECTOR = "#ampHasLogin" 


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
            
def main():
    """主函数，全程使用Selenium模拟点击来执行自动化评教"""
    print("正在启动浏览器...")
    driver = webdriver.Edge()
    # 设置一个全局的、较长的等待时间，方便处理各种网络延迟和手动操作
    wait = WebDriverWait(driver, 10)

    try:
        # --- 1. 登录 ---
        print(f"正在访问登录页面: {LOGIN_URL}")
        driver.get(LOGIN_URL)
        start_login = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="ampHasNoLogin"]')))
        start_login.click()

        print("正在填写账号密码...")
        # 等待用户名输入框出现并填写
        username_input = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="vue_main"]/div[2]/div[2]/div/div[4]/div/div[2]/div[1]/div/form/div[1]/div/div/input')))
        password_input = driver.find_element(By.XPATH, '//*[@id="vue_main"]/div[2]/div[2]/div/div[4]/div/div[2]/div[1]/div/form/div[2]/div/div/input')
        login = driver.find_element(By.XPATH, '//*[@id="vue_main"]/div[2]/div[2]/div/div[4]/div/div[2]/div[1]/div/form/div[3]/div/button')
        username_input.send_keys(USERNAME)
        password_input.send_keys(PASSWORD)
        safe_click(driver, login, "登录按钮")      
        # 等待登录成功的信号出现
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, POST_LOGIN_ELEMENT_SELECTOR)))
        print("\n登录成功！")

        # --- 2. 导航到评教页面 ---
        print(f"正在导航到评教列表页: {EVALUATION_PAGE_URL}")
        driver.get(EVALUATION_PAGE_URL)
        rukou = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="20241125142542723"]')))
        rukou.click()
        driver.window_handles[0]  # 切换到新打开的窗口
        kaishi = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="pjglTopCard"]/div/div[2]')))
        kaishi.click()

        # --- 3. 循环评教 ---
        evaluation_count = 0
        #第一轮过程性评教，直到评完
        while True:
            try:
                print(f"\n{'='*20} 第 {evaluation_count + 1} 轮评教 {'='*20}")
                # 查找“进入评教”或类似的按钮
                print(" > 正在查找下一个评教项目...")
                
                # 使用JS脚本中的CSS选择器: .card-btn.blue
                # 这里我们用WebDriverWait来等待按钮出现并且可以被点击
                enter_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".card-btn.blue")))
                
                # 为了防止页面元素遮挡，有时需要用JavaScript来点击
                driver.execute_script("arguments[0].click();", enter_button)
                print(" > 已进入评教页面。")
                evaluation_count += 1

                # 等待评分区加载完成
                print(" > 等待评分选项加载...")
                rating_groups = wait.until(EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, ":scope .kc-js-right > div > div:last-child")
                ))

                print(f" > 找到 {len(rating_groups)} 个评分题目，开始选择“满分”...")
                for option in rating_groups:
                    option.click()
                    time.sleep(0.1) # 模拟人类的点击间隔

                print(" > 所有评分题已选择“满分”。")

                # 等待评教表单页面加载完成（以单选按钮出现为标志）
                print(" > 正在选择所有问题的“非常满意”...")
                # 使用JS脚本中的CSS选择器: label:nth-child(1).bh-radio-label
                very_satisfied_options = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "label:nth-child(1).bh-radio-label")))
                for option in very_satisfied_options:
                    option.click()
                    time.sleep(0.1) # 模拟人类的点击间隔

                # 填写意见和建议
                print(f" > 正在填写建议: '{SUGGESTION_TEXT}'")
                # 使用JS脚本中的CSS选择器: .bh-txt-input__txtarea
                suggestion_box = driver.find_element(By.CLASS_NAME, "bh-txt-input__txtarea")
                suggestion_box.send_keys(SUGGESTION_TEXT)

                # 点击提交
                print(" > 正在点击提交按钮...")
                # 使用JS脚本中的CSS选择器: .bh-btn.bh-btn-success.bh-btn-large
                submit_button = driver.find_element(By.CSS_SELECTOR, ".bh-btn.bh-btn-success.bh-btn-large")
                submit_button.click()

                # 在弹窗中点击最终确认
                print(" > 正在点击最终确认...")
                # 使用JS脚本中的CSS选择器: .bh-dialog-btn.bh-bg-primary.bh-color-primary-5
                confirm_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".bh-dialog-btn.bh-bg-primary.bh-color-primary-5")))
                confirm_button.click()

                print(f" > \033[92m成功:\033[0m 本轮评教已提交！")
                
                # 等待页面跳转回列表页，为下一次循环做准备
                print(" > 等待5秒后开始下一轮...")
                time.sleep(5)

            except TimeoutException:
                # 如果在规定时间内找不到“进入评教”的按钮，说明所有评教已完成
                print("\n\033[92m未找到更多评教项目，自动化流程结束。\033[0m")
                break
            except Exception as e:
                print(f"\n\033[91m评教过程中发生未知错误: {e}\033[0m")
                print("脚本将终止。")
                break
        #第二轮期末评教，直到评完 
        qiehuan = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="tabName-content-1"]/div/div[1]')))
        qiehuan.click()
        while True:
            try:
                print(f"\n{'='*20} 第 {evaluation_count + 1} 轮期末评教 {'='*20}")
                # 查找“进入评教”或类似的按钮
                print(" > 正在查找下一个期末评教项目...")
                
                # 使用JS脚本中的CSS选择器: .card-btn.blue
                enter_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".card-btn.blue")))
                
                # 为了防止页面元素遮挡，有时需要用JavaScript来点击
                driver.execute_script("arguments[0].click();", enter_button)
                print(" > 已进入期末评教页面。")
                evaluation_count += 1


                # 等待评分区加载完成
                print(" > 等待评分选项加载...")
                rating_groups = wait.until(EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, ":scope .kc-js-right > div > div:last-child")
                ))

                print(f" > 找到 {len(rating_groups)} 个评分题目，开始选择“满分”...")
                for option in rating_groups:
                    option.click()
                    time.sleep(0.1) # 模拟人类的点击间隔

                print(" > 所有评分题已选择“满分”。")

                # 等待评教表单页面加载完成（以单选按钮出现为标志）
                print(" > 正在选择所有问题的“非常满意”...")
                
                very_satisfied_options = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "label:nth-child(1).bh-radio-label")))
                for option in very_satisfied_options:
                    option.click()
                    time.sleep(0.1) # 模拟人类的点击间隔



                # 填写意见和建议
                print(f" > 正在填写建议: '{SUGGESTION_TEXT}'")
                
                suggestion_box = driver.find_element(By.CLASS_NAME, "bh-txt-input__txtarea")
                suggestion_box.send_keys(SUGGESTION_TEXT)

                # 点击提交
                print(" > 正在点击提交按钮...")
                
                submit_button = driver.find_element(By.CSS_SELECTOR, ".bh-btn.bh-btn-success.bh-btn-large")
                submit_button.click()

                # 在弹窗中点击最终确认
                print(" > 正在点击最终确认...")
                
                confirm_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".bh-dialog-btn.bh-bg-primary.bh-color-primary-5")))
                confirm_button.click()

                print(f" > \033[92m成功:\033[0m 本轮期末评教已提交！")
                
                # 等待页面跳转回列表页，为下一次循环做准备
                print(" > 等待5秒后开始下一轮...")
                time.sleep(5)


            except TimeoutException:
                # 如果在规定时间内找不到“进入评教”的按钮，说明所有评教已完成
                print("\n\033[92m未找到更多评教项目，自动化流程结束。\033[0m")
                break
            except Exception as e:
                print(f"\n\033[91m评教过程中发生未知错误: {e}\033[0m")
                print("脚本将终止。")
                break


    except Exception as e:
        print(f"\n\033[91m脚本执行失败: {e}\033[0m")
    finally:
        # --- 4. 清理 ---
        print(f"\n总共完成了 {evaluation_count} 个评教。")
        print("5秒后将自动关闭浏览器...")
        time.sleep(5)
        driver.quit()


if __name__ == "__main__":
    main()
