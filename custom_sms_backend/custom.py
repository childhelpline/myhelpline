from AfricasTalkingGateway import AfricasTalkingGateway, AfricasTalkingGatewayException

from blackbox import Blackbox
from django.conf import settings
from sendsms.backends.base import BaseSmsBackend

class BlackboxSmsBackend(BaseSmsBackend):
    api_key = settings.BLACKBOX_API_KEY
    api_signature = settings.BLACKBOX_API_SIGNATURE
    shortcode = settings.BLACKBOX_SHORT_CODE
    keyword = settings.BLACKBOX_KEYWORD

    blackbox = Blackbox(api_key, api_signature)

    def send_messages(self, messages):
        for message in messages:
            for to in message.to:
                try:
                    self.blackbox.queue_sms(
                        to,
                        message.body,
                        self.shortcode,
                        self.keyword)
                    self.blackbox.send_sms()

                except:
                    if not self.fail_silently:
                        raise

class AfricasTalkingSmsBackend(BaseSmsBackend):
    api_key = settings.AFRICASTALKING_API_KEY
    api_username = settings.AFRICASTALKING_API_USERNAME

    gateway = AfricasTalkingGateway(api_username, api_key)

    def send_messages(self, messages):
        for message in messages:
            for to in message.to:
                try:
                    self.gateway.sendMessage(
                        to,
                        message.body,
                        )

                except:
                    if not self.fail_silently:
                       raise
