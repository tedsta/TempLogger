#!/usr/bin/env python

from socketio import socketio_manage
from socketio.server import SocketIOServer
from socketio.namespace import BaseNamespace
from socketio.mixins import RoomsMixin, BroadcastMixin

from degree_days_since import degree_days_since

class LoggerNamespace(BaseNamespace, RoomsMixin, BroadcastMixin):
    def on_start_end_datetime(self, base_temp, ambient_probe, start, end):
        start = start.replace("-", "_").replace(" ", "_").replace(":", "_")
        end = end.replace("-", "_").replace(" ", "_").replace(":", "_")
        deg_days = degree_days_since(float(base_temp), ambient_probe=="ambient", start, end)
        self.broadcast_event('degree_days', str(deg_days)) 
        #dgs = degree_days_since(20, start, end)
        #self.broadcast_event('degree_days', str(dgs)) 
        # Just have them join a default-named room
        self.join('main_room')

    def recv_disconnect(self):
        self.disconnect(silent=True)

    def on_user_message(self, msg):
        self.emit_to_room('main_room', 'msg_to_room',
            self.socket.session['nickname'], msg)

    def recv_message(self, message):
        print "PING!!!", message

###########################################################

def not_found(start_response):
    start_response("404 Not Found", [])
    return ["<h1>Not Found</h1>"]

class Application:
    def __init__(self):
        self.request = {"nicknames":[]}

    def __call__(self, environ, start_response):
        path = environ['PATH_INFO'].strip('/')

        if not path:
            with open("index.html", "r") as f:
                response_body = f.read()

            # HTTP response code and message
            status = '200 OK'

            # These are HTTP headers expected by the client.
            # They must be wrapped as a list of tupled pairs:
            # [(Header name, Header value)].
            response_headers = [('Content-Type', 'text/html'),
                               ('Content-Length', str(len(response_body)))]

            # Send them to the server using the supplied function
            start_response(status, response_headers)

            # Return the response body.
            # Notice it is wrapped in a list although it could be any iterable.
            return [response_body]
        elif path.startswith("socket.io"):
            socketio_manage(environ, {'': LoggerNamespace}, self.request)
        else:
            with open(path, "r") as f:
                data = f.read()

                if path.endswith(".js"):
                    content_type = "text/javascript"
                elif path.endswith(".css"):
                    content_type = "text/css"
                elif path.endswith(".swf"):
                    content_type = "application/x-shockwave-flash"
                else:
                    content_type = "text/html"

                start_response('200 OK', [('Content-Type', content_type), ('Content-Length', len(data))])
                return [data]            
            return not_found(start_response)

###############################################################

def main():
    httpd = SocketIOServer(('0.0.0.0', 8000), Application(), resource="socket.io")
    httpd.serve_forever()

if __name__ == "__main__":
    main()

