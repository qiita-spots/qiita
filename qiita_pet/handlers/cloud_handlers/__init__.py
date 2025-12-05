from .file_transfer_handlers import (
    FetchFileFromCentralHandler,
    PushFileToCentralHandler,
)

__all__ = ["FetchFileFromCentralHandler"]

ENDPOINTS = [
    (r"/cloud/fetch_file_from_central/(.*)", FetchFileFromCentralHandler),
    (r"/cloud/push_file_to_central/", PushFileToCentralHandler),
]
