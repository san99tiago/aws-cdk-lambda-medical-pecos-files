# Built-in imports
from sys import platform
import glob
import time
from unittest import result

# External imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

from selenium.webdriver.common.action_chains import ActionChains

from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--enable-javascript")
chrome_options.add_argument("--disable-gpu")


if platform == "linux":
    print("Configuring Linux driver...")
    chrome_options.binary_location = "/opt/chrome/chrome"
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--single-process")
    chrome_options.add_argument("--user-data-dir=/tmp/chrome-user-data")
    # chrome_options.add_argument("--disable-dev-tools")
    # chrome_options.add_argument("--no-zygote")
    # chrome_options.add_argument("--single-process")
    # chrome_options.add_argument("window-size=2560x1440")
    # chrome_options.add_argument("--user-data-dir=/tmp/chrome-user-data")
    # chrome_options.add_argument("--remote-debugging-port=9222")
    prefs = {
        "profile.default_content_setting_values.automatic_downloads": 1,
        "download.default_directory": "/tmp/test0001"
    }
    chrome_options.add_experimental_option("prefs", prefs)
elif platform == "win32":
    prefs = {
        "profile.default_content_setting_values.automatic_downloads": 1,
    }
    chrome_options.add_experimental_option("prefs", prefs)
    print("Configuring Windows driver...")
else:
    print("Your OS platform ({}) is not supported!".format(platform))
    exit()

# Must enable JavaScript to run driver on this target page
# driver = webdriver.Chrome("/opt/chromedriver", service=Service(ChromeDriverManager().install()), options=chrome_options)
driver = webdriver.Chrome("/opt/chromedriver", options=chrome_options)


def simple_wait(seconds_to_wait=3):
    """
    Simple function to wait N amount of seconds.
    """
    print("Waiting for {} seconds...".format(seconds_to_wait))
    time.sleep(seconds_to_wait)


driver.get("https://data.cms.gov/provider-characteristics/medicare-provider-supplier-enrollment/medicare-fee-for-service-public-provider-enrollment")
print("Site title is: {}".format(driver.title))

driver.maximize_window()

simple_wait(1)

# The following "XPATH" was found with "inspect" and on the "link" item, right ...
# ... click and then "Copy XPath" option and modifying the first div with "*" ...
# ... this was done for both options of links (that's why the "|" (OR) expression)
results = []
results.extend(driver.find_elements(By.XPATH, "//*[@id='DatasetPage']/div[1]/div[2]/div/div/div[3]/button/span[2]"))
# results.extend(driver.find_elements(By.CSS_SELECTOR, ".btn.btn-link.btn-lg"))
print("Results: ", results)

print("Found results were {} and they are:".format(len(results)))
for i in range(len(results)):
    print(results[i].text)

download_element = results[0]

driver.execute_script("window.scrollTo(0, 200)")

simple_wait(1)

results[0].click()

simple_wait(1)


results = driver.find_elements(By.CLASS_NAME, "DownloadModal__form-section-latest.DownloadModal__form-section-inner")
print(results[0].text)

current_documents_version = results[0].text
print("current_documents_version: ", current_documents_version)
current_q = current_documents_version.split(" ")[0]
current_year = current_documents_version.split(" ")[1]
print("current_q: ", current_q)
print("current_year: ", current_year)


checkbox_items = driver.find_elements(By.XPATH, "//*/ul/li[*]/label")
print(checkbox_items)

driver.execute_script("arguments[0].scrollIntoView();", checkbox_items[0])

simple_wait()

for i in range(len(checkbox_items)):
    print("Clicking element: ", checkbox_items[i])
    checkbox_items[i].click()
    simple_wait(1)

main_download_button = driver.find_element(By.XPATH, "//*[contains(text(), 'Download Files')]")
print(main_download_button)

main_download_button.click()

simple_wait(180)

driver.quit()
