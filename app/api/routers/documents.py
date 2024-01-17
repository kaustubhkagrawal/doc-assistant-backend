import boto3
from fastapi import APIRouter, UploadFile, HTTPException, File

from app.core.config import settings
from app.services.document import upsert_single_document
from io import BytesIO
from pydantic import BaseModel
from app.utils.file_utils import get_Document_url
from fastapi.encoders import jsonable_encoder

router = APIRouter()

# Initialize S3 client

boto_session = boto3.Session(aws_access_key_id=settings.AWS_KEY, aws_secret_access_key=settings.AWS_SECRET)

s3_client = boto_session.client("s3", endpoint_url='http://localhost:4566')

class FileData(BaseModel):
    file: UploadFile

ALLOWED_EXTENSIONS = ["pdf", "txt", "md", "jpg", "jpeg", "png", "gif"]

def is_allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@router.post("/upload")
async def upload_file_to_s3(file: UploadFile = File()):
    print(file.filename)
    if not is_allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="File type not allowed")

    with BytesIO() as file_stream:
        # Read the file into memory
        file_stream.write(await file.read())
        file_stream.seek(0)

        # Upload the file to S3
        try:
            s3_client.upload_fileobj(file_stream, settings.S3_ASSET_BUCKET_NAME, file.filename)
        except Exception as e:
            print(e)
            raise HTTPException(status_code=500, detail="Failed to upload file to S3")
        
    url: str = get_Document_url(file_name=file.filename)
    doc = await upsert_single_document(url)
    doc_dict = jsonable_encoder(doc)
    return doc_dict