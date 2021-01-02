from fastapi import HTTPException


class UserError(HTTPException):
    def __init__(self) -> None:
        self.status_code = 401
        self.detail = "Something bad happened with user"


class UserWasNotFound(UserError):
    def __init__(self) -> None:
        super(UserWasNotFound, self).__init__()
        self.detail = "Wrong credentials"


class UserHasNoPermissions(UserError):
    def __init__(self) -> None:
        super(UserHasNoPermissions, self).__init__()
        self.detail = "You has no permission to do this"
        self.status_code = 403
