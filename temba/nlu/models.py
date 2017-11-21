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

    def get_headers(self, token=None, prefix=None, prefix_separator=None, **kwargs):
        if not token:
            token = self.auth

        if prefix_separator:
            authorization = '%s%s%s' % (prefix, prefix_separator, token) if prefix else '%s' % token
        else:
            authorization = '%s %s' % (prefix, token) if prefix else '%s' % token

        extra = {'Authorization': authorization}
        for item in kwargs.keys():
            extra[item] = kwargs[item]

        return http_headers(extra=extra)

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
    AUTH_PREFIX = 'Bearer'

    def predict(self, msg, bot):
        predict_url = '%s/v1/message' % self.BASE_URL
        data = dict(bot=bot, msg=msg)
        response = self._request(predict_url, data=data, headers=self.get_headers(prefix=self.AUTH_PREFIX))
        if not response:
            return None, 0, None

        predict = json.loads(response.content)

        answer = predict.get('answer', {})
        intent = answer.get('intent', {})
        entities = self.get_entities(answer.get('entities')) if 'entities' in answer else None

        return intent.get('name', None), intent.get('confidence', None), entities

    def is_valid_bot(self, bot):
        list_intents_url = '%s/v1/bots' % self.BASE_URL
        data = dict(uuid=bot)
        response = self._request(list_intents_url, data=data, headers=self.get_headers(prefix=self.AUTH_PREFIX))
        return True if response.status_code == 200 else False

    def is_valid_token(self):
        auth_url = '%s/v1/auth' % self.BASE_URL
        response = self._request(auth_url, headers=self.get_headers(prefix=self.AUTH_PREFIX))
        return True if response.status_code == 200 else False

    def list_bots(self):
        list_bots_url = '%s/v1/auth' % self.BASE_URL
        response = self._request(list_bots_url, headers=self.get_headers(prefix=self.AUTH_PREFIX))
        list_bots = []

        if response.status_code == 200 and response.content:
            content = json.loads(response.content)
            bots = content.get('bots', [])
            for bot in bots:
                list_bots.append(dict(uuid=bot.get('uuid'), slug=bot.get('slug')))

        return list_bots

    def get_entities(self, entities):
        entity = dict()
        for item in entities:
            entity[item.get('entity')] = item.get('value')
        return entity

    def get_intents(self):
        list_intents_url = '%s/v1/bots' % self.BASE_URL
        bots = self.list_bots()
        intents_list = []

        for bot in bots:
            data = dict(uuid=bot.get('uuid'))
            response = self._request(list_intents_url, data=data, headers=self.get_headers(prefix=self.AUTH_PREFIX))
            if response.status_code == 200 and response.content:
                content = json.loads(response.content)
                intents = content.get('intents', [])
                intents_list = [dict(name=intent, bot_id=bot.get('uuid'), bot_name=bot.get('slug')) for intent in intents]

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
        data = dict(q=msg)

        response = self._request(predict_url, data=data, headers=self.get_headers(token=bot, prefix=self.AUTH_PREFIX))

        if response.status_code != 200 and not response.content:
            return None, 0, None

        predict = json.loads(response.content)

        entities = predict.get('entities', {})
        entities_keys = entities.keys()
        key = entities_keys[0] if entities_keys else None
        entity = entities.get(key) if key else None
        priority_entity = entity[0] if entity else None

        return priority_entity.get('value'), priority_entity.get('confidence'), self.get_entities(entities) \
            if priority_entity else (None, 0, None)

    def is_valid_token(self):
        intents_url = '%s/entities' % self.BASE_URL
        response = self._request(intents_url, headers=self.get_headers(prefix=self.AUTH_PREFIX))
        return True if response.status_code == 200 else False

    def get_entities(self, entities):
        entity = dict()
        for key in entities.keys():
            intents = entities.get(key, [])
            ent = intents[0] if intents else {}
            entity[key] = ent.get('value')
        return entity

    def get_intents(self):
        intents_url = '%s/entities' % self.BASE_URL
        response = self._request(intents_url, data=None, headers=self.get_headers(prefix=self.AUTH_PREFIX))

        intents_list = []

        if response.status_code == 200 and response.content:
            entities = json.loads(response.content)
            intents_list = [dict(name=intent.replace('$', '/'), bot_id=self.auth, bot_name=self.name)
                            for intent in entities]

        return intents_list


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
