from http.server import HTTPServer, BaseHTTPRequestHandler
import pathlib
import urllib.parse
import mimetypes
import json
import socket
import logging
from threading import Thread
from datetime import datetime

BASE_DIR = pathlib.Path()
SERVER_IP = '127.0.0.1'
SERVER_PORT = 5000
BUFFER = 1024
today = datetime.now()

def send_data_to_socket(body):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.sendto(body, (SERVER_IP, SERVER_PORT))
    client_socket.close()

class HTTPHadler(BaseHTTPRequestHandler):


    def do_POST(self):
        body = self.rfile.read(int(self.headers['Content-Length']))
        #body = urllib.parse.unquote_plus(body.decode())
        #payload = {key: value for key, value in [el.split('=') for el in body.split('&')]}
        #with open(BASE_DIR.joinpath('storage/data.json'), 'w', encoding='utf-8') as fd:
        #    json.dump(payload, fd, ensure_ascii=False)
        send_data_to_socket(body)
        
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()


    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        match route.path:
            case "/":
                self.send_html('index.html')
            case "/message.html":
                self.send_html('message.html')
            case _:
                file = BASE_DIR/route.path[1:]
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html('error.html', 404)


    def send_html(self, file_name, status_code = 200):
        self.send_response(status_code)
        self.send_header('Content_Type', 'text/html')
        self.end_headers()
        with open(file_name, 'rb') as f:
            self.wfile.write(f.read())


    def send_static(self, file_name):
        self.send_response(200)
        mt, *other = mimetypes.guess_type(file_name)
        if mt:
            self.send_header('Content_Type', mt)
        else:
            self.send_header('Content_Type', 'text/plain')
        self.end_headers()
        with open(file_name, 'rb') as f:
            self.wfile.write(f.read())

def run(server=HTTPServer, handler=HTTPHadler):
    address = ('', 3000)
    http_server = server(address, handler)
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()

def save_data(data):
    body = urllib.parse.unquote_plus(data.decode())
    logging.error(f"Body - {body}")
    try:
        payload = {f'{today}': {key: value for key, value in [el.split('=') for el in body.split('&')]}}
        logging.error(f"Payload - {payload}")
        with open(BASE_DIR.joinpath('storage/data.json'), encoding='utf-8') as f:
            data_file = json.load(f)
            if data_file.get('data'):
                data_file['data'].append(payload)
            else:
                data_file['data'] = [payload]
                
        with open(BASE_DIR.joinpath('storage/data.json'), 'w', encoding='utf-8') as fd:
            logging.error(f"Data - {data_file}")
            json.dump(data_file, fd, ensure_ascii=False, indent=2)
            
    except ValueError as err:
        logging.error(f"Field parse data {body} with error {err}")
    except OSError as err:
        logging.error(f"Field write data {body} with error {err}")

def run_socket_server(ip, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = ip, port
    server_socket.bind(server)
    
    try:
        while True:
            data, address = server_socket.recvfrom(BUFFER)
            save_data(data)
    except KeyboardInterrupt:
        logging.info('Socket server stoped')
    finally:
        server_socket.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(threadName)s %(message)s")
    thread_server = Thread(target=run)
    thread_server.start()

    thread_socket = Thread(target=run_socket_server(SERVER_IP, SERVER_PORT))
    thread_socket.start()