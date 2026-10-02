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
    def SQL_INSTANCE_NAME(cls) -> str:
        return _required_environment_variable("SQL_INSTANCE_NAME")
