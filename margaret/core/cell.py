# coding: UTF-8
# Copyright 2017 Hideto Manjo.
#
# Licensed under the MIT License

"""Cell module."""
import threading
from margaret.core.memory import VirtualMemory
from margaret.core.netvm import NetVM

class Cell(threading.Thread):
    """Cell.

    The cell provides virtual memory and triggers to the external memory
    interface. Data exchange uses virtual memory. The trigger indicates
    the execution timing of the input / output of the DNN model.
    These two operations can be performed separately, so the cell can pr
    ocess the data asynchronously.
    """

    def __init__(self, model):
        """Init."""
        super(Cell, self).__init__()
        self.setDaemon(True)

        self.source = VirtualMemory(1)
        self.drain = VirtualMemory(1)
        self._gate = threading.Event()
        self._lock = None
        self._exit = False
        self._model = model
        self._fetch = None
        self._writeback = None
        self._send = None

    def _internal_block(self):
        if self._lock is None:
            self._lock = threading.Lock()
            self._lock.acquire(blocking=False)
            self._lock.acquire(blocking=True)

    def _internal_release(self):
        if self._lock is not None:
            self._lock.release()
            self._lock = None

    def trigger(self, sync=False):
        """Trigger cell."""
        self._gate.set()
        if sync:
            self._internal_block()

    def is_ready(self):
        """Return state of trigger's ready."""
        return not self._gate.is_set()

    def stop(self):
        """Stop when the next trigger's in."""
        self._exit = True
        self.trigger()

    def connect(self, mem, before=False):
        """connect.

        Connects two virtual memory objects by exchanging
        the cell input or output memory with the specified one.
        Specify before = True when connecting to the upstream.
        """
        if not self.source.is_shape_equal(mem):
            return False

        if before:
            self.source = mem
        else:
            self.drain = mem
        return True

    def set_func(self, name, callback):
        """Set a callback event in the cell.
        The callback event names that can be set are "fetch" and "writeback".
        """
        if callable(callback):
            if name == "fetch":
                self._fetch = callback
                return True
            elif name == "writeback":
                self._writeback = callback
                return True

        return False

    def set_source_to_net(self, host='', port=5000):
        """Source to NetVM"""
        source = self.source.read(0)
        self.source = NetVM(1, host, port)
        self.source.write(0, source, force=True)
        self.source.listen()

    def set_drain_to_net(self, rhost, rport, src_port=3000):
        """Drain to NetVM"""
        drain = self.drain.read(0)
        self.drain = NetVM(1)
        self.drain.write(0, drain, force=True)
        self._send = lambda: self.drain.send(0, rhost, rport, src_port)

    def run(self):
        """Start."""
        while not self._exit:
            self._gate.wait()

            fetch = self.source.read(0)
            if self._fetch is not None:
                fetch = self._fetch(fetch)

            excute = self._model(fetch)

            if self._writeback is not None:
                writeback = self._writeback(excute)

            self.drain.write(0, writeback)

            if self._send is not None:
                self._send()

            self._gate.clear()
            self._internal_release()
