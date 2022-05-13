import os
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
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
    chrome_options.add_argument('--proxy-server='+ proxy)
    chrome_options.add_argument('--allow-insecure-localhost')
    return chrome_options



def login(proxy, env):
    """
    Webdriver script for logging in to a website. 
    Sets the bearer token value to the sessid cookie. 
    """
    #allows you to use an untrusted cert with your proxy
    caps = webdriver.DesiredCapabilities.CHROME.copy() 
    caps['acceptInsecureCerts'] = True
    driver = webdriver.Chrome(options=set_chrome_options(proxy), desired_capabilities=caps)

    #Ensures that 'sessId' is in the default token list
    zap = ZAPv2(proxies={"http": proxy, "https": proxy})
    cookieName="sessId"
    zap.httpsessions.add_default_session_token(cookieName)

    #There's some flexibility here. env could contain the entire domain of your site.
    #Or env could contain just the part that changes between testing environments.
    #site needs to contain domain:port, such as localhost:3000 
    site=env
    url="https://"+site
    authtype="token"
    max_retries = int(os.getenv("MAX_RETRIES", '3'))
    logged_in=False

    for attempt in range(max_retries):
        try:
            driver.get(url)
            
            #Your webdriver code goes here. 
            #It should log into the website.

            #Once logged in the bearer token needs to be put somewhere ZAP can see it.
            #This tool uses the sessid cookie for this purpose.
            #You will need to grab the token from where ever it is in the browser.
            token=driver.execute_script("return localStorage.getItem(\"token\")")
            driver.execute_script('document.cookie="sessid='+token+'"')
            #This request is to show the set cookie to ZAP.
            driver.get(url+"/dashboard")

            #Optional check to make sure the cookie was seen by ZAP.
            # sessions=zap.httpsessions.sessions(site=domain)
            # sessions[-1]['session'][1]['sessid']['value']

        except Exception as err:
            print("Exception occurred: {0}".format(err))
        else:
            print("logged in")
            logged_in=True
            break

    driver.close()
    return site, authtype, logged_in

