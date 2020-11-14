# Copyright 2019 Hideto Manjo.
#
# Licensed under the MIT License

"""Node booting-up module."""

import sys
import time
import logging

from margaret.computer import Computer
from margaret.siobus import BusMaster
from margaret.sioformat import DefaultConnectionEvents

# logging root logger config
logging.basicConfig(level=logging.INFO,
                    format=("%(asctime)-15s %(name)s %(levelname)s:"
                            " %(message)s"))
LOGGER = logging.getLogger(__name__)

class Node:
    """Node booting module."""

    def __init__(self, **options):
        """Init."""

        # options
        self.host = options.get('host', "localhost")
        self.port = options.get('port', 5000)
        self.namespace = options.get('namespace', '/')

        self._chains = {}

        self.computer = None
        self.bus = None

    def __print_config(self):
        """Print node config.

        This method displays the model class name and details.
        Also verify that the model is set correctly.
        """
        compute_model = self.computer_def.get('compute_model', None)
        if compute_model is None:
            return False

        # traning configuration
        sys.stdout.write('\n')
        sys.stdout.write('{:-^40}\n'.format('Node info'))
        sys.stdout.write('node class name: {}\n'
                         .format(self.__class__.__name__))
        sys.stdout.write('{}\n'.format(str(self)))
        sys.stdout.write('{:-^40}\n'.format('Compute model info'))
        sys.stdout.write('model class name: {}\n'
                         .format(compute_model.__class__.__name__))
        sys.stdout.write('{}\n'.format(str(compute_model)))
        sys.stdout.write('{:-^40}\n'.format(''))

        return True

    @staticmethod
    def __countdown_wait(seconds=10):
        """Countdown until server starting up.

        This mechanism is intended to launchs the model
        under incorrect conditions and avoid overwriting trained data.
        """
        for i in reversed(range(seconds)):
            sys.stdout.write('\rServer will boot in {} seconds.'
                             .format((i+1)))
            sys.stdout.flush()
            time.sleep(1)

    def get_chains(self):
        return self._chains

    def _event(self, name, data):
        # exec chain
        for method in self._chains[name][0]:
            data = getattr(self, method)(data)

        work = self._chains[name][1]

        if data is None:
            DefaultConnectionEvents.reject(self.bus, self.namespace)
            return False

        if not self.computer.add_queue(data, work, name):
            DefaultConnectionEvents.reject(self.bus, self.namespace)
            return False

        DefaultConnectionEvents.accept(self.bus, self.namespace)
        return True

    def _responce(self, data, machine_info):
        chain = machine_info["chain"]

        # no responce
        if self._chains[chain][2] is None:
            return True

        responce = self._chains[chain][2][-1]

        # exec chain
        for method in self._chains[chain][2]:
            data = getattr(self, method)(data)

        if data is None:
            return False


        self.bus.emit(responce, data, self.namespace)
        return True

    def on(self, events, work, responces):
        if not isinstance(events, (list, tuple)):
            raise TypeError("events is required list or tuple.")

        if not isinstance(work, str):
            raise TypeError("work is required str.")

        for event in events:
            if not isinstance(event, str):
                TypeError("event name is required str")
            if not callable(getattr(self, event, None)):
                TypeError("event name is not callable")

        if responces is not None:
            if not isinstance(responces, (list, tuple)):
                raise TypeError("responces is required list, tuple.")
            for responce in responces:
                if not isinstance(responce, str):
                    TypeError("responce name is required str")
                if not callable(getattr(self, responce, None)):
                    TypeError("responce name is not callable")

        self._chains[events[0]] = [events, work, responces]

        return True


    def off(self, name):
        if self._chains.pop(name, None) is None:
            return False
        return True

    def boot(self, nowait=False, port=5000):
        """Boot.

        Start the node. It is not recommended to override this method.
        """
        if not self.__print_config():
            raise ValueError("Compute_model or neural network model load failure.")

        # wait
        if nowait is False:
            self.__countdown_wait(10)

        sys.stdout.write("\rStarting socket-DNN server...")
        sys.stdout.flush()

        # Neural computer start
        self.computer = Computer(**self.computer_def)
        self.computer.start()
        self.computer.set_event("writeback", self._responce)

        # comunication bus start
        self.bus = BusMaster(self.host, self.port)
        DefaultConnectionEvents.registration_events(self.bus, self.namespace)
        for chain in self._chains:
            func = lambda sid, data, chain=chain: self._event(chain, data)
            self.bus.on(chain, func, self.namespace)

        self.bus.up()

        sys.stdout.write("\rStarted socket-DNN server.      \n\n")
        sys.stdout.flush()
        LOGGER.info("Node started.")

        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            sys.stdout.write("Node stoped.")
            LOGGER.info("Node ended by KeyboardInterrupt.")
