from caselawclient.models.documents.metrics.base import Metric


class SubmissionsBeforeFirstPublishMetric(Metric):
    key = "submissions_before_first_publish"
    title = "Submissions before first publication"
    description = "Number of SUBMISSION versions at first publication, including the initial submission."
