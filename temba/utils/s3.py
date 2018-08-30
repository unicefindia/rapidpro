from django.core.files.storage import DefaultStorage
from django.conf import settings


class PublicFileStorage(DefaultStorage):
    default_acl = "public-read"
    file_overwrite = False


class PrivateFileStorage(DefaultStorage):
    default_acl = "private"
    file_overwrite = False
    bucket_name = settings.AWS_STORAGE_PRIVATE_BUCKET_NAME


public_file_storage = PublicFileStorage()
public_file_storage.default_acl = "public-read"

private_file_storage = PrivateFileStorage()
