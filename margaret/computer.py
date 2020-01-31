# coding: UTF-8
# Copyright 2019 Hideto Manjo.
#
# Licensed under the MIT License

"""Computing modules."""

# common
import sys
import threading
import time
import logging

# module compatible
try:
    import queue
except ImportError:
    import Queue as queue

# LOGGER
LOGGER = logging.getLogger(__name__)


class PriorityItem:
    """Priority queue item.

    This is helper class of priority queue.
    """

    def __init__(self, elem_to_wrap, priority):
        """Init."""
        self.data = elem_to_wrap
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
        """_compute."""
        if "call" in job:
            return getattr(self.compute_model, job["call"])(job)
        return self.compute_model(job)


    def _print_message(self, info, process_time, addtext=""):
        loss = info.get("loss", None)
        acc = info.get("acc", None)
        iops = info.get("batch", 1) / process_time
        message = info.get("message", None)
        lossprint = " loss: {0:8}".format(loss) if loss is not None else ""
        accprint = " acc_rate: {0:8}".format(acc) if acc is not None else ""
        messageprint = " {}".format(message) if message is not None else ""

        message = ("\r({0}/{1})"
                   "{2}{3}{4} time: {5:.2f} IOPS: {6:.2f} {7} "
                   .format(self.__datacnt, self.__q.qsize() + self.__datacnt,
                           lossprint, accprint, messageprint,
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

        if output is None:
            self._print_message({}, process_time)
            return {"job_in": job, "job_out": None}

        info = output.get("info", {})

        # post massage
        self._print_message(info, process_time)

        # loop event
        if output.get("loop", False):
            self.add_queue(job.copy(), 10)

        # append info
        machine_info = {
            "datacnt": datacnt,
            "process_time": process_time
        }
        output["info"].update(machine_info)

        return {"job_in": job, "job_out": output}

    def _check_job(self, job):
        if not isinstance(job, dict):
            return False

        if "call" in job:
            if not isinstance(job["call"], str):
                return False

            if job["call"].startswith("_"):
                return False

            if not callable(getattr(self.compute_model, job["call"], None)):
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

    def add_queue(self, job, priority=3):
        """Add_queue, when check_job() return True."""
        if self._check_job(job):
            job["time"] = time.time()
            job["pr"] = priority
            self.__q.put(PriorityItem(job, priority))
            self._trigger_event("accept", job)
            return True

        self._trigger_event("reject", job)
        return False


    def run(self):
        """Thread loop."""
        while True:
            next_queue = self.__q.get(block=True).data
            result = self._exec_queue(next_queue)
            self._trigger_event("result", result)
            if result["job_out"] is not None:
                self._trigger_event("send", result)
            self.__q.task_done()
