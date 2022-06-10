import os
import time
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.common.by import By
from zapv2 import ZAPv2



def set_chrome_options(proxy) -> None:
    """Adds chrome options. 
    Proxy is required for sending the traffic through ZAP.
    """
    chrome_options = Options()
    #When using this in a container, uncomment the lines below
    #chrome_options.add_argument("--headless")
    #chrome_options.add_argument("--no-sandbox")
    #chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--proxy-server="+ proxy)
    chrome_options.add_argument("--allow-insecure-localhost")
    return chrome_options



def login(proxy, env, site):
    """
    Webdriver script for logging in to a website. 
    Sets the bearer token value to the sessid cookie. 
    """
    #allows you to use an untrusted cert with your proxy
    caps = webdriver.DesiredCapabilities.CHROME.copy() 
    caps["acceptInsecureCerts"] = True
    driver = webdriver.Chrome(options=set_chrome_options(proxy), desired_capabilities=caps)

    #Ensures that 'sessId' is in the default token list
    zap = ZAPv2(proxies={"http": proxy, "https": proxy})
    cookieName="sessId"
    zap.httpsessions.add_default_session_token(cookieName)


    #There's some flexibility here. env could contain the entire domain of your site.
    #Or env could contain just the part that changes between testing environments.
    domain=os.getenv("JUICESHOP_DOMAIN")
    url = "http://" + domain + "/#/login"
    authtype = "token"
    max_retries = int(os.getenv("MAX_RETRIES", "1"))
    logged_in = False

    for attempt in range(max_retries):
        try:
            driver.get(url)
            #Your webdriver code goes here. 
            #It should log into the website.
            driver.execute_script("document.cookie='welcomebanner_status=dismiss';")
            driver.get(url)
            time.sleep(2)
            driver.find_element(by=By.ID,value="email").send_keys(os.getenv("JUICESHOP_USER"))
            driver.find_element(by=By.ID,value="password").send_keys(os.getenv("JUICESHOP_PASS"))
            driver.find_element(by=By.ID,value="loginButton").click()
            time.sleep(2)
            #Once logged in the bearer token needs to be put somewhere ZAP can see it.
            #This tool uses the sessid cookie for this purpose.
            #You will need to grab the token from where ever it is in the browser.
            token = driver.get_cookie("token")
            driver.execute_script("document.cookie='sessid=" + token["value"] + "'")
            #This request is to show the set cookie to ZAP.
            driver.get(url + "/")
            time.sleep(2)
        except Exception as err:
            print("Exception occurred: {0}".format(err))
        except:
            print("Login failed. Attempt no "+str(attempt+1))
        else:
            print("logged in")
            logged_in = True
            break

    driver.close()
    return domain, authtype, logged_in

