from bs4 import BeautifulSoup
import cloudscraper
import json
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from concurrent.futures import ThreadPoolExecutor, as_completed
import time, random
def crawl_bds_detail_selenium(url):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    result = {'detail_link': url}
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'h1.re__pr-title'))
        )
        h1 = driver.find_element(By.CSS_SELECTOR, 'h1.re__pr-title')
        result['Tiêu đề'] = h1.text.strip()
    except:
        pass
    try:
        address_block = driver.find_element(By.CSS_SELECTOR, 'span.re__pr-short-description')
        result['Địa chỉ'] = address_block.text.strip()
    except:
        pass
    try:
        specs = driver.find_elements(By.CSS_SELECTOR, 'div.re__pr-specs-content-item')
        for spec in specs:
            try:
                key = spec.find_element(By.CSS_SELECTOR, 'span.re__pr-specs-content-item-title').text.strip()
                value = spec.find_element(By.CSS_SELECTOR, 'span.re__pr-specs-content-item-value').text.strip()
                result[key] = value
            except:
                continue
    except:
        pass
    try:
        phone_block = driver.find_element(By.CSS_SELECTOR, 'div.InlineShowPhoneButton_linkContact__U_lEr')
        result['SĐT'] = phone_block.text.strip()
    except:
        pass
    driver.quit()
    return result
# Đọc danh sách link từ file batdongsan_links.json
with open('data/batdongsan_links.json', 'r', encoding='utf-8') as f:
    results = json.load(f)
# Lọc link trùng theo detail_link
unique_links = {}
for item in results:
    unique_links[item['detail_link']] = item
results = list(unique_links.values())
print(f"Số link duy nhất: {len(results)}")

# Đa luồng crawl chi tiết
all_data = []
def crawl_and_collect(item):
    url = item['detail_link']
    try:
        data = crawl_bds_detail_selenium(url)
        print(f"Đã crawl: {url}")
        return data
    except Exception as e:
        print(f"Lỗi khi crawl {url}: {e}")
        return None

max_workers = 10  # Tùy máy, có thể tăng lên 6-8 nếu RAM khỏe
with ThreadPoolExecutor(max_workers=max_workers) as executor:
    futures = [executor.submit(crawl_and_collect, item) for item in results]
    for idx, future in enumerate(as_completed(futures)):
        data = future.result()
        # Chỉ lưu nếu data có đủ thông tin (ví dụ có tiêu đề hoặc địa chỉ, hoặc có ít nhất 3 trường)
        if data and len(data.keys()) > 1:
            all_data.append(data)
            with open('data/batdongsan_details.json', 'w', encoding='utf-8') as f:
                json.dump(all_data, f, ensure_ascii=False, indent=2)
        else:
            print(f"Bỏ qua trang không lấy được dữ liệu hoặc dữ liệu thiếu: {results[idx+1]['detail_link']}")
        print(f"Tiến độ: {idx+1}/{len(results)}")

print(f"Đã lưu {len(all_data)} kết quả vào data/batdongsan_details.json")
