from http.client import PROXY_AUTHENTICATION_REQUIRED
import json
from posixpath import split
import time
import os
import logging

from zapv2 import ZAPv2
import importlib

from dotenv import load_dotenv

import export_reports



def new_context(zap, domain):
    """
    Creates a new context in zap for the particular scan.
    """
    zap.context.new_context(domain+"_authenticated_scan")
    #returning context name. In case this code changes.
    return domain+"_authenticated_scan"
    

def cookieauth(zap,contextID,domain):
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

def tokenauth(zap, contextID, domain):
    """
    Sets up the ZAP context to use tokens for authentication.
    Only works if the token has been put in the sessid cookie.
    """
    username = "testuser"
    zap.users.new_user(contextID, username)
    userid = zap.users.users_list(contextID)[0]["id"]

    #ZAP needs the port, if testing locally over a different port, update this value.
    sessions = zap.httpsessions.sessions(site = domain)

    #sessid is identified by ZAP as a session cookie by default. 
    #It probably makes sense to have the cookie used be controlled by config.
    try:
        token = sessions[-1]["session"][1]["sessid"]["value"]
    except:
        logging.info("Failed to find cookie with token")
        
    #the token auth script is general purpose, as long as the sessid cookie is used for storing the token.
    #This works when ZAP is local.
    cwd = os.getcwd()
    scriptlocation = cwd + "/scripts/token_auth.js"
    scriptname = "token_auth.js"
    zap.script.load(scriptname,"httpsender","ECMAScript : Oracle Nashorn",scriptlocation)


    zap.script.set_global_var("token",token)

    zap.users.set_user_enabled(contextID,userid,True)
    zap.forcedUser.set_forced_user(contextID,userid)
    zap.forcedUser.set_forced_user_mode_enabled(True)
    zap.script.enable(scriptname)
    return username, userid, scriptname


def pullReport(zap, context, url, site):
    """
    Requests report from ZAP and saves it in the directory specified.
    Directory must be local to ZAP.
    """
    template = "traditional-xml"
    logging.info("arguements: title : "+site+", template : "+template+", contexts : "+context+", sites : "+url)
    returnvalue=zap.reports.generate(title=site, template=template, contexts=context, sites=url,reportdir= os.getenv("REPORT_DIR"))
    return returnvalue


def loginAndScan(proxy, script, env, project, dojo_id):
    """
    Calls the login function for the site being scanned, 
    and then runs crawlers and scans against it.
    """
    module = importlib.import_module("logins." + script)
    login = getattr(module, "login")

    #all sites will need to connect to zap and create a context.
    zap = ZAPv2(proxies={"http": proxy, "https": proxy})
    context = new_context(zap, script)
    contextID = zap.context.context(context)["id"]
    zap.authentication.set_authentication_method(contextID,"manualAuthentication")
    
    site, authtype, logged_in=login(proxy,env,script)
    if logged_in == False:
        logging.info("Failed to login, no scan will be performed for "+script)
        return

    logging.info("site is:"+ site)
    domain = site.split(":")[0]
    zap.context.include_in_context(context, ".*" + domain + ".*")
    

    #There's probably a way to make this better. probably by putting it in the login script
    zap.context.exclude_from_context(context, ".*/login.*")
    zap.context.exclude_from_context(context, ".*/logout.*")
    zap.context.exclude_from_context(context, ".*/complete.*")

    if authtype == "cookie":
        userName, userId=cookieauth(zap, contextID, site)
    elif authtype == "token":
        userName, userId, scriptname=tokenauth(zap, contextID, site)
   
    #passive scan
    zap.pscan.enable_all_scanners()
   
    #run spider
    zap.spider.scan_as_user(contextID, userId, "https://"+site)
    time.sleep(5)
    while (zap.spider.status == "running"):
        logging.debug("Spider still running")
        time.sleep(5)
    logging.info("Spider complete")

    #run ajax spider
    #this needs to be configurable.
    zap.ajaxSpider.set_option_max_duration(4)
    zap.ajaxSpider.scan_as_user(context, userName, "https://"+site)
    time.sleep(10)
    count=0
    while (zap.ajaxSpider.status == "running"):
        logging.debug("Ajax Spider still running")
        time.sleep(10)
        count=count+1
        if count > 24:
            zap.ajaxSpider.stop()
    logging.info("Ajax Spider complete")

    # #Run active scan as the authenticated user.
    zap.ascan.scan_as_user(contextid=contextID, userid=userId)
    time.sleep(60)
    while (zap.ascan.status() != "100"):
        status=zap.ascan.status()
        logging.info(status)
        time.sleep(5)
    logging.info("Active scanner complete")

    reportFile = pullReport(zap, context, "https://" + site, site)
    export_reports.codedx_upload(project,reportFile)
    export_reports.defectdojo_upload(dojo_id, reportFile, os.getenv("DOJO_KEY"), os.getenv("DOJO_USER"),"http://defectdojo.defectdojo.svc.cluster.local")

    zap.forcedUser.set_forced_user_mode_enabled(False)

    if authtype == "token":
        zap.script.disable(scriptname)

