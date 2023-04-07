import boto3
import time
import json
from datetime import datetime, timezone

app_config_data_client = boto3.client('appconfigdata')

APPLICATION_ID = 'DemoApplication'
ENVIRONMENT_ID = 'DemoEnvironment'
CONFIG_PROFILE_ID = 'DemoFlag'

class FeatureFlagWrapper:

    def __init__(self):
        self.session_token = None
        self.value = None

    def update_token(self, new_token):
        self.session_token = new_token

    """
    {
        "MyFeature": {
            "Amount": 3
        }
    }
    """
    def update_value(self, new_value):
        if len(new_value) > 0:
            self.value = new_value['MyFeature']['Amount']


# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/appconfigdata/client/start_configuration_session.html
def initialize_session(feature_flag_wrapper):
    response = app_config_data_client.start_configuration_session(
        ApplicationIdentifier=APPLICATION_ID,
        EnvironmentIdentifier=ENVIRONMENT_ID,
        ConfigurationProfileIdentifier=CONFIG_PROFILE_ID,
        RequiredMinimumPollIntervalInSeconds=15 # Minimum allowed

    )
    feature_flag_wrapper.update_token(response['InitialConfigurationToken'])


# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/appconfigdata/client/get_latest_configuration.html
def retrieve_configuration(token):
    response = app_config_data_client.get_latest_configuration(
        ConfigurationToken=token
    )

    configuration = response['Configuration']
    configuration_result = configuration.read().decode('utf-8')
    configuration.close()

    # The result is sometimes empty because there isn't a new value to apply
    configuration_json = json.loads(configuration_result) if len(configuration_result) > 0 else {}
    return (configuration_json, response['NextPollConfigurationToken'])


def execute():
    feature_flag_wrapper = FeatureFlagWrapper()
    initialize_session(feature_flag_wrapper)
    for i in range(100):
        configuration, next_token = retrieve_configuration(feature_flag_wrapper.session_token)
        feature_flag_wrapper.update_token(next_token)
        feature_flag_wrapper.update_value(configuration)
        do_business_logic(feature_flag_wrapper.value)
        time.sleep(16)


def do_business_logic(feature_value):
    now_utc = datetime.now(timezone.utc)
    if feature_value < 5:
        print(f'{now_utc}: The value is small: {feature_value}')
    elif feature_value < 10:
        print(f'{now_utc}: The value is medium: {feature_value}')
    else:
        print(f'{now_utc}: The value is large: {feature_value}')


execute()