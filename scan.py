from http.client import PROXY_AUTHENTICATION_REQUIRED
import json
from posixpath import split
import time
import os
import logging

from zapv2 import ZAPv2
import importlib

from dotenv import load_dotenv




def new_context(zap, context_name):
    """
    Creates a new context in zap for a given scan.
    """
    if context_name == None:
        context_name = "default"
    zap.context.new_context(context_name)
    return context_name


def load_sites():
    f = open("sites.json", "r")
    sites = json.load(f)
    return sites


def load_test_sites():
    f = open("test_sites.json", "r")
    sites = json.load(f)
    return sites

    
def parse_site(site):
    site_name = elem["site"]
    login_script_name = elem["login"]
    environment = elem["env"]

    return site_name, login_script_name, environment


def cookieauth(zap, contextID, domain):
    """
    Sets up the ZAP context to use cookies for authentication.
    Only works if the cookie used by the app is recognized as a session cookie by ZAP.
    """
    username = "testuser"
    zap.users.new_user(contextID, username)
    userid = zap.users.users_list(contextID)[0]["id"]
    #this is the secret sauce for using cookies. The user above is now associated with the active cookie.
    #It should always choose the newest one.
    sessions=zap.httpsessions.sessions(site = domain)
    sessionName=sessions[-1]["session"][0]
    zap.users.set_authentication_credentials(contextID,userid,"sessionName=" + sessionName)

    zap.users.set_user_enabled(contextID,userid,True)
    zap.forcedUser.set_forced_user(contextID,userid)
    zap.forcedUser.set_forced_user_mode_enabled(True)
    return username, userid


def tokenauth(zap, context, token, name="auth"):
    """
    Sets up the ZAP context to use tokens for authentication.
    Only works if the token has been put in the sessid cookie.
    """
    username = "testuser"
    contextID = zap.context.context(context)["id"]
    zap.users.new_user(contextID, username)
    userid = zap.users.users_list(contextID)[0]["id"]
        
    # Replacer set up
    results = zap.context.context(context)
    include_string = results["includeRegexs"]

    include_string = include_string.lstrip("[")
    include_string = include_string.rstrip("]")
    templist = include_string.split(",")
    url_regx = ""
    for elem in templist:
        elem = elem.strip('"')
        url_regx = url_regx + f"|{elem}"
    url_regx = url_regx.lstrip("|")

    bearer = f"Bearer {token}"
    zap.replacer.remove_rule("auth")
    zap.replacer.add_rule(
        description=name,
        enabled=True,
        matchtype="REQ_HEADER",
        matchregex=False,
        matchstring="Authorization",
        replacement=bearer,
        url=url_regx
    )
    return username, userid


def localPullReport(zap, context, url, site, reportDir):
    """
    Requests report from ZAP and saves it in the directory specified.
    Directory must be local to ZAP.
    """
    template = "traditional-xml"
    reportDir = reportDir + '/' + site
    logging.info("Pulling report with following arguements: title : "+site+", template : "+template+", contexts : "+context+", sites : "+url)
    os.mkdir(reportDir)
    returnvalue=zap.reports.generate(title=site, template=template, contexts=context, sites=url,reportdir= reportDir)
    return returnvalue


def login(proxy, script, env):
    """
    Calls the login function for the site being scanned
    """

    #all sites will need to connect to zap and create a context.
    zap = ZAPv2(proxies={"http": proxy, "https": proxy})
    context = script
    contextID = zap.context.context(context)["id"]
    zap.authentication.set_authentication_method(contextID,"manualAuthentication")

    logged_in = False
    module = importlib.import_module("logins." + script)
    login = getattr(module, "login")
    site, authtype, logged_in=login(proxy,env,script)
    if logged_in == False:
        logging.info("Failed to login, no scan will be performed for "+script)
        return logged_in, "", ""

    logging.info("site is:"+ site)
    domain = site.split(":")[0]
    zap.context.include_in_context(context, ".*" + domain + ".*")
    

    #There's probably a way to make this better. probably by putting it in the login script
    zap.context.exclude_from_context(context, ".*/login.*")
    zap.context.exclude_from_context(context, ".*/logout.*")
    zap.context.exclude_from_context(context, ".*/complete.*")

    if authtype == "cookie":
        _, userId = cookieauth(zap, contextID, site)
    elif authtype == "token":
        sessions = zap.httpsessions.sessions(site = domain)

        try:
            token = sessions[-1]["session"][1]["sessid"]["value"]
        except:
            logging.info("Failed to find cookie with token")
        _, userId = tokenauth(zap, context, token=token)
    
    return logged_in, domain, userId

