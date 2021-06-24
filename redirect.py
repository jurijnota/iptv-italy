#!/usr/bin/env python3
import re
import os
import json
import requests as req
import socketserver
from http.server import BaseHTTPRequestHandler


PORT = 80
LISTEN_ADDR = '127.0.0.1'
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

with open('{}/channels.json'.format(SCRIPT_DIR), 'r') as f:
    CHANNELS = json.load(f)

_streamIdRegex = re.compile(r'(?:[\?|&]([^\s&=]*)=([^\s&=]*))')


class HTTPRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        # Get queries from the request
        queries = dict(_streamIdRegex.findall(self.path))
        stream_id = str(queries.get('id'))

        for key, value in CHANNELS.get('Sky', {}).items():
            id = value.get('id')
            if stream_id == id:
                jsonUrl = 'https://apid.sky.it/vdp/v1/getLivestream?id={}&isMobile=false'.format(id)
                jsonReq = req.get(jsonUrl)
                if not jsonReq.ok:
                    self.send_response(jsonReq.status_code)
                    self.end_headers()
                    self.wfile.write(jsonReq.content)
                else:
                    chJson = json.loads(jsonReq.text)
                    if 'streaming_url' not in chJson.keys():
                        self.send_response(404)
                        self.end_headers()
                        self.wfile.write(b'Could not find "streaming_url" in JSON.')
                    else:
                        self.send_response(301)
                        self.send_header('Location', chJson['streaming_url'])
                        self.end_headers()
                break
        else:
            self.send_response(404)
            self.end_headers()
            body = 'Could not find streaming id {}.'.format(stream_id)
            self.wfile.write(body.encode(encoding='UTF-8'))


if __name__ == '__main__':
    with socketserver.TCPServer((LISTEN_ADDR, PORT), HTTPRequestHandler) as httpd:
        print("serving at port", PORT)
        httpd.serve_forever()