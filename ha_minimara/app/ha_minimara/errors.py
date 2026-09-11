class HAMiniMaraError(Exception):
    """Expected, safe-to-report adapter error."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code

