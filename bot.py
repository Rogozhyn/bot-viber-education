from flask import Flask, request, Response
from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration
from viberbot.api.messages import VideoMessage
from viberbot.api.messages.text_message import TextMessage
from viberbot.api.viber_requests import ViberConversationStartedRequest
from viberbot.api.viber_requests import ViberFailedRequest
from viberbot.api.viber_requests import ViberMessageRequest
from viberbot.api.viber_requests import ViberSubscribedRequest
from viberbot.api.viber_requests import ViberUnsubscribedRequest
import configparser
import logging
from pyngrok import ngrok  # Install the pyngrok library

PUBLIC_URL = None
WEBHOOK_URL = None


def load_config(file_path):
    config = configparser.ConfigParser()
    config.read(file_path)
    return config


config_file_path = 'config.ini'
config = load_config(config_file_path)
bot_configuration = BotConfiguration(
    name=config['Credentials']['name'],
    avatar=config['Credentials']['avatar'],
    auth_token=config['Credentials']['auth_token']
)
viber = Api(bot_configuration)
app = Flask(__name__)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


@app.route('/')
def index():
    return '<h1>Hello World!</h1>\n<h2>This is Flask with Viber Bot</h2>'


'''
@app.route('/start_ngrok')
def start_ngrok():
    global PUBLIC_URL
    # Start ngrok and create a public tunnel
    PUBLIC_URL = ngrok.connect(port=8087)
    return PUBLIC_URL
    
    
@app.route('/register-webhook', methods=['POST'])
def register_webhook():
    global PUBLIC_URL, WEBHOOK_URL
    # Extract the public URL
    WEBHOOK_URL = PUBLIC_URL.replace("http://", "https://") + "/viber-webhook"

    # Your Viber API credentials
    api_key = config['Credentials']['auth_token']
    # webhook_url = "YOUR_WEBHOOK_URL"  # Replace with your dynamic webhook URL

    # Make a request to Viber's API to set the webhook
    response = requests.post(
        f"https://api.viber.com/pa/set_webhook?url={WEBHOOK_URL}",
        headers={"X-Viber-Auth-Token": api_key}
    )

    if response.status_code == 200:
        return 'Webhook registered successfully'
    else:
        return 'Webhook registration failed'
'''


@app.route('/viber-webhook', methods=['POST'])
def incoming():
    logger.debug("received request. post data: {0}".format(request.get_data()))
    # every viber message is signed, you can verify the signature using this method
    if not viber.verify_signature(request.get_data(), request.headers.get('X-Viber-Content-Signature')):
        return Response(status=403)

    # this library supplies a simple way to receive a request object
    viber_request = viber.parse_request(request.get_data())

    if isinstance(viber_request, ViberMessageRequest):
        message = viber_request.message.text
        try:
            result = str(eval(message))
        except:
            result = "?"
        # lets echo back
        viber.send_messages(viber_request.sender.id, [TextMessage(text=message + " = " + result)])
    elif isinstance(viber_request, ViberSubscribedRequest):
        viber.send_messages(viber_request.sender.id, [TextMessage(text="thanks for subscribing!")])
    # elif isinstance(viber_request, ViberFailedRequest):
    # logger.warning("client failed receiving message. failure: {0}".format(viber_request))

    return Response(status=200)


if __name__ == "__main__":
    context = ('server.crt', 'server.key')
    # app.run(host='0.0.0.0', port=8087, debug=True, ssl_context=context)
    app.run(port=8087)
