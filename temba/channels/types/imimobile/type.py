from django.utils.translation import ugettext_lazy as _

from temba.channels.types.imimobile.views import ClaimView
from temba.contacts.models import TEL_SCHEME

from ...models import ChannelType


class ImiMobileType(ChannelType):
    """
    An IMImobile channel
    """

    code = "IMI"
    category = ChannelType.Category.PHONE

    name = "IMImobile"
    claim_blurb = _(
        """Easily add a two way number you have configured with <a href="https://imimobile.com/">IMImobile</a> using their APIs."""
    )
    claim_view = ClaimView

    schemes = [TEL_SCHEME]
    max_length = 1600
    available_timezones = ["Asia/Kolkata"]

    ivr_protocol = ChannelType.IVRProtocol.IVR_PROTOCOL_IMI

    configuration_blurb = _(
        """
        Your IMImobile configuration URLs are as follows. These should have been set up automatically when claiming your number.
        """
    )

    configuration_urls = (
        dict(
            label=_("Callback URL for Delivery Receipt"),
            url="https://{{ channel.callback_domain }}{% url 'handlers.imimobile_call_handler' channel.uuid %}",
            description=_(
                "The delivery URL is called by IMImobile when a message is successfully delivered to a recipient."
            ),
        ),
    )
