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
