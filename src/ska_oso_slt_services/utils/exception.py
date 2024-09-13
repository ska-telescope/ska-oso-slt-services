class InvalidInputError(Exception):
    """Exception raised for invalid input errors.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"Invalid Input Error: {self.message}"


class DatabaseError(Exception):
    """Exception raised for database-related errors.

    Attributes:
        message -- explanation of the error
        original_error -- the original exception that caused this error (optional)
    """

    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)

    def __str__(self):
        error_msg = f"Database Error: {self.message}"
        if self.original_error:
            error_msg += f" (Original error: {str(self.original_error)})"
        return error_msg
