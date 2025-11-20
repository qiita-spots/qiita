from .file_transfer_handlers import (FetchFileFromCentralHandler,
                                     PushFileToCentralHandler,
                                     DeleteFileFromCentralHandler)
from qiita_core.util import is_test_environment

__all__ = ['FetchFileFromCentralHandler']

ENDPOINTS = [
    (r"/cloud/fetch_file_from_central/(.*)", FetchFileFromCentralHandler),
    (r"/cloud/push_file_to_central/", PushFileToCentralHandler)
]

if is_test_environment():
    ENDPOINTS.append(
        (r"/cloud/delete_file_from_central/(.*)",
         DeleteFileFromCentralHandler))
