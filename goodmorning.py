# -*- coding: utf-8 -*-
import random
import logging
import requests
import json
from datetime import datetime
from dateutil.tz import gettz
from typing import Union, List

from ask_sdk_model import ui
from ask_sdk.standard import StandardSkillBuilder
from ask_sdk_core.dispatch_components import (
    AbstractRequestHandler, AbstractExceptionHandler,
    AbstractRequestInterceptor, AbstractResponseInterceptor)
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_model import Response, IntentRequest
from ask_sdk_model.interfaces.connections import SendRequestDirective
from ask_sdk_model.interfaces.alexa.presentation.apl import (RenderDocumentDirective, ExecuteCommandsDirective, SpeakItemCommand, AutoPageCommand, HighlightMode)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def http_get(url):
    """Return a response JSON for a GET call from `request`."""
    # type: (str, Dict) -> Dict
    response = requests.get(url)

    if response.status_code < 200 or response.status_code >= 300:
        response.raise_for_status()

    return response.json()

def _load_apl_document(file_path):
    # type: (str) -> Dict[str, Any]
    """Load the apl json document at the path into a dict object."""
    with open(file_path) as f:
        return json.load(f)

class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In LaunchRequestHandler")

        price_api_link = "https://min-api.cryptocompare.com/data/price?fsym=BTC&tsyms=USD&api_key=4ca8ca1f2f7499823cde74ea2212edbd64d972f770b8d28708224065f262bf46&e=Coinbase"
        price_api_result = http_get(price_api_link)
        price = "The price of Bitcoin is {} US Dollars.".format(str('%.f' % list(price_api_result.values())[0]))

        hi = "Good morning! "
        bye = " Have a great day!"

        time = "The time is: " + str(datetime.now(gettz("Europe/Bucharest")).hour) + " and " + str(datetime.now(gettz("Europe/Bucharest")).minute) + " minutes. "

        weather_api_link = "https://api.darksky.net/forecast/c0ab99fade4c790cf3ef32793717e258/44.4396,26.0963"
        bucharest = http_get(weather_api_link)
        celsius = round((bucharest["currently"]["temperature"] - 32) * 5 / 9)
        temperature = "The temperature outside is {} degrees. ".format(celsius)

        speech = "<speak><amazon:effect name='whispered'>" + hi + "<break time='0.25s'/>" + time + "<break time='0.25s'/>" + temperature + "<break time='0.25s'/>" + price + "<break time='0.25s'/>" + bye + "</amazon:effect></speak>"
            
        handler_input.attributes_manager.session_attributes["lastSpeech"] = speech

        if handler_input.request_envelope.context.system.device.supported_interfaces.alexa_presentation_apl:
            return handler_input.response_builder.speak(speech).add_directive(
                                RenderDocumentDirective(
                                    token="pagerToken",
                                    document=_load_apl_document("aplprice.json"),
                                    datasources={
                                        "bodyTemplate6Data": {
                                            "type": "object",
                                            "objectId": "bt6Sample",
                                            "backgroundImage": {
                                                "sources": [
                                                    {
                                                        "url": "https://yakkie.app/wp-content/uploads/2019/06/myback.png",
                                                        "size": "small",
                                                        "widthPixels": 0,
                                                        "heightPixels": 0
                                                    },
                                                    {
                                                        "url": "https://yakkie.app/wp-content/uploads/2019/06/myback.png",
                                                        "size": "large",
                                                        "widthPixels": 0,
                                                        "heightPixels": 0
                                                    }
                                                ]
                                            },
                                            "textContent": {
                                                "primaryText": {
                                                    "type": "PlainText",
                                                    "text": str(datetime.now(gettz("Europe/Bucharest")).time())[:5]
                                                },
                                                "secondaryText": {
                                                    "type": "PlainText",
                                                    "text": "{} °C".format(celsius)
                                                },
                                                "tertiaryText": {
                                                    "type": "PlainText",
                                                    "text": str('%.f' % list(price_api_result.values())[0]) + " USD"
                                                }
                                            },
                                            "logoUrl": "https://yakkie.app/wp-content/uploads/2019/06/y.png",
                                            "hintText": "Good morning!"
                                        }
                                    }
                                )
                    ).set_should_end_session(True).response
            
        else:
            return handler_input.response_builder.speak(speech).set_card(
                ui.StandardCard(
                    title = str(datetime.now(gettz("Europe/Bucharest")).time())[:5],
                    text = "Good morning!",
                    image = ui.Image(
                        small_image_url = "https://yakkie.app/wp-content/uploads/2019/08/card.png",
                        large_image_url = "https://yakkie.app/wp-content/uploads/2019/08/card.png"
                    ))).set_should_end_session(True).response

