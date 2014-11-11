import websocket, httplib, sys, asyncore
def _onopen(ws):
    print("opened!")

def _onshipsg(ws,msg):
    print("msg: " + str(msg))

def _onclose(ws):
    print("closed!")


def connect(server, port):

    print("connecting to: %s:%d" %(server, port))

    conn  = httplib.HTTPConnection(server,port)
    conn.request('POST','/socket.io/1/')
    resp  = conn.getresponse() 
    hskey = resp.read().split(':')[0]
    ws = websocket.WebSocketApp(
                'ws://'+server+':'+str(port)+'/socket.io/1/websocket/'+hskey,
                on_open   = _onopen,
                on_shipstat = _onmessage,
                on_close = _onclose)

    return ws, hskey




if __name__ == '__main__':

    server = 'ninjanode.tn42.com'
    port = 80

    ws,key = connect(server, port)
    print key

    ws.run_forever()