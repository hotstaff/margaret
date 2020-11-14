# coding: UTF-8
# Copyright 2019 Hideto Manjo.
#
# Licensed under the MIT License

"""Computing modules."""

# common
import sys
import threading
import time
from collections import namedtuple
import logging
import queue

# LOGGER
LOGGER = logging.getLogger(__name__)

# Computer job format
Job = namedtuple('Job', ['chain', 'work', "data"])

class PriorityItem:
    """Priority queue item.

    This is helper class of priority queue.
    """

    def __init__(self, elem_to_wrap, priority):
        """Init."""
        self.job = elem_to_wrap
        self.priority = priority
        self.time = time.time()

    def __lt__(self, other):
        """Comparison order."""
        if self.priority < other.priority:
            return True

        if self.time < other.time:
            return True

        return False


class Computer(threading.Thread):
    """Class Computer.

    init:
        Computer(COMPUTER_DEF)


    COMPUTER_DEF = {
        'compute_model': Oneshot(DeepLSTM(300, 300),
                           optimizers.adam(),
                           loss_func, acc_func)
        'callbacks':{
            'result': callback_func(result)
        }
    }
    """

    def __init__(self, compute_model, callbacks=None):
        """Init."""
        super(Computer, self).__init__()
        self.setDaemon(True)

        # model is required
        self.compute_model = compute_model

        # computer internal variable
        self.__datacnt = 0

        # queue
        self.__q = queue.PriorityQueue()

        # callbacks
        self.callbacks = {}
        if isinstance(callbacks, dict):
            for name in callbacks:
                if not self.set_event(name, callbacks[name]):
                    raise ValueError("registration callback is failed.")

        self._trigger_event("load")


    @staticmethod
    def _handler(func, *args):
        return func(*args)

    def _trigger_event(self, event, *args):
        if event not in self.callbacks:
            return False

        return self._handler(self.callbacks[event], *args)

    def _compute(self, job):
        return getattr(self.compute_model, job.work)(job.data)


    def _print_message(self, process_time, addtext=""):
        iops = 1.0 / process_time
        message = ("\r({0}/{1}) in {2:.2f}s ({3:.2f} IOPS) {4} "
                   .format(self.__datacnt, self.__q.qsize() + self.__datacnt,
                           process_time, iops, addtext))
        sys.stdout.write(message)
        sys.stdout.flush()
        return message

    def _exec_queue(self, job):
        # datacnt copy before process
        self.__datacnt += 1
        datacnt = self.__datacnt

        # compute
        processstart = time.time()
        output = self._compute(job)
        process_time = time.time() - processstart

        # append info
        machine_info = {
            "datacnt": datacnt,
            "process_time": process_time,
            "work": job.work,
            "chain": job.chain,
        }

        # post massage
        self._print_message(process_time)

        if output is None:
            return (None, machine_info)

        # loop event
        if job.work == "loop":
            if output is False:
                return (None, machine_info)

            self.add_queue(job.data, job.work, job.chain, 10)

        return (output, machine_info)

    def _check_job(self, data, work):
        if work is not None:
            if not isinstance(work, str):
                return False

            if work.startswith("_"):
                return False

            if not callable(getattr(self.compute_model, work, None)):
                return False

        return True

    def set_event(self, event, callback, force=False):
        """Set callback event."""
        if not callable(callback):
            return False
        if event in self.callbacks and force is False:
            return False

        self.callbacks[event] = callback

        return True

    def add_queue(self, data, work, chain, priority=3):
        """Add_queue, when check_job() return True."""
        if self._check_job(data, work):
            job = Job(chain, work, data)
            self.__q.put(PriorityItem(job, priority))
            self._trigger_event("accept")
            return True

        self._trigger_event("reject")
        return False


    def run(self):
        """Thread loop."""

        # loop start
        if callable(getattr(self.compute_model, "setup", None)):
            self.add_queue(None, "setup", "setup", priority=1)

        if callable(getattr(self.compute_model, "loop", None)):
            self.add_queue(None, "loop", "loop", priority=2)

        while True:
            next_queue = self.__q.get(block=True).job
            self._trigger_event("fetch", next_queue)
            output, machine_info = self._exec_queue(next_queue)
            if output is not None:
                self._trigger_event("writeback", output, machine_info)
            self.__q.task_done()
