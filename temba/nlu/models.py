# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import requests
import json

from django.conf import settings


class BothubConsumer(object):
    """
    Bothub consumer
    This consumer will call Bothub api.
    """
    BASE_URL = settings.BOTHUB_BASE_URL
    AUTH_PREFIX = "Bearer"

    def __init__(self, authorization_key):
        self.bothub_authorization_key = authorization_key

    def __str__(self):
        return self.bothub_authorization_key

    def request(self, url, method="GET", payload=None):
        response = requests.request(
            method=method,
            url="{}/{}/".format(self.BASE_URL, url),
            headers={"Authorization": "{} {}".format(self.AUTH_PREFIX, self.bothub_authorization_key)},
            data=payload,
        )
        return response

    def predict(self, text, language=None):
        payload = {"text": str(text)}
        if language:
            payload.update({"language": language})

        response = self.request("parse", method="POST", payload=payload)

        if response.status_code != 200:
            return None, 0, None

        predict = json.loads(response.content)
        answer = predict.get("answer", {})
        intent = answer.get("intent", {})
        entities = self.get_entities(answer.get("entities")) if "entities" in answer else None
        return intent.get("name", None), intent.get("confidence", 0), entities

    def is_valid_token(self):
        response = self.request("info")
        return True if response.status_code == 200 else False

    def get_repository_info(self):
        response = self.request("info")
        return json.loads(response.content)

    def get_entities(self, entities):
        entity = dict()
        for item in entities:
            entity[item.get("entity")] = item.get("value")
        return entity

    def get_intents(self):
        response = self.get_repository_info()
        return response.get("intents", {})
