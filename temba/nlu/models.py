# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import requests
import json
import logging

from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from temba.utils.http import http_headers


NLU_API_NAME = 'NLU_API_NAME'
NLU_API_KEY = 'NLU_API_KEY'

NLU_BOTHUB_TAG = 'BTH'
NLU_WIT_AI_TAG = 'WIT'

NLU_API_CHOICES = (
    ('', ''),
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
        self.type = nlu_type
        self.extra_tokens = extra_tokens

    def __str__(self):
        return self.name

    def predict(self, msg, bot):
        """
        Abstract funciton to predict
        """
        raise NotImplementedError

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
        raise NotImplementedError

    def get_intents(self):
        """
        Abstract function to get bot intents
        """
        raise NotImplementedError

    def is_valid_token(self):
        """
        Abstract function to check if token is valid
        """
        raise NotImplementedError

    def _request(self, base_url, method='GET', data=None, headers=None):
        kwargs = dict(headers=headers)

        if method == 'GET':
            kwargs['params'] = data
        else:
            kwargs['data'] = data

        return requests.request(method=method, url=base_url, **kwargs)


class BothubConsumer(object):
    """
    Bothub consumer
    This consumer will call Bothub api.
    """
    BASE_URL = settings.BOTHUB_BASE_URL
    AUTH_PREFIX = 'Bearer'

    def __init__(self, authorization_key):
        self.bothub_authorization_key = authorization_key

    def __str__(self):
        return self.bothub_authorization_key

    def request(self, url, method='GET', payload=None):
        response = requests.request(
            method=method,
            url='{}/{}/'.format(self.BASE_URL, url),
            headers={
                'Authorization': '{} {}'.format(self.AUTH_PREFIX, self.bothub_authorization_key),
            },
            data=payload)
        return response

    def predict(self, text, language=None):
        payload = {
            'text': str(text)
        }
        if language:
            payload.update({'language': language})

        response = self.request('parse', method='POST', payload=payload)

        if response.status_code != 200:
            return None, 0, None

        predict = json.loads(response.content)
        answer = predict.get('answer', {})
        intent = answer.get('intent', {})
        entities = self.get_entities(answer.get('entities')) if 'entities' in answer else None
        return intent.get('name', None), intent.get('confidence', 0), entities

    def is_valid_token(self):
        response = self.request('info')
        return True if response.status_code == 200 else False

    def get_repository_info(self):
        response = self.request('info')
        return json.loads(response.content)

    def get_entities(self, entities):
        entity = dict()
        for item in entities:
            entity[item.get('entity')] = item.get('value')
        return entity

    def get_intents(self):
        response = self.get_repository_info()
        return response.get('intents', {})


class NluApiConsumer(object):
    """
    Nlu API consumer
    This consumer will check which api will be called.
    """
    @staticmethod
    def factory(org):
        api_name, api_key = org.get_bothub_repositories()
        extra_tokens = org.nlu_api_config_json().get('extra_tokens', None)

        if api_name == NLU_BOTHUB_TAG:
            consumer = BothubConsumer(api_key, api_name, extra_tokens)
        # elif api_name == NLU_WIT_AI_TAG:
        #     consumer = WitConsumer(api_key, api_name, extra_tokens)
        else:
            consumer = None
            logging.warning(_('Consumer not found, please provide a valid'))

        return consumer

    @staticmethod
    def is_valid_token(api_name, api_key, bot=None):
        assert api_name and api_key, _('Please, provide the follow args: api_name and api_key')
        if api_name == NLU_BOTHUB_TAG:
            result = BothubConsumer(api_key, api_name).is_valid_token()
        # elif api_name == NLU_WIT_AI_TAG:
        #     result = WitConsumer(api_key, api_name).is_valid_token()
        else:
            result = False
            logging.warning(_('Consumer not found, please provide a valid'))

        return result
