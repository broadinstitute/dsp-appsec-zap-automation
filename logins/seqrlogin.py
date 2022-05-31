from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
import os


def set_chrome_options(proxy) -> None:
    """Adds chrome options. 
    Proxy is required for sending the traffic through ZAP.
    """
    chrome_options = Options()
    #When using this in a container, uncomment the lines below
    #chrome_options.add_argument("--headless")
    #chrome_options.add_argument("--no-sandbox")
    #chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument('--proxy-server='+ proxy)
    chrome_options.add_argument('--allow-insecure-localhost')
    return chrome_options

def login(proxy, env, site):
    """
    Webdriver script for logging into seqr. 
    """
    caps = webdriver.DesiredCapabilities.CHROME.copy() 
    caps['acceptInsecureCerts'] = True
    driver = webdriver.Chrome(options=set_chrome_options(proxy), desired_capabilities=caps)


    domain="seqr-"+env+".broadinstitute.org:443"
    url="https://"+domain
    authtype="cookie"

    max_retries = int(os.getenv("MAX_RETRIES", '3'))
    logged_in=False

    for attempt in range(max_retries):
        try:
            driver.get(url)
            driver.add_cookie({"name": "accepted_cookies", "value": "true"})
            driver.get(url)
            expected_conditions.title_is("seqr: Dashboard")
            driver.find_element(by=By.LINK_TEXT, value="Log in").click()
            #next page. should be google login.
            expected_conditions.title_is("Sign in - Google Accounts")
            
            driver.find_element(by=By.ID, value="identifierId").send_keys(os.getenv("SEQR_LOGIN"))
            driver.find_element(by=By.ID, value="identifierNext").click()
            #what in the what is the double parens.
            driver.implicitly_wait(3)
            expected_conditions.presence_of_element_located((By.NAME, "password"))
            driver.implicitly_wait(6)
            driver.find_element(by=By.NAME, value="password").send_keys(os.getenv("SEQR_PASS"))
            driver.implicitly_wait(3)
            driver.find_element(by=By.ID, value="passwordNext").click()
            
            expected_conditions.title_contains("seqr")
            expected_conditions.presence_of_all_elements_located((By.LINK_TEXT,"Summary Data"))
            driver.find_element(by=By.LINK_TEXT, value="Summary Data").click()
            driver.implicitly_wait(10)


        except Exception as err:
            print("Exception occurred: {0}".format(err))
        else:
            print("logged in")
            logged_in=True
            break
    driver.close()
    return domain, authtype, logged_in


