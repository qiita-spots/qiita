from .base import QiitaStatusObject


class RawData(QiitaStatusObject):
    _table = "raw_data"
    pass


class PreprocessedData(QiitaStatusObject):
    _table = "preprocessed_data"
    pass


class ProcessedData(QiitaStatusObject):
    _table = "processed_data"
    pass