import os


def _required_environment_variable(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Required environment variable {name} is not configured")
    return value


class SettingsMeta(type):
    @property
    def PROJECT_ID(cls) -> str:
        return _required_environment_variable("PROJECT_ID")

    @property
    def SQL_REGION(cls) -> str:
        return _required_environment_variable("SQL_REGION")

    @property
    def SQL_INSTANCE_NAME(cls) -> str:
        return _required_environment_variable("SQL_INSTANCE_NAME")

    @property
    def DATABASE_USER(cls) -> str:
        return _required_environment_variable("DATABASE_USER")

    @property
    def SQL_IP_TYPE(cls) -> str:
        return os.getenv("SQL_IP_TYPE", "public").strip().lower()

    @property
    def SERVER_PARK(cls) -> str:
        return _required_environment_variable("SERVER_PARK")

    @property
    def BLAISE_API_URL(cls) -> str:
        return _required_environment_variable("BLAISE_API_URL")

    @property
    def CMA_TIME_THRESHOLD(cls) -> int:
        return int(_required_environment_variable("CMA_TIME_THRESHOLD"))


class Settings(metaclass=SettingsMeta):
    pass