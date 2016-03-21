import os
import sys
import json
from datetime import datetime
from urlparse import urlparse, parse_qs, urlunparse

from twisted.web import proxy, http
from twisted.internet import reactor
from twisted.internet.error import CannotListenError


class ProxyRequestHandler(proxy.ProxyRequest):
    transferred_bytes = 0
    uptime = datetime.now()

    def response(self, code, message, body):
        self.setResponseCode(code, message)
        self.responseHeaders.addRawHeader('Content-Type', 'application/json')
        self.write(json.dumps(body, indent=4), False)
        self.finish()

    def write(self, data, transfer=True):
        """
        Override the write function of http.Request class
        to store the sentLength variable in transferred_bytes
        just when there is a real transfer
        """
        proxy.ProxyRequest.write(self, data)
        if transfer:
            ProxyRequestHandler.transferred_bytes += self.sentLength

    def process(self):
        """
        Override the process of ProxyRequest to handle
        range query and /stats endpoint

        """
        parsed = urlparse(self.uri)

        if not parsed.scheme:
            # Expose proxy statistics at /stats endpoint
            if parsed.path == '/stats':
                status, message = 200, 'Ok'
                self.response(
                    status, message,
                    {'code': status,
                     'message': message,
                     'stats':
                         {'transferred_bytes':
                             ProxyRequestHandler.transferred_bytes,
                          'uptime': str(datetime.now() - self.uptime)}}
                )
                return
            status, message = 404, 'Not Found'
            self.response(
                status, message,
                {'error':
                    {'code': status,
                     'message': message,
                     'description': 'Path %s not found' % parsed.path}}
            )
            return

        protocol = parsed[0]
        host = parsed[1]
        port = self.ports[protocol]
        if ':' in host:
            host, port = host.split(':')
            port = int(port)
        rest = urlunparse(('', '') + parsed[2:])
        if not rest:
            rest = rest + '/'
        class_ = self.protocols[protocol]
        headers = self.getAllHeaders().copy()

        # Getting the range from query
        try:
            range_from_query = self.args['range'][0]
        except KeyError:
            pass
        else:
            # Getting the range from header
            range_from_header = headers.get("range")
            if range_from_header:
                range_from_header = range_from_header.split('=')[1]

                if range_from_query != range_from_header:
                    status, message = 416, 'Range Not Satisfiable'
                    self.response(
                        status, message,
                        {'error':
                            {'code': status,
                             'message': message,
                             'description': 'Range specified in header and '
                                            'query but with different values'}}
                    )
                    return
            else:
                headers["range"] = "bytes=" + range_from_query

        if 'host' not in headers:
            headers['host'] = host
        self.content.seek(0, 0)
        s = self.content.read()
        clientFactory = class_(
            self.method, rest, self.clientproto, headers, s, self)
        self.reactor.connectTCP(host, port, clientFactory)


class ProxyModified(http.HTTPChannel):
    requestFactory = ProxyRequestHandler


class ProxyFactory(http.HTTPFactory):
    protocol = ProxyModified


if __name__ == '__main__':
    # Proxy port can be configured by ENV
    try:
        port = int(os.environ.get("PROXY_PORT"))
    except IndexError:
        port = 8080

    # Run the proxy
    try:
        reactor.listenTCP(port, ProxyFactory())
        reactor.run()
    except CannotListenError as e:
        print 'Please try another port:', e
