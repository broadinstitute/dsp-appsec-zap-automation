from datetime import datetime
import os
import logging
from google.cloud import storage


from codedx_api.CodeDxAPI import CodeDx  # pylint: disable=import-error
import defectdojo_api.defectdojo_apiv2 as defectdojo

#tool for exporting reports to the correct location.

def codedx_upload(project: str, filename: str, env: str):
    """
    Create CodeDx project if needed and trigger analysis on the uploaded file.
    """

    codedx_url = "http://codedx.codedx.svc.cluster.local/codedx"
    codedx_api_key = os.getenv("CODEDX_API_KEY_"+env)
    
    cdx = CodeDx(codedx_url, codedx_api_key)

    cdx.analyze(project, filename)


def defectdojo_upload(product_id: int, zap_filename: str, defect_dojo_key: str, defect_dojo_user: str, defect_dojo: str):  # pylint: disable=line-too-long
    """
    Upload Zap results in DefectDojo engagement
    """
    dojo = defectdojo.DefectDojoAPIv2(
        defect_dojo, defect_dojo_key, defect_dojo_user, debug=False)

    absolute_path = os.path.abspath(zap_filename)

    #create engagement. 
    date = datetime.today().strftime("%Y%m%d%H:%M")

    try:
        lead_id = dojo.list_users(defect_dojo_user).data["results"][0]["id"]
    except:
        logging.error("Did not retrieve dojo user ID, upload failed.")
        return

    engagement=dojo.create_engagement( name=date, product_id=product_id, lead_id=lead_id,target_start=datetime.today().strftime("%Y-%m-%d"),target_end=datetime.today().strftime("%Y-%m-%d"), status="In Progress", active='True')
    print(engagement.data)
    engagement_id=engagement.data["id"]
    
    dojo_upload = dojo.upload_scan(engagement_id=engagement_id,
                     scan_type="ZAP Scan",
                     file=absolute_path,
                     active=True,
                     verified=False,
                     close_old_findings=True,
                     skip_duplicates=True,
                     scan_date=str(datetime.today().strftime('%Y-%m-%d')),
                     tags="Zap_scan")
    logging.info("Dojo file upload: %s", dojo_upload)

    dojo.close_engagement(engagement_id)
