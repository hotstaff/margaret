# coding: UTF-8

# Copyright 2017 Hideto Manjo.
# Licensed under the MIT License

"""Socket-IO data connection modules for client."""

import logging
import time
from threading import BoundedSemaphore
import socketio
from margaret.core import network


LOGGER = logging.getLogger(__name__)

class Client:
    """Client.

    Client is the source class of listener and sender
    """

    def __init__(self, **options):
        """Init."""
        # options
        self.host = options.get('host', "localhost")
        self.port = options.get('port', 5000)
        self.layer = options.get('namespace', '/')
        self.bus = network.BusWorker(self.host, self.port)
        self.bus.set_layer(self.layer)
        self.buffer = options.get('buffer', 5)
        self._semaphore = BoundedSemaphore(self.buffer)
        self.on_default()

    def _semaphore_all_release(self):
        while self._semaphore._value < self.buffer:
            self._semaphore.release()

    def _semaphore_set(self):
        self._semaphore_all_release()
        self._semaphore = BoundedSemaphore(self.buffer)

    def change_buffer(self, buf):
        """Change buffer size."""
        if isinstance(buf, int):
            self.buffer = buf
            self._semaphore_set()
            return True
        return False

    def on_default(self):
        """On default events."""
        def on_connect():
            """On_connect."""
            self._semaphore_all_release()
            LOGGER.info("connect.")

        def on_disconnect():
            """On_disconnect."""
            LOGGER.info("disconnect.")

        def on_broadcast(*args):
            """On broadcast."""
            print("[Server]", args[0]["message"])

        self.on("connect", on_connect)
        self.on("disconnect", on_disconnect)
        self.on("broadcast", on_broadcast)

    def dec_sync_count_down(self, func):
        """Dec_sync_regist."""
        def new_func(*args, **kwargs):
            try:
                self._semaphore.release()
            except ValueError:
                LOGGER.warn("semaphore release exceeds acquire.")
            return func(*args, **kwargs)
        return new_func

    def on(self, name, callback):
        """On."""
        self.bus.on(name, callback)

    def emit(self, event, data=None, layer_name=None):
        """Emit."""
        self.bus.emit(event, data, layer_name=layer_name)

    def on_sync(self, name, callback):
        """On sync.

        Register events in synchro transmission mode.
        """
        self.bus.on(name, self.dec_sync_count_down(callback))

    def emit_sync(self, event, data=None, layer_name=None):
        """Emit sync.

        Emits in synchro transmission mode. Wait for
        transmission until the semaphore is released.
        The number of simultaneous transmissions can
        be set with self.buffer.
        """
        self._semaphore.acquire()
        self.bus.emit(event,
                      data,
                      layer_name=layer_name)

    def boot(self):
        """Boot."""
        while True:
            try:
                self.bus.up()
                break
            except socketio.exceptions.ConnectionError:
                LOGGER.error("Connection error")
                time.sleep(1)

        LOGGER.info('Client started.')
