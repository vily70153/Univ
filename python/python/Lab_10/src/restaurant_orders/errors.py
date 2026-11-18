class RestaurantError(Exception):
    """Base domain error."""


class ValidationError(RestaurantError, ValueError):
    """Invalid domain data."""


class DataError(RestaurantError):
    """Input/output or malformed data."""


class NotFound(RestaurantError, LookupError):
    """Missing entity."""
