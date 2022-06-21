import os
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time
from zapv2 import ZAPv2


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



def login(proxy, env,site):
    """
    Webdriver script for logging into the angio project for ddp. 
    Sets the bearer token value to the sessid cookie. 
    """

    zap = ZAPv2(proxies={"http": proxy, "https": proxy})

    caps = webdriver.DesiredCapabilities.CHROME.copy() 
    caps['acceptInsecureCerts'] = True
    driver = webdriver.Chrome(options=set_chrome_options(proxy), desired_capabilities=caps)

    
    domain="angio."+env+".datadonationplatform.org:443"
    url="https://"+domain
    zap.context.include_in_context(site+"_authenticated_scan", ".*pepper-"  + env + ".datadonationplatform.org.*")

    authtype="token"
    max_retries = int(os.getenv("MAX_RETRIES", '3'))
    logged_in=False

    for attempt in range(max_retries):
        try:
            driver.get(url)
            #The sleeps are to allow the angular page to fully load. Webdriver has issues wihout them.
            time.sleep(1)
            driver.add_cookie({"name": "pepper.ANGIO.irbsession", "value": "LOGGEDIN"})
            driver.get(url)
            time.sleep(10)
            time.sleep(3)
            time.sleep(2)
            driver.execute_script('document.querySelector("body > app-root > mat-sidenav-container > mat-sidenav-content > div > app-welcome > toolkit-header > mat-toolbar > nav > ul > li.Header-navItem.user-menu-header.ng-star-inserted > ddp-user-menu > ddp-sign-in-out > button").click()')
            time.sleep(2)
            time.sleep(2)
            time.sleep(6)
            expected_conditions.title_is("Count Me In")
            driver.find_element(by=By.NAME, value="email").send_keys(os.getenv("DDP_USER"))
            driver.find_element(by=By.NAME, value="password").send_keys(os.getenv("DDP_PASS"))
            driver.find_element(by=By.CLASS_NAME, value="auth0-lock-submit").click()
            time.sleep(1)
            expected_conditions .title_is("Angiosarcoma Project")
            time.sleep(1)
            time.sleep(8)
            #need to stick bearer token into a cookie.
            token=driver.execute_script("return localStorage.getItem(\"token\")")
            driver.execute_script('document.cookie="sessid='+token+'"')
            driver.get(url+"/dashboard")
            time.sleep(2)
        except Exception as err:
            print("Exception occurred: {0}".format(err))
        else:
            print("logged in")
            logged_in=True
            break

    driver.close()
    return domain, authtype, logged_in

