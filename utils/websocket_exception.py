class WebSocketCustomException(Exception):
    def __init__(self, code: int, reason: str):
        self.code = code
        self.reason = reason
        super().__init__(self.reason)

    def __str__(self):
        return f"[Error {self.code}]: {self.reason}"