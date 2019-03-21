import pytz
from django.urls import reverse

from temba.tests import TembaTest
from ...models import Channel


class ImiMobileTypeTest(TembaTest):
    def test_claim(self):
        Channel.objects.all().delete()

        self.login(self.admin)
        url = reverse("channels.types.imimobile.claim")

        # shouldn't be able to see the claim play mobile page if we aren't part of that group
        response = self.client.get(reverse("channels.channel_claim"))
        self.assertNotContains(response, url)

        # but if we are in the proper time zone
        self.org.timezone = pytz.timezone("Asia/Kolkata")
        self.org.save()

        response = self.client.get(reverse("channels.channel_claim"))
        self.assertContains(response, "IMImobile")
        self.assertContains(response, url)

        # try to claim a channel
        response = self.client.get(url)
        post_data = response.context["form"].initial

        post_data["send_url"] = "http://eapps.imimobile.com/rapidpro/api/outbound/OBDInit"
        post_data["country"] = "IN"
        post_data["phone_number"] = "123456789"
        post_data["username"] = "unicef"
        post_data["password"] = "HmGWbdCFiJBj5bui"

        response = self.client.post(url, post_data)

        channel = Channel.objects.get()

        self.assertEqual("IN", channel.country)
        self.assertEqual(
            "http://eapps.imimobile.com/rapidpro/api/outbound/OBDInit", channel.config[Channel.CONFIG_SEND_URL]
        )
        self.assertEqual("unicef", channel.config[Channel.CONFIG_USERNAME])
        self.assertEqual("HmGWbdCFiJBj5bui", channel.config[Channel.CONFIG_PASSWORD])
        self.assertEqual("+91123456789", channel.address)
        self.assertEqual("IMI", channel.channel_type)

        Channel.objects.all().delete()

        post_data["phone_number"] = "1122"
        response = self.client.post(url, post_data)
        channel = Channel.objects.get()
        self.assertEqual(post_data["phone_number"], channel.address)

        config_url = reverse("channels.channel_configuration", args=[channel.uuid])
        self.assertRedirect(response, config_url)

        response = self.client.get(config_url)
        self.assertEqual(200, response.status_code)

        call_handler_event_url = reverse("handlers.imimobile_call_handler", args=[channel.uuid])

        payload = """<?xml version="1.0"?>
        <evt-notification>
            <evt-id>release</evt-id>
            <evt-date>2018-12-12 17:59:45.786</evt-date>
            <evt-seqno>2</evt-seqno>
            <evt-info>
                <tid>1544617781_96918382</tid>
                <sid>6b4e89c4-825a-438a-950d-29cc5f06c27a</sid>
                <src>2</src>
                <ani>1234567890</ani>
                <dnis>1234567890</dnis>
                <correlationid>636802479229739872919810410133</correlationid>
                <offered-on>2018-12-12 17:59:42.810</offered-on>
                <accepted-on>2018-12-12 17:59:45.786</accepted-on>
            </evt-info>
        </evt-notification>"""

        response = self.client.post(call_handler_event_url, payload, content_type="application/xml")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.content), 64)
