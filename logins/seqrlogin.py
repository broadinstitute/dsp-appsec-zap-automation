import logging
import time
from dotenv import load_dotenv
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
import os
from zapv2 import ZAPv2


def set_chrome_options(proxy) -> None:
    """Adds chrome options. 
    Proxy is required for sending the traffic through ZAP.
    """
    chrome_options = Options()
    #When using this in a container, uncomment the lines below
    # chrome_options.add_argument("--headless")
    # chrome_options.add_argument("--no-sandbox")
    # chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument('--proxy-server='+ proxy)
    chrome_options.add_argument('--allow-insecure-localhost')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36')
    chrome_options.add_argument('--window-size=1300,9000')
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--lang=en")
    return chrome_options

def login(proxy, env, site):
    """
    Webdriver script for logging into seqr. 
    """
    caps = webdriver.DesiredCapabilities.CHROME.copy() 
    caps['acceptInsecureCerts'] = True
    driver = webdriver.Chrome(options=set_chrome_options(proxy), desired_capabilities=caps)

    #zap = ZAPv2(proxies={"http": proxy, "https": proxy})
    cookieName="sessionid"
    #zap.httpsessions.add_default_session_token(cookieName)



    domain="seqr-"+env+".broadinstitute.org:443"
    url="https://"+domain
    authtype="cookie"

    max_retries = int(os.getenv("MAX_RETRIES", '1'))
    logged_in=False

    for attempt in range(max_retries):
        try:

            driver.get(url)
            driver.add_cookie({"name": "accepted_cookies", "value": "true"})
            time.sleep(5)
            driver.get(url)
            expected_conditions.title_is("seqr: Dashboard")
            driver.find_element(by=By.LINK_TEXT, value="Log in").click()
            #next page. should be google login.
            expected_conditions.title_is("Sign in - Google Accounts")
            time.sleep(4)
            time.sleep(1)
            driver.find_element(by=By.ID, value="identifierId").send_keys(os.getenv("SEQR_USER"))
            time.sleep(3)
            driver.find_element(by=By.ID, value="identifierNext").click()
            #what in the what is the double parens.
            time.sleep(30)
            try:
                driver.findElement(By.xpath("//*[text()='This browser or app may not be secure']"))
                
            except:
                logging.info("SEQR user was not flagged as using an insecure browser")
            else:
                logging.error("Google flagged the browser as insecure, scan will not continue.")
                break
            try:
                driver.find_element(by=By.ID, value="password")                
            except:
                logging.error("Google is presenting a captcha, and scanning cannot continue")
                break
            else:
                logging.info("Login will continue to password form. Google is not presenting a captcha")
            #     #domstring=driver.execute_script("var xmlString = new XMLSerializer().serializeToString( document ); return xmlString;")
            #     #print(domstring)

            driver.implicitly_wait(3)
            expected_conditions.presence_of_element_located((By.NAME, "password"))
            driver.implicitly_wait(6)
            driver.find_element(by=By.NAME, value="password").send_keys(os.getenv("SEQR_PASS"))
            driver.implicitly_wait(3)
            driver.find_element(by=By.ID, value="passwordNext").click()
            
            expected_conditions.title_contains("seqr")
            expected_conditions.presence_of_all_elements_located((By.LINK_TEXT,"Summary Data"))
            driver.find_element(by=By.LINK_TEXT, value="Summary Data").click()

            time.sleep(20)


        except Exception as err:
            logging.error("Exception occurred: {0}".format(err))
        else:
            logging.info("SEQR login passed. User is now logged in")
            logged_in=True
            break
    driver.close()
    return domain, authtype, logged_in


if __name__ == "__main__":
    load_dotenv("../test.env")
    logging.basicConfig(level="INFO")
    login(os.getenv("PROXY")+":"+os.getenv("PORT"),"dev","seqr")