class RepeatHandler(AbstractRequestHandler):
    """Repeat last fact/legend."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.RepeatIntent")(handler_input)

    def handle(self, handler_input):
        logger.info("In RepeatHandler")

        return handler_input.response_builder.speak("{}".format(handler_input.attributes_manager.session_attributes["lastSpeech"])).response

class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In HelpIntentHandler")
        
        speech = "Well, my little crypto friend, you just have to say, 'Good morning!', and I will provide you with the info you need to start your day. Your turn now!"

        handler_input.attributes_manager.session_attributes["lastSpeech"] = speech

        return handler_input.response_builder.speak(speech).ask(speech).response

class FallbackIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In FallbackIntentHandler")

        nice_fallbacks = ["Excuse me, I was checking my portfolio. Can you say it again?",
                          "<say-as interpret-as='interjection'>Damn</say-as>, my <prosody volume='loud'>wallet</prosody>coin looks so good! Can you repeat?",
                          "Sorry, I didn't get that. I was stacking satoshis. Can you rephrase?",
                          "Sorry, I got a text from Satoshi. Can you say that again?",
                          "Sorry, I was checking my <prosody volume='loud'>Bit</prosody>coin wallet. Please say that again.",
                          "I beg your pardon, I was checking the price of <prosody volume='loud'>Bit</prosody>coin. Come again?",
                          "Forgive me, I was texting this guy, Nakamoto. Say that again, please!",
                          "I'm sorry, I was buying some coins. Can you repeat?",
                          "Excuse me, Satoshi keeps calling me. Please repeat!",
                          "<prosody volume='loud'>Oups</prosody>, you caught me checking my <prosody volume='loud'>Bit</prosody>coin stack. Say that again, please!"]

        speech = random.choice(nice_fallbacks)

        return handler_input.response_builder.speak(speech).ask(speech).response

class SessionEndedHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_request_type("SessionEndedRequest")(handler_input) or
                is_intent_name("AMAZON.StopIntent")(handler_input) or
                is_intent_name("AMAZON.CancelIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In SessionEndedHandler")

        return handler_input.response_builder.speak(get_random_goodbye()).set_should_end_session(True).response

class CatchAllExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        sorrys = ["Sorry, I can't understand the command. Please try again!",
                  "I'm not sure I understand your wish. Say it again! I'm all ears.",
                  "I didn't catch that. Can you repeat, please?"]

        speech = random.choice(sorrys)

        handler_input.response_builder.speak(speech).ask(speech)

        return handler_input.response_builder.response

class RequestLogger(AbstractRequestInterceptor):
    """Log the request envelope."""
    def process(self, handler_input):
        # type: (HandlerInput) -> None
        logger.info("Request Envelope: {}".format(handler_input.request_envelope))

class ResponseLogger(AbstractResponseInterceptor):
    """Log the response envelope."""
    def process(self, handler_input, response):
        # type: (HandlerInput, Response) -> None
        logger.info("Response: {}".format(response))


sb = StandardSkillBuilder()

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedHandler())
sb.add_request_handler(RepeatHandler())
sb.add_exception_handler(CatchAllExceptionHandler())
sb.add_global_request_interceptor(RequestLogger())
sb.add_global_response_interceptor(ResponseLogger())

lambda_handler = sb.lambda_handler()

#End of program