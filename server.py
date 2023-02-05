import socket
from http import HTTPStatus
from datetime import datetime, timedelta
from pytz import timezone
import re

HOST = "127.0.0.1"
PORT = 11111
TEXT_END_OF_STRING = '\r\n'
BROWSER_END_OF_STRING = '\r\n<br>'
END_OF_STREAM = TEXT_END_OF_STRING + TEXT_END_OF_STRING


def clientDataParse(client_data, address):
    browser = re.search(r"(.*)User-Agent: (.*)(Firefox|Chrome|Opera)", client_data, re.MULTILINE)
    if browser is not None:
        END_OF_STRING = BROWSER_END_OF_STRING
    else:
        END_OF_STRING = TEXT_END_OF_STRING
    client_data_arr = client_data.split(END_OF_STREAM)
    headers = client_data_arr[0].split(TEXT_END_OF_STRING)
    request = headers[0]
    request_arr = headers[0].split(' ')
    code = 200
    if ('status' in request):
        status = request_arr[1]
        code = int(status[9:])
    try:
        code_text = HTTPStatus(code).phrase
    except:
        code = 200
        code_text = HTTPStatus(code).phrase

    response_message = f"Request Method: {request_arr[0]}{END_OF_STRING}"
    response_message += f"Request Source: ('{address[0]}', {address[1]}){END_OF_STRING}"
    response_message += f"Response Status: {code} {code_text}{END_OF_STRING}"
    cnt = 1
    while cnt < len(headers):
        header_value = headers[cnt].split(': ')
        response_message += f"header-name: {header_value[0]}-{header_value[1]}{END_OF_STRING}"
        cnt += 1

    return response_message


def handle_client(connection, address):
    client_data = ''
    with connection:
        while True:
            data = connection.recv(1024)
            if not data:
                break
            client_data += data.decode()
            if END_OF_STREAM in client_data:
                break

        response_message = clientDataParse(client_data, address)

        http_message = response_message.encode()
        http_message_sz = len(http_message)

        http_response = f"HTTP/1.0 200 OK{TEXT_END_OF_STRING}"
        http_response += f"Server: otusdemo{TEXT_END_OF_STRING}"
        tz = timezone('GMT')
        dt = datetime.now(tz=tz).strftime(("%a, %d %b %Y %I:%M:%S %Z"))
        http_response += f"Date: {dt}{TEXT_END_OF_STRING}"
        http_response += f"Content-Type: text/html; charset=UTF-8{TEXT_END_OF_STRING}"
        http_response += f"Content - Length: {http_message_sz}{TEXT_END_OF_STRING}"
        http_response += TEXT_END_OF_STRING

        connection.send(http_response.encode()
                        + response_message.encode()
                        + TEXT_END_OF_STRING.encode())


def server():
    with socket.socket() as serverSocket:
        serverSocket.bind((HOST, PORT))
        serverSocket.listen()
        while True:
            (clientConnection, clientAddress) = serverSocket.accept()
            handle_client(clientConnection, clientAddress)


if __name__ == '__main__':
    server()
