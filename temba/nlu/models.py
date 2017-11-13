# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import requests
import json


NLU_API_NAME = 'NLU_API_NAME'
NLU_API_KEY = 'NLU_API_KEY'

NLU_BOTHUB_TAG = 'BTH'
NLU_WIT_AI_TAG = 'WIT'

NLU_API_CHOICES = (
    (NLU_BOTHUB_TAG, 'BotHub'),
    (NLU_WIT_AI_TAG, 'Wit.AI'),)

NLU_API_WITHOUT_KEY = [NLU_WIT_AI_TAG]


class BaseConsumer(object):
    """
    Base consumer
    This is the base for any nlu api consumers.
    """
    def __init__(self, auth, nlu_type):
        self.auth = auth
        self.name = "%s Consumer" % dict(NLU_API_CHOICES).get(nlu_type)

    def __str__(self):
        return self.name

    def list_bots(self):
        """
        Abstract funciton to list bots
        """

    def predict(self, msg, bot):
        """
        Abstract funciton to predict
        """

    def get_headers(self):
        return {
            'Authorization': 'Bearer %s' % self.auth
        }

    def get_entities(self, entities):
        """
        Abstract funciton to get entities
        """

    def get_intents(self):
        """
        Abstract function to get bot intents
        """

    def is_valid_token(self):
        """
        Abstract function to check if token is valid
        """

    def _request(self, base_url, data=None, headers=None):
        try:
            return requests.get(base_url, params=data, headers=headers)
        except Exception as e:
            print(e)
            return None


class BothubConsumer(BaseConsumer):
    """
    Bothub consumer
    This consumer will call Bothub api.
    """
    BASE_URL = 'http://api.bothub.it'

    def predict(self, msg, bot):
        predict_url = '%s/v1/message' % self.BASE_URL
        data = {
            'bot': bot,
            'msg': msg
        }
        response = self._request(predict_url, data=data, headers=self.get_headers())
        if not response:
            return None, 0, None

        predict = json.loads(response.content)

        answer = predict.get('answer', None)
        intent = answer.get('intent', None)
        entities = self.get_entities(answer.get('entities', None))

        return intent.get('name', None), intent.get('confidence', None), entities

    def is_valid_token(self):
        auth_url = '%s/v1/auth' % self.BASE_URL
        response = self._request(auth_url, headers=self.get_headers())
        if response.status_code == 200:
            return True

    def list_bots(self):
        list_bots_url = '%s/v1/auth' % self.BASE_URL
        response = self._request(list_bots_url, headers=self.get_headers())
        if response:
            tuple_bots = tuple(json.loads(response.content).get('bots'))
            list_bots = list()
            for bot in tuple_bots:
                list_bots.append((bot.get('uuid'), bot.get('slug')))
            return list_bots

    def get_entities(self, entities):
        ent = dict()
        for entity in entities:
            ent.update({entity.get('entity'): entity.get('value')})
        return ent

    def get_intents(self):
        list_intents_url = '%s/v1/bots' % self.BASE_URL
        bots = self.list_bots()
        if bots:
            intents_list = []
            for bot in bots:
                data = {
                    'uuid': bot[0]
                }
                response = self._request(list_intents_url, data=data, headers=self.get_headers())
                intents = json.loads(response.content).get('intents')
                for intent in intents:
                    intents_list.append({
                        'name': intent,
                        'bot_id': bot[0],
                        'bot_name': bot[1]
                    })
            return intents_list


class WitConsumer(BaseConsumer):
    """
    Wit AI consumer
    This consumer will call Wit Ai api.
    """
    BASE_URL = 'https://api.wit.ai'

    def predict(self, msg, bot):
        predict_url = '%s/message' % self.BASE_URL
        data = {
            'q': msg,
            'n': 1
        }
        response = self._request(predict_url, data=data, headers=self.get_headers())
        if not response:
            return None, 0, None

        predict = json.loads(response.content)

        entities = predict.get('entities', None)
        if entities:
            intents = entities.get('intent', None)
            if intents:
                return intents[0].get('value'), intents[0].get('confidence'), self.get_entities(entities)
        return None, 0, None

    def is_valid_token(self):
        intents_url = '%s/entities/intent' % self.BASE_URL
        response = self._request(intents_url, headers=self.get_headers())
        if response.status_code == 200:
            return True

    def get_entities(self, entities):
        ent = dict()
        entities.pop('intent', None)
        for entity in entities.items():
            ent.update({entity[0]: entity[1][0].get('value')})
        return ent

    def get_intents(self):
        intents_url = '%s/entities/intent' % self.BASE_URL
        response = self._request(intents_url, data=None, headers=self.get_headers())
        if response:
            response_intents = json.loads(response.content)
            intents = response_intents.get('values', None)
            intent_list = []
            if intents:
                for intent in intents:
                    intent_list.append({
                        'name': intent.get('value', None),
                        'bot_id': self.auth,
                        'bot_name': self.name
                    })
                return intent_list


class NluApiConsumer(object):
    """
    Nlu API consumer
    This consumer will check which api will be called.
    """
    @staticmethod
    def factory(org):
        api_name, api_key = org.get_nlu_api_credentials()
        if api_name == NLU_BOTHUB_TAG:
            return BothubConsumer(api_key, api_name)
        if api_name == NLU_WIT_AI_TAG:
            return WitConsumer(api_key, api_name)

    @staticmethod
    def is_valid_token(api_name, api_key):
        if api_key[:7] == "Bearer ":
            api_key = api_key[7:]

        if api_name == NLU_BOTHUB_TAG:
            return BothubConsumer(api_key, api_name).is_valid_token()
        if api_name == NLU_WIT_AI_TAG:
            return WitConsumer(api_key, api_name).is_valid_token()