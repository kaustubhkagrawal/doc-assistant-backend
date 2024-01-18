# import boto3
# import aiohttp
# import fsspec
import s3fs
from fsspec.asyn import AsyncFileSystem
from app.core.config import settings

import os

from urllib.parse import urlsplit

def generate_name_from_url(url):
    # Parse the URL
    parsed_url = urlsplit(url)

    # Extract the domain or path component
    if parsed_url.netloc:
        name = parsed_url.netloc.replace(".", "_")
    else:
        name = parsed_url.path.replace("/", "_").strip("_")

    # Exclude file extension if present
    filename = os.path.basename(parsed_url.path)
    name_without_extension = os.path.splitext(filename)[0]
    if name_without_extension:
        name = name_without_extension.replace(".", "_")

    return name


# def get_s3_client():
#     boto_session = boto3.Session(aws_access_key_id=settings.AWS_KEY, aws_secret_access_key=settings.AWS_SECRET)

#     s3_client = boto_session.client("s3", endpoint_url=settings.S3_ENDPOINT_URL)
#     return s3_client


def get_s3_fs(bucket_name: str = settings.S3_BUCKET_NAME) -> AsyncFileSystem:
    s3 = s3fs.S3FileSystem(
        key=settings.AWS_KEY,
        secret=settings.AWS_SECRET,
        endpoint_url=settings.S3_ENDPOINT_URL,
        client_kwargs={'region_name': settings.AWS_DEFAULT_REGION} if settings.RENDER else {}
    )
    
    if not (settings.RENDER or s3.exists(bucket_name)):
        s3.mkdir(bucket_name)
    return s3


# async def get_s3_fs():
#     s3_client = get_s3_client()
#     return await fsspec.filesystem("s3", client=s3_client, anon=False)
    

# async def get_async_s3_fs():
#     aws_session = aiohttp.ClientSession()
    
#     auth = aiohttp.BasicAuth(login=settings.AWS_KEY, password=settings.AWS_SECRET)
#     async with aws_session.get(
#         settings.S3_ENDPOINT_URL,
#         auth=auth,
#     ) as resp:
#         s3_client = boto3.client(
#             "s3",
#             aws_access_key_id=settings.AWS_KEY,
#             aws_secret_access_key=settings.AWS_SECRET,
#             endpoint_url=settings.S3_ENDPOINT_URL,
#         )
#         async_fs = fsspec.filesystem("s3", client=s3_client, anon=False)
#     return async_fs

def get_Document_url(bucket_name: str = settings.S3_ASSET_BUCKET_NAME, file_name: str = ''):
    return settings.S3_ENDPOINT_URL + '/' + bucket_name + '/' + file_name