from __future__ import annotations


class BadRequestError(ValueError):
    pass


class ResourceNotFoundError(LookupError):
    pass
