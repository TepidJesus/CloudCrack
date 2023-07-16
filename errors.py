## General Errors ##
class MaskFormatError(Exception):
    def __init__(self, message) -> None:
        super().__init__(message)

class MalformedJobError(Exception):
    def __init__(self, message) -> None:
        super().__init__(message)

class ConfigError(Exception):
    def __init__(self, message) -> None:
        super().__init__("The configuration file is missing or malformed. Please get a new one from the repository.")

class CredentialsFileNotFoundError(Exception):
    def __init__(self, message) -> None:
        super().__init__(message)

class EnvironmentVariableNotFoundError(Exception):
    def __init__(self, message) -> None:
        super().__init__(message)

## AWS Errors ##         

class AWSCommunicationError(Exception):
    def __init__(self, message) -> None:
        super().__init__(message)

class AWSCredentialError(Exception):
    def __init__(self, message) -> None:
        super().__init__(message)

class AWSPermissionsError(Exception):
    def __init__(self, message) -> None:
        super().__init__(message)
