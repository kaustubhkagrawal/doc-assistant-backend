
from app.core.config import settings


def get_Document_url(bucket_name: str = settings.S3_ASSET_BUCKET_NAME, file_name: str = ''):
    return settings.S3_ENDPOINT_URL + '/' + bucket_name + '/' + file_name