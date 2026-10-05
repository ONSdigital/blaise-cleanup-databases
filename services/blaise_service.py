import logging
from typing import Any, Dict, List

import blaise_restapi

from models.blaise_config_model import BlaiseConfig


class BlaiseService:
    def __init__(self, config: BlaiseConfig):
        self._config = config
        self.restapi_client = blaise_restapi.Client(
            f"http://{self._config.blaise_api_url}"
        )

    def get_questionnaires(self) -> List[Dict[str, Any]]:
        try:
            return self.restapi_client.get_all_questionnaires_for_server_park(
                self._config.server_park
            )
        except Exception as error:
            logging.error(
                f"BlaiseService: error in calling 'get_all_questionnaires_for_server_park': {error}"
            )
            raise error

    def get_guid_of_questionnaire_in_blaise(self) -> List[str]:
        questionnaire_guids = []
        questionnaires = self.get_questionnaires()
        for questionnaire in questionnaires:
            if not questionnaire["id"]:
                print(f"MainSurveyID for {questionnaire['name']} not available. This will result in skipping cleanup for this Questionnaire : {questionnaire['name']}")
                logging.warning(f"MainSurveyID for {questionnaire['name']} not available. This will result in skipping cleanup for this Questionnaire : {questionnaire['name']}")
                continue

            questionnaire_guids.append(questionnaire["id"])
            print(f"MainSurveyID '{questionnaire['id']}' for {questionnaire['name']} added")
            logging.info(f"MainSurveyID '{questionnaire['id']}' for {questionnaire['name']} added")
        print(f"Questionnaire GUIDs: {questionnaire_guids}")
        return questionnaire_guids