def crawl(proxy, context, domain):
    """
    Runs the crawlers and passive scanner
    """
    zap = ZAPv2(proxies={"http": proxy, "https": proxy})
    contextID = zap.context.context(context)["id"]
    #passive scan
    zap.pscan.enable_all_scanners()

        #run spider
    zap.spider.scan(recurse=True, contextname=context, url="https://"+domain)
    time.sleep(5)
    while (zap.spider.status == "running"):
        logging.debug("Spider still running")
        time.sleep(5)
    logging.info("Spider complete")

    #run ajax spider
    #this needs to be configurable.
    zap.ajaxSpider.set_option_max_duration(4)
    zap.ajaxSpider.scan(contextname=context, url="https://"+domain)
    time.sleep(10)
    count=0
    while (zap.ajaxSpider.status == "running"):
        logging.debug("Ajax Spider still running")
        time.sleep(10)
        count=count+1
        if count > 24:
            zap.ajaxSpider.stop()
    logging.info("Ajax Spider complete")

    # Do our best to finish passive scans first.
    while(int(zap.pscan.records_to_scan) > 0):
        time.sleep(10)
    return


def scan(proxy, context, domain):
    """
    Runs the crawlers and active scanner
    """
    zap = ZAPv2(proxies={"http": proxy, "https": proxy})
    contextID = zap.context.context(context)["id"]

    # Run active scan as the authenticated user.
    zap.ascan.scan(url="https://"+domain, contextid=contextID)
    time.sleep(60)
    while (zap.ascan.status() != "100"):
        status=zap.ascan.status()
        logging.info("Active scan is at this percentage:" + status)
        time.sleep(10)
    logging.info("Active scanner complete")

    return



if __name__ == "__main__":
    #attempt to wait to initialize zap
    #If running locally, this can be commented out.
    #time.sleep(40)

    #For local testing
    load_dotenv("test.env")
    proxy = str(os.getenv("PROXY")) + ":" + str(os.getenv("PORT"))
    zap = ZAPv2(proxies={"http": proxy, "https": proxy})
    sites = {}
     
    if (os.getenv("DEBUG")=="debug"):
        sites = load_test_sites()
    else:
        sites = load_sites()
    
    logging.basicConfig(level="INFO")
    logging.info(proxy)

    zap.core.new_session(name="Untitled Session", overwrite=True)
    for elem in sites:
        site_name, login_script_name, environment = parse_site(elem)
        

        logging.info("Starting scan for " + site_name)
        context = new_context(zap, login_script_name)

        success, domain, userId = login(proxy, login_script_name, environment)
        if success:
            crawl(proxy, context, domain)
            if (os.getenv("DEBUG") != "debug"):
                scan(proxy, context, domain)
            try:
                reportFile = localPullReport(zap, context, "https://" + domain, site_name, os.getenv("REPORT_DIR"))
            except Exception:
                logging.error("Failed to pull report for scan.")
    

        zap.replacer.remove_rule("auth")

        zap.forcedUser.set_forced_user_mode_enabled(False)
        zap.context.remove_context(context)
        zap.core.run_garbage_collection()
        zap.core.new_session(name="Untitled Session", overwrite=True)

    logging.info("All tests complete")

   
    
    