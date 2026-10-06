import os


def _required_environment_variable(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Required environment variable {name} is not configured")
    return value


class SettingsMeta(type):
    @property
    def DATABASE_USER(cls) -> str:
        return _required_environment_variable("DATABASE_USER")

    @property
    def DATABASE_PASSWORD(cls) -> str:
        return _required_environment_variable("DATABASE_PASSWORD")

    @property
    def DATABASE_IP_ADDRESS(cls) -> str:
        return _required_environment_variable("DATABASE_IP_ADDRESS")

    @property
    def DATABASE_PORT(cls) -> int:
        return int(_required_environment_variable("DATABASE_PORT"))

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
