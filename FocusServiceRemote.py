import zmq

class FocusServiceRemote():
    #context = zmq.Context()
    def __init__(self):
        self.context = zmq.Context()
        # Socket to talk to server
        print("Connecting to focus score server...")
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect("tcp://localhost:5555")

    def get_score(self,data):
        # Send request, waiting each time for a response
        print("Sending request")
        self.socket.send_pyobj(data)

        #  Get the reply
        self.message = self.socket.recv()
        score = int(self.message)
        print("Received reply [score = %d ]" %score)
        return score