def testScan(proxy, script, env, project, dojo_id):
    """
    Calls the login function for the site being scanned, 
    and runs the spider. It does not run attacks or generate a report.
    """
    module = importlib.import_module("logins." + script)
    login = getattr(module, "login")

    #all sites will need to connect to zap and create a context.
    zap = ZAPv2(proxies={"http": proxy, "https": proxy})
    context = new_context(zap, script)
    contextID = zap.context.context(context)["id"]
    zap.authentication.set_authentication_method(contextID,"manualAuthentication")
    
    site, authtype, logged_in=login(proxy,env,script)
    if logged_in == False:
        logging.info("Failed to login, no scan will be performed for "+script)
        return

    logging.info("site is:"+ site)
    domain = site.split(":")[0]
    zap.context.include_in_context(context, ".*" + domain + ".*")
    

    #There's probably a way to make this better. probably by putting it in the login script
    zap.context.exclude_from_context(context, ".*/login.*")
    zap.context.exclude_from_context(context, ".*/logout.*")
    zap.context.exclude_from_context(context, ".*/complete.*")

    if authtype == "cookie":
        userName, userId=cookieauth(zap, contextID, site)
    elif authtype == "token":
        userName, userId, scriptname=tokenauth(zap, contextID, site)
   
    #passive scan
    zap.pscan.enable_all_scanners()
   
    #run spider
    zap.spider.scan_as_user(contextID, userId, "https://"+site)
    time.sleep(5)
    while (zap.spider.status == "running"):
        logging.debug("Spider still running")
        time.sleep(5)
    logging.info("Spider complete")



    reportFile = pullReport(zap, context, "https://" + domain, domain)
    export_reports.codedx_upload(project,reportFile)
    export_reports.defectdojo_upload(dojo_id, reportFile, os.getenv("DOJO_KEY"), os.getenv("DOJO_USER"),"http://defectdojo.defectdojo.svc.cluster.local")



    zap.forcedUser.set_forced_user_mode_enabled(False)

    if authtype == "token":
        zap.script.disable(scriptname)

if __name__ == "__main__":
    #attempt to wait to initialize zap
    #If running locally, this can be commented out.
    time.sleep(20)

    #For local testing
    #load_dotenv("test.env")
    proxy = str(os.getenv("PROXY")) + ":" + str(os.getenv("PORT"))
     
    if (os.getenv("DEBUG")=="debug"):
       
        logging.basicConfig(level="INFO")
        logging.info(proxy)
        logging.info("Test scan running")

        f = open("test_sites.json", "r")
        sites = json.load(f)
        for elem in sites:
            logging.info("Starting scan for "+elem["site"])
            testScan(proxy, elem["login"], elem["env"], elem["codedx"],elem["dojo_id"])

    else:
        logging.basicConfig(level="INFO")
        logging.info(proxy)
   
    
        f = open("sites.json", "r")
        sites = json.load(f)
        for elem in sites:
            logging.info("Starting scan for "+elem["site"])
            loginAndScan(proxy, elem["login"], elem["env"], elem["codedx"],elem["dojo_id"])

    logging.info("All test complete")

   
    
    