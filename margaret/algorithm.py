# coding: UTF-8
# Copyright 2019 Hideto Manjo.
#
# Licensed under the MIT License

"""Algorithms."""

from collections import deque
import time

class Queueing:
    """Queueing.

    This module is used to calculate latency and turnaround time
     based on queuing theory when processing queues continuously.
    Calling arrival and service will record the time.The required
    parameters can be calculated by calling the respective method.
    """

    def __init__(self, maxlen=10):
        """Init."""
        self._arrivals = deque(maxlen=maxlen)
        self._services = deque(maxlen=maxlen)
        self._last_arrival = time.time()
        self._last_service = time.time()

    @classmethod
    def __mean(cls, time_list):
        return sum(time_list) / len(time_list)

    @classmethod
    def __record(cls, time_list, last_time):
        """Record the lap time and return the current time."""
        now = time.time()
        time_list.append(now - last_time)
        return now

    def clear_history(self):
        """Clear history only."""
        self._arrivals.clear()
        self._services.clear()

    def clear(self):
        """Clear."""
        self.clear_history()
        self._last_arrival = time.time()
        self._last_service = time.time()

    def arrival(self):
        """Record arrival time."""
        self._last_arrival = self.__record(self._arrivals, self._last_arrival)
        return self._arrivals[-1]

    def service(self):
        """Record service time."""
        self._last_service = self.__record(self._services, self._last_service)
        return self._services[-1]

    def average_arrival_time(self):
        """Average arrival time (Ta)."""
        return self.__mean(self._arrivals)

    def average_service_time(self):
        """Average service time (Ts)."""
        return self.__mean(self._services)

    def average_arrival_rate(self):
        """Avarage arrival rate (lambda)."""
        return 1.0 / self.__mean(self._arrivals)

    def average_service_rate(self):
        """Avarage service rate (mu)."""
        return 1.0 / self.__mean(self._services)

    def average_utilization(self):
        """Avarage utilization."""
        return self.average_service_time() / self.average_arrival_time()

    def average_wait(self):
        """Avarage wait."""
        rho = self.average_utilization()
        if rho < 1.0:
            return rho / (1.0 - rho)
        return float('inf')

    def average_wait_time(self):
        """Avarage wait time."""
        return self.average_wait() * self.average_service_time()

    def turnaround_time(self):
        """Turnaround time."""
        return self.average_wait_time() + self.average_service_time()


if __name__ == "__main__":

    import random

    QUEUEING = Queueing()

    #This means the avarage service time fix 0.5.
    QUEUEING.service()
    time.sleep(1)
    QUEUEING.service()

    for i in range(100):
        sleep_time = random.uniform(0, 2)
        time.sleep(sleep_time)
        QUEUEING.arrival()
        print("-----------------------------")
        print("Current arrival", sleep_time, "[sec]")
        print("Ta", QUEUEING.average_arrival_time(), "[sec]")
        print("Ts", QUEUEING.average_service_time(), "[sec]")
        print("Rho", QUEUEING.average_utilization())
        print("Average wait time", QUEUEING.average_wait_time(), "[sec]")
        print("Turnaround time", QUEUEING.turnaround_time(), "[sec]")
