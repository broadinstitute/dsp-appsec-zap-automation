
import logging
import os
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By


def set_chrome_options(proxy) -> None:
    """Adds chrome options. 
    Proxy is required for sending the traffic through ZAP.
    """
    chrome_options = Options()
    #When using this in a container, uncomment the lines below
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument('--proxy-server='+ proxy)
    chrome_options.add_argument('--allow-insecure-localhost')
    chrome_options.add_argument('--user-agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.61 Safari/537.36"')
    chrome_options.add_argument('--window-size=1600,1000')
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--lang=en")
    return chrome_options

def login(proxy, env, site):
    """
    Webdriver script for logging into dsm. 
    Sets the bearer token value to the sessid cookie. 
    """
    
    #TODO DSM login and UI have changed. Script needs to be updated.
    caps = webdriver.DesiredCapabilities.CHROME.copy() 
    caps['acceptInsecureCerts'] = True
    driver = webdriver.Chrome(options=set_chrome_options(proxy), desired_capabilities=caps)


    domain="dsm-"+env+".datadonationplatform.org:443"
    url="https://"+domain
    authtype="token"
    max_retries = int(os.getenv("MAX_RETRIES", '3'))
    logged_in=False

    for attempt in range(max_retries):
        try:
            driver.get(url)
            driver.find_element(by=By.LINK_TEXT,value="Log In").click()
            #
            driver.implicitly_wait(3)
            logging.info("Chrome driver found DSM login form")
            driver.implicitly_wait(10)
            expected_conditions.presence_of_element_located((By.NAME,"email"))
            driver.find_element(by=By.NAME,value="email").send_keys(os.getenv("DSM_USER"))
            driver.find_element(by=By.NAME, value="password").send_keys(os.getenv("DSM_PASS"))
            driver.find_element(by=By.CLASS_NAME, value="auth0-lock-submit").click()
            driver.implicitly_wait(10)
            expected_conditions.presence_of_element_located((By.LINK_TEXT,"Samples"))
            driver.find_element(by=By.LINK_TEXT, value="Samples").click()
            logging.info("Chrome Driver found link text 'Samples' after login.")
            token=driver.execute_script("return localStorage.getItem(\"dsm_token\")")
            driver.execute_script('document.cookie="sessid='+token+'"')
            driver.get(url+"/userSettings")
        except Exception as err:
            logging.error("Exception occurred: {0}".format(err))
        else:
            logging.info("Login script for DSM passed. User is now logged in.")
            logged_in=True
            break
    driver.close()
    return domain, authtype, logged_in

