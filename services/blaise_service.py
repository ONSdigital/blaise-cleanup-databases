import logging
from typing import Any

import blaise_restapi  # type: ignore[reportMissingTypeStubs]

from models.blaise_config_model import BlaiseConfig

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)
class BlaiseService:
    def __init__(self, config: BlaiseConfig):
        self._config = config
        self.restapi_client = blaise_restapi.Client(
            f"http://{self._config.blaise_api_url}"
        )

    def get_questionnaires(self) -> list[dict[str, Any]]:
        try:
            return self.restapi_client.get_all_questionnaires_for_server_park(
                self._config.server_park
            )
        except Exception as error:
            LOGGER.error(
                f"BlaiseService: error in calling "
                "'get_all_questionnaires_for_server_park': "
                f"{error}"
            )
            raise error

    def get_guid_of_ips_questionnaire_in_blaise(self) -> list[str]:
        questionnaire_guids = []
        questionnaires = self.get_questionnaires()
        for questionnaire in questionnaires:
            if not questionnaire["id"]:
                message = (
                    f"MainSurveyID for {questionnaire['name']} not available. "
                    "This will result in skipping cleanup for this Questionnaire "
                    f": {questionnaire['name']}"
                )
                LOGGER.info(message)
                continue

            if not questionnaire["name"].startswith("IPS"):
                message = (
                    f"Excluding questionnaire {questionnaire['name']} "
                    "because it is non-IPS"
                )
                LOGGER.info(message)
                continue

            questionnaire_guids.append(questionnaire["id"])
            LOGGER.info(
                f"MainSurveyID '{questionnaire['id']}' "
                f"for {questionnaire['name']} added"
            )
        return questionnaire_guids
