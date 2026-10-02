from caselawclient.models.documents.metrics.base import Metric


class TdrToLatestPublishMetric(Metric):
    key = "tdr_to_latest_publish"
    title = "Time to latest publication"
    description = "Integer seconds from the first SUBMISSION after the previous publication (or first ever) to latest publication."
