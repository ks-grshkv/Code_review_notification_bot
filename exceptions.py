class EmptyAPIResponseError(Exception):
    """Custom class for Empty API response exceptions"""
    pass


class APIResponseStatusCodeError(Exception):
    """Custom class for Empty API response status code if it
    doesnt equal HttpStatus.OK"""
    pass
