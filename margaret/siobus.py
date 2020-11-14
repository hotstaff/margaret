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
from flask import Flask

LOGGER = logging.getLogger(__name__)

class Master(threading.Thread):
    """Socket-IO Master class."""

    def __init__(self, host="0.0.0.0", port=5000, debug=False):
        """Init."""
        super(Master, self).__init__()
        self.setDaemon(True)
        self.__host = host
        self.__port = port
        self.__debug = debug

        if not self.__debug:
            self._logger_disable()

        self.sio = socketio.Server(async_mode="threading",
                                   logger=self.__debug,
                                   cors_allowed_origins="*")
        self.__app = Flask(__name__)
        self.__app.wsgi_app = socketio.WSGIApp(self.sio,
                                               self.__app.wsgi_app)

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
        os.environ["WERKZEUG_RUN_MAIN"] = "true"
        self.__app.run(threaded=True)


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

    def __init__(self, node_type, host="127.0.0.1", port=5000, debug=False):
        """Init."""
        self.node_type = node_type
        if self.node_type == "master":
            self.__bus = Master(host, port, debug=debug)
        elif self.node_type == "worker":
            self.__bus = Worker(host, port, debug=debug)
        else:
            raise ValueError("Node type must be master or worker.")

        self.sio = self.__bus.sio

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

        self.namespaces = set()
        self._regist_events()

    def _regist_events(self):
        pass

    def append_relay(self, namespace, in_name, out_name=None):
        """Append client to client relay."""
        if out_name is None:
            out_name = in_name

        handler = (lambda sid, data:
                   self.sio.emit(out_name,
                                 data,
                                 namespace=namespace,
                                 skip_sid=sid))

        self.sio.on(in_name, handler, namespace=namespace)
        self.namespaces.add(namespace)

        LOGGER.info("Append relay %s -> %s on %s",
                    in_name, out_name, namespace)

    def remove_relay(self, namespace, in_name):
        """Remove relay."""
        self.sio.on(in_name, None, namespace=namespace)
        LOGGER.info("Remove relay %s on %s", in_name, namespace)

    def on(self, event, handler, namespace):
        """On."""
        self.sio.on(event, handler, namespace=namespace)
        LOGGER.info("Regist event %s on %s.", event, namespace)

    def off(self, event, namespace):
        """Off."""
        self.sio.on(event, None, namespace=namespace)
        LOGGER.info("Unregist event %s on %s.", event, namespace)

    def emit(self, event, data=None, namespace=None):
        """Emit."""
        self.sio.emit(event, data, namespace=namespace)


class BusWorker(Bus):
    """Bus worker node.

    Define a worker node for the data bus.
    Worker nodes are used by connecting to the master node.
    """

    def __init__(self, host="127.0.0.1", port=5000, debug=False):
        """Init."""
        super(BusWorker, self).__init__("worker", host, port, debug=debug)
        self.namespace = None

    def on(self, event, handler, namespace=None):
        """On."""
        if namespace is None:
            namespace = self.namespace

        self.sio.on(event, handler, namespace=namespace)
        LOGGER.info("Regist %s on %s.", event, namespace)
        self.update()

    def off(self, event, namespace=None):
        """Off."""
        if namespace is None:
            namespace = self.namespace

        self.sio.on(event, None, namespace=namespace)
        LOGGER.info("Unregist %s on %s.", event, namespace)
        self.update()

    def set_namespace(self, namespace):
        """Set client namespace."""
        self.namespace = namespace
        self.update()
        LOGGER.info("Append namespace: %s.", self.namespace)

    def emit(self, event, data=None, namespace=None, callback=None):
        """Transmit data to any namespace.

        If namespace is not selected, submit own namespace.
        """
        if namespace is None:
            namespace = self.namespace
        self.sio.emit(event, data, namespace=namespace, callback=callback)


if __name__ == '__main__':
    DATABUS_MASTER = BusMaster()
    DATABUS_MASTER.up()
    input("Press any key to exit.")
