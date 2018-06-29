import logging
import os
import signal
import sys

from multiprocessing.process import Process

sys.path.insert(0, os.path.abspath(os.path.realpath(__file__) + '/../../../'))

from oauth2 import Provider
from oauth2.error import UserNotAuthenticated
from oauth2.grant import AuthorizationCodeGrant
from oauth2.tokengenerator import Uuid4
from oauth2.store.memory import ClientStore, TokenStore
from oauth2.web import AuthorizationCodeGrantSiteAdapter
from oauth2.web.tornado import OAuth2Handler
from oauth2.client_authenticator import http_basic_auth
from oauth2.datatype import AccessToken
from tornado.ioloop import IOLoop
from tornado.web import Application, url

from tornado.web import RequestHandler
import urllib2
import json

WIO_SERVER_URL = "https://us.wio.seeed.io"

logging.basicConfig(level=logging.DEBUG)

class TestSiteAdapter(AuthorizationCodeGrantSiteAdapter):
    """
    This adapter renders a confirmation page so the user can confirm the auth
    request.
    """

    CONFIRMATION_TEMPLATE = """
<html>
    <body>
        <form method="GET">
            <div>
                <label for="email_address">email</label>
                <input type="email" name="email_address" id="email_address" />
            </div>
            <input type="hidden" name="client_id" value="{client_id}" />
            <input type="hidden" name="response_type" value="{response_type}" />
            <input type="hidden" name="state" value="{state}" />
            <input type="hidden" name="redirect_uri" value="{redirect_uri}" />
            <button>Send</button>
        </form>
    </body>
</html>
    """

    def render_auth_page(self, request, response, environ, scopes, client):
        url = "https://wioserver.southeastasia.cloudapp.azure.com/oa/authorize?" + request.query_string
        response.body = self.CONFIRMATION_TEMPLATE.format(url=url, client_id=request.get_param("client_id"), response_type=request.get_param("response_type"), state=request.get_param("state"), redirect_uri=request.get_param("redirect_uri"))

        return response

    def authenticate(self, request, environ, scopes, client):
        if request.method == "GET":
            if request.get_param("email_address") in {"t-matsuoka@seeed.co.jp"}:
                return ("https://us.wio.seeed.io", request.get_param("email_address"))

        raise UserNotAuthenticated

    def user_has_denied_access(self, request):
        return False

class DiscoverHandler(RequestHandler):
    def get(self):
        access_token = self.get_argument("access_token")
        nodes_obj = HttpGetObject("{}/v1/nodes/list?access_token={}".format(WIO_SERVER_URL, access_token))
        dis_obj = []
        for node in nodes_obj["nodes"]:
            node_obj = HttpGetObject("{}/v1/node/config?access_token={}".format(WIO_SERVER_URL, node["node_key"]))
            for connection in node_obj["config"]["connections"]:
                dis_obj.append({"name":node["name"], "sn":node["node_sn"], "con_port":connection["port"], "con_sku":connection["sku"]})
        dis_text = json.dumps(dis_obj)
        self.write(dis_text)

def HttpGetObject(url):
    req = urllib2.Request(url)
    res = urllib2.urlopen(req)
    res_text = res.read()
    res_obj = json.loads(res_text)
    return res_obj

#auth_url : https://wioserver.southeastasia.cloudapp.azure.com/oa/authorize
#token_url : https://wioserver.southeastasia.cloudapp.azure.com/oa/token

def run_auth_server():
    client_store = ClientStore()
    client_store.add_client(client_id="alexa.matsuoka", client_secret="xxxx", redirect_uris=["https://layla.amazon.com/api/skill/link/M2Q7FOC6AVxxxx", "https://pitangui.amazon.com/api/skill/link/M2Q7FOC6AVxxxx", "https://alexa.amazon.co.jp/api/skill/link/M2Q7FOC6AVxxxx"])

    token_store = TokenStore()
    token_store.save_token(AccessToken(client_id="alexa.matsuoka", grant_type="authorization_code", user_id="t-matsuoka@seeed.co.jp", token="xxxx"))

    provider = Provider(access_token_store=token_store, auth_code_store=token_store, client_store=client_store, token_generator=Uuid4(),client_authentication_source=http_basic_auth)
    provider.add_grant(AuthorizationCodeGrant(site_adapter=TestSiteAdapter(), unique_token=True))

    try:
        app = Application([
            url(provider.authorize_path, OAuth2Handler, dict(provider=provider)),
            url(provider.token_path, OAuth2Handler, dict(provider=provider)),
#            ("/discover", DiscoverHandler),
        ], debug = False)

        app.listen(8082)
        print("Starting OAuth2 server on http://localhost:8082/...")
        IOLoop.current().start()

    except KeyboardInterrupt:
        IOLoop.close()

def main():
    auth_server = Process(target=run_auth_server)
    auth_server.start()

    def sigint_handler(signal, frame):
        print("Terminating servers...")
        auth_server.terminate()
        auth_server.join()

    signal.signal(signal.SIGINT, sigint_handler)

if __name__ == "__main__":
    main()
