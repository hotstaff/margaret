# Copyright 2019 Hideto Manjo.
#
# Licensed under the MIT License

"""Socket-IO network modules.

This module defines bus, which is the base module for data transfer.
The bus consists of socket-IO, and the purpose of this module is to
abstract socket-IO.
"""

import time
import threading
import logging
import os
import socketio
import eventlet

# module compatible with Python 2.7 and Python 3
try:
    import queue
except ImportError:
    import Queue as queue

LOGGER = logging.getLogger(__name__)

class Master(threading.Thread):
    """Socket-IO Master class."""

    def __init__(self, host="0.0.0.0", port=5000, debug=False, thread=False):
        """Init."""
        super(Master, self).__init__()
        self.setDaemon(True)
        self.__host = host
        self.__port = port
        self.__debug = debug

        if not self.__debug:
            self._logger_disable()

        if thread:
            from flask import Flask
            self.sio = socketio.Server(async_mode="threading",
                                       logger=self.__debug,
                                       cors_allowed_origins="*")
            self.__app = Flask(__name__)
            self.__app.wsgi_app = socketio.WSGIApp(self.sio,
                                                   self.__app.wsgi_app)
        else:
            eventlet.monkey_patch()
            self.sio = socketio.Server(async_mode="eventlet",
                                       logger=self.__debug)
            self.__app = socketio.WSGIApp(self.sio)

    @staticmethod
    def _logger_disable():
        """Disable socketio info logging."""
        logging.getLogger('socketio.server').setLevel(logging.ERROR)
        logging.getLogger('engineio.server').setLevel(logging.ERROR)
        logging.getLogger('werkzeug').setLevel(logging.ERROR)

    def update(self):
        """Update."""
        pass

    def change_host(self, host, port):
        """Change host and port."""
        pass

    def run(self):
        """Start server."""
        if self.sio.async_mode == "threading":
            os.environ["WERKZEUG_RUN_MAIN"] = "true"
            self.__app.run(threaded=True)
            return

        eventlet.wsgi.server(
            eventlet.listen((self.__host, self.__port)),
            self.__app,
            log=None,
            log_output=self.__debug)


class Worker:
    """Socket-IO Worker class."""

    def __init__(self, host="127.0.0.1", port=5000, debug=False):
        """Init."""
        self.__host = host
        self.__port = port
        self.__debug = debug
        self.__start = False

        if not self.__debug:
            self._logger_disable()

        self.sio = socketio.Client(logger=self.__debug, binary=True)

    @staticmethod
    def _logger_disable():
        """Disable socketio info logging."""
        logging.getLogger('socketio.client').setLevel(logging.ERROR)
        logging.getLogger('engineio.client').setLevel(logging.ERROR)

    def update(self):
        """Update connection."""
        if self.__start:
            if self.sio.eio.state != "disconnected":
                self.sio.disconnect()
            self.sio.connect('http://{0}:{1}'.format(self.__host, self.__port))
            LOGGER.info("Connection is updated.")

    def change_host(self, host, port):
        """Change master."""
        self.__host = host
        self.__port = port
        self.update()

    def start(self):
        """Start connection."""
        self.sio.connect('http://{0}:{1}'.format(self.__host, self.__port))
        self.sio.start_background_task(self.sio.wait)
        self.__start = True



class Bus:
    """A Bus base module.

    This class implements virtual data transport module using socketio.
    Common methods for "Master" and "Worker" are written.

    :param node_type: Set the data bus node type. Possible values ​​are
                      "master" and "worker". One “master” is a required
                      node on the network, and any number of “workers”
                      can be installed on the network. “Workers” exchange
                      data via “Master”. This value is a required.

    :param host: The host name.
    :param port: The port number.

    """

    def __init__(self, node_type, host="127.0.0.1", port=5000, start=False,
                 debug=False):
        """Init."""
        self.node_type = node_type
        if self.node_type == "master":
            self.__bus = Master(host, port, debug=debug)
        elif self.node_type == "worker":
            self.__bus = Worker(host, port, debug=debug)
        else:
            raise ValueError("Node type must be master or worker.")

        self.sio = self.__bus.sio

        if start:
            self.up()

    def _ready_wait(self):
        """Wait for the connection."""
        LOGGER.info("Stand-by for commencement of life cycle.")
        if self.node_type == "worker":
            while self.sio.eio.state != "connected":
                time.sleep(0.05)
        else:
            time.sleep(2)

    def update(self):
        """Update connection."""
        self.__bus.update()

    def up(self):
        """Activate bus."""
        self.__bus.start()
        self._ready_wait()
        LOGGER.info("Commencing(%s)", self.node_type)

    def down(self):
        """Deactivate bus."""
        pass

class BusMaster(Bus):
    """Bus master node.

    Define the master node for the data bus.
    The master node mediates worker communication.
    """

    def __init__(self, host="127.0.0.1", port=5000, debug=False):
        """Init."""
        super(BusMaster, self).__init__("master", host, port, debug=debug)

        self.layers = set()
        self._regist_events()

    def _regist_events(self):
        pass

    def append_relay(self, layer_name, in_name, out_name=None):
        """Append client to client relay."""
        if out_name is None:
            out_name = in_name

        handler = (lambda sid, data:
                   self.sio.emit(out_name,
                                 data,
                                 namespace=layer_name,
                                 skip_sid=sid))

        self.sio.on(in_name, handler, namespace=layer_name)
        self.layers.add(layer_name)

        LOGGER.info("Append relay %s -> %s on %s",
                    in_name, out_name, layer_name)

    def remove_relay(self, layer_name, in_name):
        """Remove relay."""
        self.sio.on(in_name, None, namespace=layer_name)
        LOGGER.info("Remove relay %s on %s", in_name, layer_name)

    def on(self, event, handler, layer_name):
        """On."""
        self.sio.on(event, handler, namespace=layer_name)
        LOGGER.info("Regist event %s on %s.", event, layer_name)

    def off(self, event, layer_name):
        """Off."""
        self.sio.on(event, None, namespace=layer_name)
        LOGGER.info("Unregist event %s on %s.", event, layer_name)

    def emit(self, event, data=None, layer_name=None):
        """Emit."""
        self.sio.emit(event, data, namespace=layer_name)


class BusWorker(Bus):
    """Bus worker node.

    Define a worker node for the data bus.
    Worker nodes are used by connecting to the master node.
    """

    def __init__(self, host="127.0.0.1", port=5000, debug=False):
        """Init."""
        super(BusWorker, self).__init__("worker", host, port, debug=debug)
        self.layer = None

    def on(self, event, handler, layer_name=None):
        """On."""
        if layer_name is None:
            layer_name = self.layer

        self.sio.on(event, handler, namespace=layer_name)
        LOGGER.info("Regist %s on %s.", event, layer_name)
        self.update()

    def off(self, event, layer_name=None):
        """Off."""
        if layer_name is None:
            layer_name = self.layer

        self.sio.on(event, None, namespace=layer_name)
        LOGGER.info("Unregist %s on %s.", event, layer_name)
        self.update()

    def set_layer(self, name):
        """Set client layer."""
        self.layer = name
        self.update()
        LOGGER.info("Append layer: %s.", self.layer)

    def emit(self, event, data=None, layer_name=None, callback=None):
        """Transmit data to any layer.

        If layer_name is not selected, submit own layer.
        """
        if layer_name is None:
            layer_name = self.layer
        self.sio.emit(event, data, namespace=layer_name, callback=callback)


if __name__ == '__main__':
    DATABUS_MASTER = BusMaster()
    input("Press any key to exit.")
