import json
from ws4py.client.threadedclient import WebSocketClient


class Connection(WebSocketClient):

    def opened(self):
        self.state = None

    def received_message(self, message):
        data = json.loads(message.data.decode())
        if data['message'] == 'state':
            self.state = data['data']
        elif data['message'] == 'turn':
            data = {'players': self.state['ours'], 'kick': None}
            self.send(json.dumps(data))


def main():
    ws_url = 'ws://localhost:9000/play/NEW'
    ws = Connection(ws_url)
    ws.connect()
    ws.run_forever()


if __name__ == '__main__':
    main()
