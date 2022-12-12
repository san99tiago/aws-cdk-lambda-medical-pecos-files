# Built-in imports
import os
import glob
import boto3
from sys import platform

# External imports
from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# Own dependencies
import waiter
import s3_helpers
import send_emails_ses


################################################################################
# GLOBAL VARIABLES TO CONFIGURE SOLUTION
# CHROME DRIVER PATH
CHROME_DRIVER_PATH = "/opt/chromedriver"

# URL SITE CONFIGURATIONS
MAIN_URL = os.environ.get("MAIN_URL")

# AWS CONFIGURATIONS
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")  # "<ACCOUNT_NUMBER>-pecos-prod-cms-files"
OUTPUT_FOLDER = os.environ.get("OUTPUT_FOLDER")  # "/tmp/files"

# EMAIL CONFIGURATIONS
FROM_EMAIL = os.environ.get("FROM_EMAIL")  # "san99tiagodevsecops2@gmail.com"
TO_EMAILS_LIST = os.environ.get("TO_EMAILS_LIST").split(",")  # "san99tiagodevsecops@gmail.com,san99tiagodevsecops2@gmail.com"
SES_CONFIG_SET_NAME = os.environ.get("SES_CONFIG_SET_NAME")  # "npi-emails"
################################################################################


# AWS resources and clients (best practice is to keep outside handler for efficiency)
s3_client = boto3.client("s3")
s3_resource = boto3.resource("s3")
ses_client = boto3.client('ses')


# Chrome and ChromeDriver Selenium configurations
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
    prefs = {
        "profile.default_content_setting_values.automatic_downloads": 1,
        "download.default_directory": OUTPUT_FOLDER,
    }
    chrome_options.add_experimental_option("prefs", prefs)
elif platform == "win32":
    print("Configuring Windows driver...")
else:
    print("Your OS platform ({}) is not supported!".format(platform))
    exit()

# Must enable JavaScript to run driver on this target page
# driver = webdriver.Chrome(CHROME_DRIVER_PATH, service=Service(ChromeDriverManager().install()), options=chrome_options)
driver = webdriver.Chrome(CHROME_DRIVER_PATH, options=chrome_options)


def handler(event, context):
    """
    Main lambda handler function.
    """
    print("Event is:")
    print(event)
    print("Context is:")
    print(context)

    # Getting initial information from scrape page
    print("Starting chrome/chromedriver selenium process")
    driver.get(MAIN_URL)
    print("Site title is: {}".format(driver.title))

    driver.maximize_window()

    waiter.simple_wait(5)

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

    print("results[0]: ", results[0])

    driver.execute_script("window.scrollTo(0, 200)")

    waiter.simple_wait(1)

    results[0].click()

    waiter.simple_wait(1)

    # Get main "Qx yyyy" title to see if it necessary to download again
    results = driver.find_elements(By.CLASS_NAME, "DownloadModal__form-section-latest.DownloadModal__form-section-inner")
    current_documents_version = results[0].text
    print("current_documents_version: ", current_documents_version)
    current_q = current_documents_version.split(" ")[0]
    current_year = current_documents_version.split(" ")[1]
    print("current_q: ", current_q)
    print("current_year: ", current_year)


    # Get existing files names (the ones already downloaded in S3 bucket)
    existing_files_in_s3 = s3_helpers.get_all_files_from_s3(s3_resource, S3_BUCKET_NAME)
    print("Existing files in s3 are: {}".format(existing_files_in_s3))

    # Validate if current found version exists in S3 bucket
    already_downloaded = False
    for file in existing_files_in_s3:
        if "{}/{}".format(current_year, current_q) in file:
            print("Found same version already downloaded in S3 bucket")
            already_downloaded = True

    if already_downloaded:
        # If file already exists (inform duplicate)...
        message_title_to_send = "PECOS quarterly data already downloaded"
        message_body_to_send = "The PECOS quarterly data for {}/{} was already downloaded before at ({})".format(current_year, current_q, S3_BUCKET_NAME)
    else:
        try:
            # Starting download process with the help of Selenium Chrome Driver
            print("New data found: starting download process with ChromeDriver")
            checkbox_items = driver.find_elements(By.XPATH, "//*/ul/li[*]/label")
            print(checkbox_items)

            driver.execute_script("arguments[0].scrollIntoView();", checkbox_items[0])

            waiter.simple_wait()

            for i in range(len(checkbox_items)):
                print("Clicking element: ", checkbox_items[i])
                checkbox_items[i].click()
                waiter.simple_wait(1)

            main_download_button = driver.find_element(By.XPATH, "//*[contains(text(), 'Download Files')]")
            print(main_download_button)

            main_download_button.click()

            waiter.simple_wait(180)

            print("already_downloaded_files: ", glob.glob("{}/*".format(OUTPUT_FOLDER)))

            waiter.simple_wait(5)

            driver.quit()

            print("The download was successful and the temp folder is: {}".format(OUTPUT_FOLDER))

            # Upload all files to S3 bucket
            uploaded_files = []
            for file in glob.glob("{}/*".format(OUTPUT_FOLDER)):
                print("Starting upload of file: ", file)
                downloaded_file_stats = os.stat(file)
                file_size_in_mb = downloaded_file_stats.st_size / (1024 * 1024)
                print("Downloaded file: ({}), with size ({} MB) and you can find it at the s3 bucket ({}).".format(file, file_size_in_mb, S3_BUCKET_NAME))
                s3_path = "{}/{}/{}".format(current_year, current_q, os.path.basename(file))
                s3_helpers.upload_file_to_s3(s3_client, S3_BUCKET_NAME, file, s3_path)
                uploaded_files.append(os.path.basename(file))
            message_title_to_send = "New PECOS quarterly data downloaded successfully!"
            message_body_to_send = "The PECOS quarterly data found is new and was successfully downloaded in the S3 bucket ({}) at the path ({}/{}/). The gathered files are ({})".format(S3_BUCKET_NAME, current_year, current_q, uploaded_files)
        except Exception as e:
            print(e)
            message_title_to_send = "PECOS quarterly data had an automation error"
            message_body_to_send = "The PECOS quarterly data for {}/{} had an automation error (contact developer)".format(current_year, current_q)

    # Send e-mail based on process workflow and messages
    print("Starting e-mail process with SES...")
    print("Message title: {}".format(message_title_to_send))
    print("Message body: {}".format(message_body_to_send))
    print(send_emails_ses.email_handler(FROM_EMAIL, TO_EMAILS_LIST, ses_client, SES_CONFIG_SET_NAME, message_title_to_send, message_body_to_send))

    return {
        'statusCode': 200,
        'body': message_body_to_send
    }


## ONLY FOR LOCAL TESTS! (OWN COMPUTER VALIDATIONS)
if __name__ == "__main__":
    # TESTS
    import os
    os.environ["MAIN_URL"] = "https://data.cms.gov/provider-characteristics/medicare-provider-supplier-enrollment/medicare-fee-for-service-public-provider-enrollment"
    os.environ["S3_BUCKET_NAME"] = "pecos-quarterly-data-185855006690"
    os.environ["OUTPUT_FOLDER"] = "/tmp/files"
    os.environ["FROM_EMAIL"] = "san99tiagodevsecops2@gmail.com"
    os.environ["TO_EMAILS_LIST"] = "san99tiagodevsecops@gmail.com,san99tiagodevsecops2@gmail.com"
    os.environ["SES_CONFIG_SET_NAME"] = "npi-emails"
    print(handler({"info": "fake event for local validations"}, None))
