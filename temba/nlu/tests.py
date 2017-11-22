# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from mock import patch
from temba.tests import TembaTest, MockResponse
from .models import NluApiConsumer, NLU_BOTHUB_TAG, NLU_WIT_AI_TAG
from django.core.urlresolvers import reverse

import six


class NluTest(TembaTest):
    def test_nlu_api_bothub_consumer(self):
        self.login(self.admin)

        payload = dict(api_name=NLU_BOTHUB_TAG, api_key='BOT_KEY_STRING', disconnect='false')
        self.client.post(reverse('orgs.org_nlu_api'), payload, follow=True)
        self.org.refresh_from_db()

        consumer = NluApiConsumer.factory(self.org)
        self.assertEqual(six.text_type(consumer), 'BotHub Consumer')
        self.assertEqual(consumer.get_headers(), {'Authorization': 'Bearer BOT_KEY_STRING'})

        with patch('requests.get') as mock_get:
            mock_get.return_value = MockResponse(200, """
            {
                "bots": [
                    {"slug": "bot-slug-16", "uuid": "e5bf3007-2629-44e3-8cbe-4505ecb130e2"},
                    {"slug": "bot-slug-15", "uuid": "53c800c6-9e90-4ede-b3b8-723596bd8b2e"}
                ]
            }
            """)
            self.assertEqual(tuple(consumer.list_bots()),
                             (('e5bf3007-2629-44e3-8cbe-4505ecb130e2', 'bot-slug-16'),
                              ('53c800c6-9e90-4ede-b3b8-723596bd8b2e', 'bot-slug-15')))

        with patch('requests.get') as mock_get:
            mock_get.return_value = MockResponse(200, """
            {
                "bot_uuid": "e5bf3007-2629-44e3-8cbe-4505ecb130e2",
                "answer": {
                    "text": "I am looking for a Mexican restaurant in the center of town",
                    "entities": [
                        {
                            "start": 19,
                            "value": "Mexican",
                            "end": 26,
                            "entity": "cuisine",
                            "extractor": "ner_crf"
                        },
                        {
                            "start": 45,
                            "value": "center",
                            "end": 51,
                            "entity": "location",
                            "extractor": "ner_crf"
                        }
                    ],
                    "intent_ranking": [
                        {
                            "confidence": 0.731929302865667,
                            "name": "restaurant_search"
                        },
                        {
                            "confidence": 0.14645046976303883,
                            "name": "goodbye"
                        },
                        {
                            "confidence": 0.07863577626166107,
                            "name": "greet"
                        },
                        {
                            "confidence": 0.04298445110963322,
                            "name": "affirm"
                        }
                    ],
                    "intent": {
                        "confidence": 0.731929302865667,
                        "name": "restaurant_search"
                    }
                }
            }
            """)
            intent, accuracy, entities = consumer.predict("I am looking for a Mexican restaurant in the center of town",
                                                          "e5bf3007-2629-44e3-8cbe-4505ecb130e2")
            self.assertEqual(intent, 'restaurant_search')
            self.assertEqual(accuracy, 0.731929302865667)
            self.assertEqual(type(entities), dict)
            self.assertEqual(entities.get('cuisine'), 'Mexican')
            self.assertEqual(entities.get('location'), 'center')

    def test_nlu_api_wit_consumer(self):
        self.login(self.admin)

        payload = dict(api_name=NLU_WIT_AI_TAG, api_key='BOT_KEY_STRING', disconnect='false')
        self.client.post(reverse('orgs.org_nlu_api'), payload, follow=True)
        self.org.refresh_from_db()

        consumer = NluApiConsumer.factory(self.org)
        self.assertEqual(six.text_type(consumer), 'Wit.AI Consumer')

        with patch('requests.get') as mock_get:
            mock_get.return_value = MockResponse(200, """
            {
                "msg_id": "0j1thaYcCT2iJX7dB",
                "_text": "Eu quero um exame com um ortopedista",
                "entities": {
                    "exames": [
                        {
                            "confidence": 1,
                            "value": "exame",
                            "type": "value"
                        }
                    ],
                    "medico": [
                        {
                            "confidence": 0.87037789125963,
                            "value": "ortopedista",
                            "type": "value"
                        }
                    ],
                    "intent": [
                        {
                            "confidence": 0.89605580369856,
                            "value": "atendimento"
                        }
                    ]
                }
            }
            """)
            intent, accuracy, entities = consumer.predict("Eu quero um exame com um ortopedista", None)
            self.assertEqual(intent, 'atendimento')
            self.assertEqual(accuracy, 0.89605580369856)
            self.assertEqual(type(entities), dict)
            self.assertEqual(entities.get('exames'), 'exame')
            self.assertEqual(entities.get('medico'), 'ortopedista')

        with patch('requests.get') as mock_get:
            mock_get.return_value = MockResponse(200, """
            {
                "msg_id": "0j1thaYcCT2iJX7dB",
                "_text": "Test none intents or entities",
                "entities": {}
            }
            """)
            intent, accuracy, entities = consumer.predict("Test none intents or entities", None)
            self.assertEqual(intent, None)
            self.assertEqual(accuracy, 0)
            self.assertEqual(entities, None)
