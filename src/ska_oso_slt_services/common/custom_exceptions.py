class ShiftEndedException(Exception):
    """Custom exception raised when a PUT operation is attempted after
    the shift has ended."""

    def __init__(
        self,
        message="Put Operation is not allowed once Shift ends;"
        " only annotations are allowed",
    ):
        self.message = message
        super().__init__(self.message)


class ODADataError(Exception):
    """Custom exception raised when there are issues with
    ODA data retrieval or processing."""

    def __init__(self, message="Error occurred while processing ODA data"):
        self.message = message
        super().__init__(self.message)
