# coding=UTF-8

### Some global variables
CONF_NAME = 'server.conf'
TEMPLATES_DIRNAME = 'templates'



# Import all stuff we need
import os
import socket
import cherrypy
from mako.template import Template
from mako.lookup   import TemplateLookup


current_folder = os.path.dirname(__file__)
# Transform relative path to absolute
template_folder = os.path.join(current_folder, TEMPLATES_DIRNAME)



class MakoHandler(cherrypy.dispatch.LateParamPageHandler):
    """ Callable which sets response.body.
        Source: http://tools.cherrypy.org/wiki/Mako
    """

    def __init__(self, template, next_handler):
        self.template = template
        self.next_handler = next_handler

    def __call__(self):
        env = globals().copy()
        env.update(self.next_handler())
        return self.template.render(**env)



class MakoLoader(object):

    def __init__(self):
        self.lookups = {}

    def __call__(self, filename, directories=[template_folder], module_directory=None,
                 collection_size=-1, output_encoding='utf-8', input_encoding='utf-8',
                 encoding_errors='replace'):
        # Find the appropriate template lookup.
        key = (tuple(directories), module_directory)
        try:
            lookup = self.lookups[key]
        except KeyError:
            lookup = TemplateLookup(directories=directories,
                                    module_directory=module_directory,
                                    collection_size=collection_size,
                                    input_encoding=input_encoding,
                                    output_encoding=output_encoding,
                                    encoding_errors=encoding_errors)
            self.lookups[key] = lookup
        cherrypy.request.lookup = lookup
        # Replace the current handler.
        cherrypy.request.template = t = lookup.get_template(filename)
        cherrypy.request.handler = MakoHandler(t, cherrypy.request.handler)



def authorize():
    """ This method check session data and allow the current user to access a page or not
        Source: http://tools.cherrypy.org/wiki/HandlerTool
    """
    PASSTHROUGH_URLS = ['/static', '/favicon.', '/login', '/callback']
    authorized = has_session = cherrypy.session.get('access_token')
    if not authorized:
        for url in PASSTHROUGH_URLS:
            if cherrypy.request.path_info.startswith(url):
                authorized = True
                break
    if authorized:
        # Allow normal handler to run and display the page
        return False
    else:
        raise cherrypy.HTTPRedirect('/login')
        # Suppress normal handler from running
        return True



def main():
    # Set default network timeout
    socket.setdefaulttimeout(10)

    # Here is the default config for static content
    conf = { '/static': { 'tools.staticdir.on' : True
                        , 'tools.staticdir.dir': os.path.join(current_folder, 'static')
                        }
           , '/favicon.png': { 'tools.staticfile.on'      : True
                             , 'tools.staticfile.filename': os.path.join(current_folder, 'static/favicon.png')
                             }
           }
    cherrypy.config.update(conf)

    # Enable sessions
    cherrypy.config.update( { 'tools.sessions.on'          : True
                            , 'tools.sessions.timeout'     : 60
                            #, 'tools.sessions.storage_type': "file"
                            #, 'tools.sessions.storage_path': os.path.join(current_folder, 'sessions')
                            })

    # Let our server honor proxied requests
    cherrypy.config.update({'tools.proxy.on': True})

    # Gzip eveything that looks like text
    cherrypy.config.update({'tools.gzip.mime_types': ['text/*', 'application/json', 'application/javascript']})

    # Load and apply the global config file
    conf_file = os.path.join(current_folder, CONF_NAME)
    cherrypy.config.update(conf_file)

    # Setup our Mako decorator
    loader = MakoLoader()
    cherrypy.tools.mako = cherrypy.Tool('on_start_resource', loader)

    # Register a tool to check for authentication
    cherrypy.tools.authorize = cherrypy._cptools.HandlerTool(authorize)

    # Import our application logic
    from app import Root

    # Prepare the app
    app_root = Root()
    app = cherrypy.tree.mount(app_root, config=conf)

    # Start the engine
    cherrypy.engine.start()

    # Wait for requests
    cherrypy.engine.block()



if __name__ == '__main__':
    main()

