# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import requests
import json
import logging

from django.utils.translation import ugettext_lazy as _

from temba.utils.http import http_headers


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
    def __init__(self, auth, nlu_type, extra_tokens=None):
        self.auth = auth
        self.name = "%s Consumer" % dict(NLU_API_CHOICES).get(nlu_type)
        self.extra_tokens = extra_tokens

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

    def get_headers(self, token=None, prefix=None, prefix_separator=None):
        if not token:
            token = self.auth

        if prefix_separator:
            authorization = '%s%s%s' % (prefix, prefix_separator, token) if prefix else '%s' % token
        else:
            authorization = '%s %s' % (prefix, token) if prefix else '%s' % token

        return http_headers(extra={'Authorization': authorization})

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

    def _request(self, base_url, method='GET', data=None, headers=None):
        kwargs = dict(headers=headers)

        if method == 'GET':
            kwargs['params'] = data
        else:
            kwargs['data'] = data

        return requests.request(method=method, url=base_url, **kwargs)


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

    def is_valid_bot(self, bot):
        list_intents_url = '%s/v1/bots' % self.BASE_URL
        data = {
            'uuid': bot
        }
        response = self._request(list_intents_url, data=data, headers=self.get_headers())
        if response.status_code == 200:
            return True

    def is_valid_token(self):
        auth_url = '%s/v1/auth' % self.BASE_URL
        response = self._request(auth_url, headers=self.get_headers())
        return True if response.status_code == 200 else False

    def list_bots(self):
        list_bots_url = '%s/v1/auth' % self.BASE_URL
        response = self._request(list_bots_url, headers=self.get_headers())
        list_bots = []

        if response.status_code == 200 and response.content:
            content = json.loads(response.content)
            bots = content.get('bots', [])
            for bot in bots:
                list_bots.append(dict(uuid=bot.get('uuid'), slug=bot.get('slug')))

        return list_bots

    def get_entities(self, entities):
        ent = dict()
        for entity in entities:
            ent.update({entity.get('entity'): entity.get('value')})
        return ent

    def get_intents(self):
        list_intents_url = '%s/v1/bots' % self.BASE_URL
        bots = self.list_bots()
        intents_list = []

        for bot in bots:
            data = dict(uuid=bot[0])
            response = self._request(list_intents_url, data=data, headers=self.get_headers())
            if response.status_code == 200 and response.content:
                content = json.loads(response.content)
                intents = content.get('intents', [])
                intents_list = [dict(name=intent, bot_uuid=bot.get('uuid'), bot_name=bot.get('slug')) for intent in intents]

        return intents_list


class WitConsumer(BaseConsumer):
    """
    Wit AI consumer
    This consumer will call Wit Ai api.
    """
    BASE_URL = 'https://api.wit.ai'
    AUTH_PREFIX = 'Bearer'

    def predict(self, msg, bot):
        predict_url = '%s/message' % self.BASE_URL
        data = {
            'q': msg,
            'n': 1
        }
        response = self._request(predict_url, data=data, headers=self.get_headers(token=bot, prefix=self.AUTH_PREFIX))
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
        intents_url = '%s/entities' % self.BASE_URL
        response = self._request(intents_url, headers=self.get_headers(prefix='Bearer'))
        return True if response.status_code == 200 else False

    def get_entities(self, entities):
        ent = dict()
        entities.pop('intent', None)
        for entity in entities.items():
            ent.update({entity[0]: entity[1][0].get('value')})
        return ent

    def get_intents(self):
        intents_url = '%s/entities/intent' % self.BASE_URL
        response = self._request(intents_url, data=None, headers=self.get_headers(prefix='Bearer'))
        print response.content
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
        extra_tokens = org.nlu_api_config_json().get('extra_tokens', None)

        assert api_name and api_key, _('Please, provide the follow args: api_name and api_key')

        if api_name == NLU_BOTHUB_TAG:
            consumer = BothubConsumer(api_key, api_name, extra_tokens)
        elif api_name == NLU_WIT_AI_TAG:
            consumer = WitConsumer(api_key, api_name, extra_tokens)
        else:
            consumer = None
            logging.warning(_('Consumer not found, please provide a valid'))

        return consumer

    @staticmethod
    def is_valid_token(api_name, api_key):

        assert api_name and api_key, _('Please, provide the follow args: api_name and api_key')

        if api_name == NLU_BOTHUB_TAG:
            consumer = BothubConsumer(api_key, api_name).is_valid_token()
        elif api_name == NLU_WIT_AI_TAG:
            consumer = WitConsumer(api_key, api_name).is_valid_token()
        else:
            consumer = None
            logging.warning(_('Consumer not found, please provide a valid'))

        return consumer
