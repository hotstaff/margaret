# coding: UTF-8
# Copyright 2020 Hideto Manjo.
#
# Licensed under the MIT License

"""Network virtual memory module."""
import threading
import socket

from margaret.core.memory import VirtualMemory
from margaret.core.formats import NumpyRawFormat

class NetVM(VirtualMemory):
    """NetVM.

    Network virtual memory is virtual memory with a communication
    function. Memory data can be sent and received via UDP/IP.
    """

    def __init__(self, slot, host="", port=5000):
        """Init."""
        super(NetVM, self).__init__(slot)

        self.host = host
        self.port = port
        self._callbacks = [lambda array, addr, slot: True] * slot

    def resv(self, slot):
        """Receive
        Open the UDP socket and receive the data. The packet receives
        only the specified number of bytes and discards the packet if
        the number of bytes does not match. If the number of bytes
        matches, the reception is successful and the memory is rewritten.
        Executes the function specified in the callback.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as soc:
            soc.bind((self.host, self.port + slot))

            while True:
                data, addr = soc.recvfrom(self.read(slot).nbytes + 1)
                if len(data) != self.read(slot).nbytes:
                    continue

                shape, dtype = self.shape(slot)
                array = NumpyRawFormat.decode(data, shape, dtype)
                self.write(slot, array)
                self._callbacks[slot](array, addr, slot)

    def send(self, slot, host, port, src_port=3000):
        """Send
        Sends memory data for the specified slot via a UDP socket.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as soc:
            soc.bind((self.host, src_port))
            mem = self.read(slot)
            soc.sendto(mem, (host, port))

    def listen(self):
        """Listen
        Start a thread for receiving. The port number will be the
        specified port number + slot number.
        """
        threads = []
        for i in range(self._slot):
            th = threading.Thread(target=self.resv, args=(i, ), daemon=True)
            threads.append(th)
            th.start()

    def on(self, slot, callback):
        """Set a callback event for the slot."""
        if callable(callback):
            self._callbacks[slot] = callback

    def off(self, slot):
        """Unsets the slot callback event."""
        self._callbacks[slot] = lambda array, addr, slot: True

    def info(self):
        """Return info string of the memory."""
        message = []
        for i, item in enumerate(self.shape()):
            message.append(f"slot: {i}, shape: {item[0]}, "
                           f"dtype: {item[1]}, port: {self.port + i}")
        return "\n".join(message)


if __name__ == "__main__":
    import time
    import numpy as np
    N1 = NetVM(3)
    N1.set(0, (3, 3), "float32")
    N1.set(1, (3, 3), "float32")
    N1.set(2, (3, 4), "float32")
    N1.write(1, np.ones((3, 3), dtype=np.float32))
    N1.write(2, np.ones((3, 4), dtype=np.float32))

    def on_resv(array, addr, slot):
        print(f"resv slot{slot} {array.nbytes} bytes from {addr[0]}")

    N1.on(0, on_resv)
    N1.listen()
    print("Listening...")
    while True:
        time.sleep(1)
        print("send slot 1 to 127.0.0.1:5000")
        N1.send(1, "127.0.0.1", 5000)
        print("send slot 2 to 127.0.0.1:5000")
        N1.send(2, "127.0.0.1", 5000)
