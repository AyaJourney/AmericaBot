import requests
import base64

# CRM_BASE = "http://localhost:3000"
CRM_BASE = "https://crm.ayajourney.com"


def send_captcha(image_bytes, job_id):
    encoded = base64.b64encode(image_bytes).decode()

    requests.post(
        f"{CRM_BASE}/api/internal/bot/captcha",
        json={
            "job_id": job_id,
            "image": encoded
        }
    )
