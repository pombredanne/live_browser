import cherrypy
import urllib
import urllib2
import json
import httplib2
#httplib2.debuglevel = 1
from httplib2 import Http
from urllib import urlencode



class Root():


    # Our whole application is private: nobody can see anything of it unless he's authorized
    _cp_config = {'tools.authorize.on': True}


    @cherrypy.expose
    def default(self):
        raise cherrypy.HTTPRedirect('/home')


    def call_ws(self, query='me'):
        API_URL = 'https://apis.live.net/v5.0'
        params = { 'access_token': cherrypy.session.get('access_token')
                 }
        headers = { 'Accept'         : 'application/json'
                  # Force identity else httplib2 default to deflate/gzip which raise the following exception with the python-httplib2 0.6.0-4 Debian Squeeze package:
                  #   error: Error -3 while decompressing data: incorrect header check
                  , 'Accept-Encoding': 'identity'
                  }
        query_url = full_url = '%s/%s' % (API_URL, query)
        cherrypy.log('Calling the web service at %s' % query_url, 'APP')
        if params:
            full_url = '%s?%s' % (query_url, urlencode(params))
        h = Http()
        response, content = h.request(full_url, "GET", headers=headers)
        cherrypy.log('Web service returned: %r' % [response, content], 'APP')
        return json.loads(content)


    @cherrypy.expose
    def callback(self, code):
          """ See documentation and reference there:
                * http://msdn.microsoft.com/en-us/library/hh243649.aspx
                * http://msdn.microsoft.com/en-us/library/hh243647.aspx
          """
          cherrypy.log('Got a callback code: %r' % code, 'APP')
          # We've got a code, we're ready to exchange it to a true access token
          params = {
              'client_id': '000000004C05390D',
              'redirect_uri': '%s/callback' % cherrypy.request.base,
              'client_secret': 'fiMIb91LhBu9T5LPk4hPd2QaqKXLTY4a',
              'code': code,
              'grant_type': 'authorization_code'
              }
          url = 'https://oauth.live.com/token'
          post_data = urllib.urlencode(params)
          request = urllib2.Request(url, post_data)
          response = urllib2.urlopen(request)
          body = response.read()
          creds = json.loads(body)
          cherrypy.log('Callback code exchanged to: %r' % creds, 'APP')
          # Save the current credentials to the session
          for (k, v) in creds.items():
              cherrypy.session[k] = v
          raise cherrypy.HTTPRedirect('/home')


    @cherrypy.expose
    @cherrypy.tools.mako(filename="login.mako")
    def login(self):
        # Force session expiration each time we are redirected to the login screen.
        self.expire_session()
        return {}


    @cherrypy.expose
    def logout(self):
        self.expire_session()
        raise cherrypy.HTTPRedirect('/login')


    def expire_session(self):
        """ Helper method to expire the current session
        """
        try:
            cherrypy.session.delete()
        except KeyError:
            pass
        cherrypy.lib.sessions.expire()


    @cherrypy.expose
    @cherrypy.tools.mako(filename="home.mako")
    def home(self):
        me = self.call_ws('me')
        return { 'me': me
               }

