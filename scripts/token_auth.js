/*
This file needs to be local and accessible to the ZAP instance you are using.

*/


function sendingRequest(msg, initiator, helper) {  
  var token = org.zaproxy.zap.extension.script.ScriptVars.getGlobalVar("token");

  if (msg.isInScope())
	{
	  msg.getRequestHeader().setHeader('Authorization', 'Bearer ' + token);
	} else {
    //Not in scope, don't add the header.
	}
  return msg;
}

function responseReceived(msg, initiator, helper) {
     return;
  }
 