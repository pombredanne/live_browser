<%inherit file="base.mako"/>

<%block name="title">Login</%block>

<a href="https://oauth.live.com/authorize?client_id=000000004C05390D&scope=wl.signin%20wl.basic&response_type=code&redirect_uri=${cherrypy.request.base}/callback">Login with your Windows Live account</a>
