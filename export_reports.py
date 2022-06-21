import os
import logging
from google.cloud import storage


from codedx_api.CodeDxAPI import CodeDx  # pylint: disable=import-error
import defectdojo_api as defectdojo

#tool for exporting reports to the correct location.

def codedx_upload(project: str, filename: str):
    """
    Create CodeDx project if needed and trigger analysis on the uploaded file.
    """
    project = 111
    codedx_url = "https://codedx.dsp-appsec-dev.broadinstitute.org/codedx/"
    codedx_api_key = os.getenv("CODEDX_API_KEY")
    
    cdx = CodeDx(codedx_url, codedx_api_key)

    cdx.analyze(project, filename)



def defectdojo_upload(engagement_id: int, zap_filename: str, defect_dojo_key: str, defect_dojo_user: str, defect_dojo: str):  # pylint: disable=line-too-long
    """
    Upload Zap results in DefectDojo engagement
    """
    dojo = defectdojo.DefectDojoAPIv2(
        defect_dojo, defect_dojo_key, defect_dojo_user, debug=False)

    absolute_path = os.path.abspath(zap_filename)

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


def upload_gcs(bucket_name: str, scan_type: ScanType, filename: str):
    """
    Upload scans to a GCS bucket and return the path to the file in Cloud Console.
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    date = datetime.today().strftime("%Y%m%d")
    path = f"{scan_type}-scans/{date}/{filename}"
    blob = bucket.blob(path)
    blob.upload_from_filename(filename)
    return f"https://console.cloud.google.com/storage/browser/_details/{bucket_name}/{path}"