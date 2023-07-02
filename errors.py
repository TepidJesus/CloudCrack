class MaskFormatError(Exception):
    def __init__(self, message) -> None:
        super().__init__(message)

class MalformedJobError(Exception):
    def __init__(self, message) -> None:
        super().__init__(message)

class AWSCommunicationError(Exception):
    def __init__(self, message) -> None:
        super().__init__(message)

class AWSCredentialError(Exception):
    def __init__(self, message) -> None:
        super().__init__(message)

        