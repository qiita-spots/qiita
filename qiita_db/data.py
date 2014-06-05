from .base import QiitaStatusObject


class RawData(QiitaStatusObject):
    _table = "raw_data"


class PreprocessedData(QiitaStatusObject):
    pass


class ProcessedData(QiitaStatusObject):
    pass