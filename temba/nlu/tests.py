# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from mock import patch
from temba.tests import TembaTest, MockResponse
from .models import BothubConsumer
from django.core.urlresolvers import reverse


class NluTest(TembaTest):

    def test_nlu_api_bothub_consumer(self):
        self.login(self.admin)

        payload = dict(bothub_authorization_key="", disconnect="false")
        with patch("temba.nlu.models.BothubConsumer.is_valid_token") as mock_validation:
            mock_validation.return_value = True
            payload.update(dict(bothub_authorization_key="673d4c5f35be4d1e9e76eaafe56704c1"))

            with patch("requests.request") as mock_get:
                mock_get.return_value = MockResponse(
                    200,
                    """
                {
                    "uuid": "673d4c5f35be4d1e9e76eaafe56704c1",
                    "owner": 2,
                    "owner__nickname": "bob",
                    "name": "Binary Answers",
                    "slug": "binary",
                    "language": "en",
                    "available_languages": [
                        "pt",
                        "en"
                    ],
                    "categories": [
                        3
                    ],
                    "categories_list": [
                        {
                            "id": 3,
                            "name": "Tools"
                        }
                    ],
                    "description": "",
                    "is_private": false,
                    "intents": [
                        "restaurant_search",
                        "goodbye",
                        "greet"
                    ],
                    "entities": [],
                    "examples__count": 23,
                    "authorization": null,
                    "ready_for_train": false,
                    "votes_sum": 2,
                    "created_at": "2018-06-11T22:02:42.185098Z"
                }
                """,
                )
                self.client.post(reverse("orgs.org_bothub"), payload, follow=True)
                self.org.refresh_from_db()
                bothub = BothubConsumer("673d4c5f35be4d1e9e76eaafe56704c1")

                with patch("requests.request") as mock_get:
                    mock_get.return_value = MockResponse(
                        200,
                        """
                    {
                        "intents": [
                            "restaurant_search",
                            "goodbye",
                            "greet"
                        ]
                    }
                    """,
                    )
                    self.assertEqual(bothub.get_intents(), ["restaurant_search", "goodbye", "greet"])

                with patch("requests.request") as mock_get:
                    entities = [
                        {"start": 19, "value": "Mexican", "end": 26, "entity": "cuisine", "extractor": "ner_crf"},
                        {"start": 45, "value": "center", "end": 51, "entity": "location", "extractor": "ner_crf"},
                    ]
                    mock_get.return_value = MockResponse(
                        200,
                        """
                    {
                        "cuisine": "Mexican"

                    },
                    {
                        "location": "center"
                    }
                    """,
                    )
                    self.assertEqual(bothub.get_entities(entities), {"cuisine": "Mexican", "location": "center"})

                mock_get.return_value = MockResponse(403, "")
                intent, accuracy, entities = bothub.predict("Eu quero um exame com um ortopedista", None)
                self.assertEqual(intent, None)
                self.assertEqual(accuracy, 0)
                self.assertEqual(entities, None)

                with patch("requests.request") as mock_get:
                    mock_get.return_value = MockResponse(
                        200,
                        """
                    {
                        "bot_uuid": "673d4c5f35be4d1e9e76eaafe56704c1",
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
                    """,
                    )
                    intent, accuracy, entities = bothub.predict("i want chinese food")
                    self.assertEqual(intent, "restaurant_search")
                    self.assertEqual(accuracy, 0.731929302865667)
                    self.assertEqual(type(entities), dict)
                    self.assertEqual(entities.get("cuisine"), "Mexican")
                    self.assertEqual(entities.get("location"), "center")
