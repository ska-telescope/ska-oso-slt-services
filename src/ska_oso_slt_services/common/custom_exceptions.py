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
