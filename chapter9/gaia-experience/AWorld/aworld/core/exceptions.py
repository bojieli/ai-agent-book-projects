class AWorldRuntimeException(Exception):
    """Base exception class for AWorld runtime errors.
    
    This exception should be raised when runtime-specific errors occur
    within the AWorld framework.
    
    Attributes:
        message: Human-readable error message describing what went wrong.
    """

    def __init__(self, message: str):
        """Initialize the AWorld runtime exception.
        
        Args:
            message: Descriptive error message.
        """
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return string representation of the exception."""
        return f"AWorldRuntimeException: {self.message}"


class AWorldConfigurationError(AWorldRuntimeException):
    """Exception raised for configuration-related errors."""
    pass


class AWorldConnectionError(AWorldRuntimeException):
    """Exception raised for connection and network-related errors."""
    pass


class AWorldToolExecutionError(AWorldRuntimeException):
    """Exception raised when tool execution fails."""
    pass
