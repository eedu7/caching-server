import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import time
import requests
import argparse
from pprint import pprint
import redis
hostName = "localhost"

REDIS_URL = "redis://127.0.0.1:6379"

redis = redis.from_url(REDIS_URL, encoding="utf8", decode_responses=True)
cache_expiry = 60 * 60 * 24

def get_cache_data(url):
    json_data = redis.get(url)
    if json_data:
        return json.loads(json_data)

def set_cache_data(url, data):
    json_value = json.dumps(data)
    redis.set(url, json_value, ex=cache_expiry)
    return True
class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        external_url = self.server.external_url

        response = get_cache_data(external_url)

        if response is None:
            response = requests.get(external_url)

            if response.status_code == 200:
                response = response.json()
                set_cache_data(external_url,response)
            else:
                response = {
                    "error": "Failed to fetch data from external URL"
                }

        pprint(response)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(f"<html><body>{response}</body></html>".encode('utf-8'))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Simple HTTP Server with external URL request.')
    parser.add_argument('--port', "--p", type=int, default=8080, help='Port number to run the server on')
    parser.add_argument('--origin', "--o", type=str, required=True, help='External URL to fetch data from')
    parser.add_argument('--clear-cache', action="store_true", help='To clear all cache')
    args = parser.parse_args()

    serverPort = args.port if args.port else args.p
    external_url = args.origin if args.origin else args.o
    clearCache = args.clear_cache


    if clearCache:
        redis.flushall()
        print("Clearing all the caches")
        exit()




    webServer = HTTPServer((hostName, serverPort), MyServer)
    webServer.external_url = external_url
    print(f"Server started http://{hostName}:{serverPort}")
    print(f"Requesting data from: {external_url}")

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:

        webServer.server_close()
        print("Server stopped.")
