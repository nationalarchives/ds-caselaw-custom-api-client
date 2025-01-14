import requests


class MarklogicAPIError(requests.HTTPError):
    status_code = 500
    default_message = "An error occurred, and we didn't recognise it."


class MarklogicBadRequestError(MarklogicAPIError):
    status_code = 400
    default_message = "Marklogic did not understand the request that was made."


class MarklogicUnauthorizedError(MarklogicAPIError):
    status_code = 401
    default_message = "Your credentials are not valid, or you did not provide any by basic authentication"


class MarklogicNotPermittedError(MarklogicAPIError):
    status_code = 403
    default_message = "Your credentials are valid, but you are not allowed to do that."


class MarklogicResourceNotFoundError(MarklogicAPIError):
    status_code = 404
    default_message = "No resource with that name could be found."


class MarklogicResourceLockedError(MarklogicAPIError):
    status_code = 409
    default_message = "The resource is locked by another user, so you cannot change it."


class MarklogicResourceUnmanagedError(MarklogicAPIError):
    """Note: this exception may be raised if a document doesn't exist,
    since all documents should be managed."""

    status_code = 404
    default_message = (
        "The resource isn't managed. It probably doesn't exist, and if it does, that's a problem. Please report it."
    )


class MarklogicResourceNotCheckedOutError(MarklogicAPIError):
    status_code = 409
    default_message = "The resource is not checked out by anyone, but that request needed a checkout first."


class MarklogicCheckoutConflictError(MarklogicAPIError):
    status_code = 409
    default_message = "The resource is checked out by another user."


class MarklogicValidationFailedError(MarklogicAPIError):
    status_code = 422
    default_message = "The XML document did not validate according to the schema."


class MarklogicCommunicationError(MarklogicAPIError):
    status_code = 500
    default_message = "Something unexpected happened when communicating with the Marklogic server."


class GatewayTimeoutError(MarklogicAPIError):
    "This will not contain XML, because it is a failure to connect to the Marklogic server."

    status_code = 504
    default_message = "The gateway to MarkLogic timed out."


class InvalidContentHashError(MarklogicAPIError):
    # This error does not come from Marklogic, but is an error raised by this API...
    status_code = 422
    default_message = "The content hash in the document did not match the hash of the content"


class DocumentNotFoundError(MarklogicAPIError):
    # This error does not come from Marklogic, but is an error raised by this API...
    status_code = 404
    default_message = "The document was not found"


class NotSupportedOnVersion(MarklogicAPIError):
    # This error does not come from Marklogic, but is an error raised by this API...
    status_code = 400
    default_message = "An operation was attempted on a version of a document which cannot occur on a version."


class OnlySupportedOnVersion(MarklogicAPIError):
    status_code = 400
    default_message = "The operation requested cannot be performed on a document that is not a version."
