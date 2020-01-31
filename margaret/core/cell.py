# coding: UTF-8
# Copyright 2017 Hideto Manjo.
#
# Licensed under the MIT License

"""Cell module."""
import threading
from margaret.core.memory import VirtualMemory

class Cell(threading.Thread):
    """Cell.

    The cell provides virtual memory and triggers to the external memory
    interface. Data exchange uses virtual memory. The trigger indicates
    the execution timing of the input / output of the DNN model.
    These two operations can be performed separately, so the cell can pr-
    ocess the data asynchronously.
    """

    def __init__(self, model):
        """Init."""
        super(Cell, self).__init__()
        self.setDaemon(True)

        self.mem_in = VirtualMemory(1)
        self.mem_out = VirtualMemory(1)
        self._trig = threading.Event()
        self._lock = None
        self._exit = False
        self._model = model

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
        self._trig.set()
        if sync:
            self._internal_block()

    def is_ready(self):
        """Return state of trigger's ready."""
        return not self._trig.is_set()

    def stop(self):
        """Stop when the next trigger's in."""
        self._exit = True

    def connect(self, mem, before=False, exact=True):
        """connect.

        Connects two virtual memory objects by exchanging
        the cell input or output memory with the specified one.
        Specify before = True when connecting to the upstream.
        """
        if exact:
            _eq = "is_shape_equal"
        else:
            _eq = "is_slot_equal"

        if before:
            if getattr(self.mem_in, _eq)(mem):
                self.mem_in = mem
                return True
        else:
            if getattr(self.mem_out, _eq)(mem):
                self.mem_out = mem
                return True

        return False

    def run(self):
        """Start."""
        while not self._exit:
            self._trig.wait()
            self.mem_out.write_list(0, self._model(self.mem_in.read_list(0)))
            self._trig.clear()
            self._internal_release()
