# Copyright 2019 Hideto Manjo.
#
# Licensed under the MIT License

"""Node booting-up module."""

import sys
import time
import logging

from margaret.computer import Computer
from margaret.communicator import Communicator

# logging root logger config
logging.basicConfig(level=logging.INFO,
                    format=("%(asctime)-15s %(name)s %(levelname)s:"
                            " %(message)s"))
LOGGER = logging.getLogger(__name__)

class Node:
    """Node booting module."""

    def __init__(self):
        """Init."""
        super(Node, self).__init__()

        self.computer_def = getattr(self, "computer_def")

        if 'flags' not in self.computer_def:
            self.computer_def['flags'] = {}


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

        # DNC start
        computer = Computer(**self.computer_def)
        computer.start()

        # comunication server start
        comm = Communicator(computer,
                            encoder=getattr(self, "encode", None),
                            decoder=getattr(self, "decode", None),
                            port=port)
        comm.boot()

        sys.stdout.write("\rStarted socket-DNN server.      \n\n")
        sys.stdout.flush()
        LOGGER.info("Node started.")

        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            sys.stdout.write("Node stoped.")
            LOGGER.info("Node ended by KeyboardInterrupt.")
