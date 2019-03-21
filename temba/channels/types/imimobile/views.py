import phonenumbers

from smartmin.views import SmartFormView

from django import forms
from django.utils.translation import ugettext_lazy as _

from ...models import Channel
from ...views import ALL_COUNTRIES, ClaimViewMixin


class ClaimView(ClaimViewMixin, SmartFormView):
    class IMIClaimForm(ClaimViewMixin.Form):
        country = forms.ChoiceField(choices=ALL_COUNTRIES)
        send_url = forms.URLField(label=_("Send URL"), help_text=_("The send URL for IMImobile"))
        phone_number = forms.CharField(label=_("Phone Number"), help_text=_("The phone number being added"))
        username = forms.CharField(label=_("Username"), help_text=_("The username for your API account"))
        password = forms.CharField(label=_("Password"), help_text=_("The password for your API account"))

        def clean_phone_number(self):
            phone = self.cleaned_data["phone_number"]

            # short code should not be formatted
            if len(phone) <= 6:
                return phone

            phone = phonenumbers.parse(phone, self.cleaned_data["country"])
            return phonenumbers.format_number(phone, phonenumbers.PhoneNumberFormat.E164)

    form_class = IMIClaimForm

    def form_valid(self, form):
        user = self.request.user
        data = form.cleaned_data
        org = user.get_org()

        if not org:  # pragma: no cover
            raise Exception(_("No org for this user, cannot claim"))

        config = {
            Channel.CONFIG_SEND_URL: data["send_url"],
            Channel.CONFIG_USERNAME: data["username"],
            Channel.CONFIG_PASSWORD: data["password"],
        }

        self.object = Channel.create(
            org,
            user,
            data["country"],
            "IMI",
            name=data["phone_number"],
            address=data["phone_number"],
            config=config,
            role=Channel.ROLE_CALL,
        )

        return super(ClaimView, self).form_valid(form)
