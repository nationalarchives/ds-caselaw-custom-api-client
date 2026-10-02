from caselawclient.models.documents.metrics.base import Metric


class TdrToFirstPublishMetric(Metric):
    key = "tdr_to_first_publish"
    title = "Time to first publication"
    description = "Integer seconds from the first SUBMISSION save to first publication."
