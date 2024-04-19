class InvalidStoreError(Exception):
    """
    Raised when a the provider name informed does not match
    any of the supported stores.
    """

    def __init__(self, msg: str | None = None) -> None:
        if msg is None:
            msg = "Invalid provider name informed."
        super().__init__(msg)
