# Copyright 2019 Hideto Manjo.
#
# Licensed under the MIT License

"""Socket-IO data connection modules."""

import logging
from margaret.core import network

LOGGER = logging.getLogger(__name__)

class Communicator:
    """Communicator.

    Communicator handles data bus.
    """

    def __init__(self, computer, **options):
        """Init."""
        if computer.__class__.__name__ != "Computer":
            raise Exception("computer instance is required")

        self.lisner = None
        self.sender = None

        self.computer = computer

        # encode option
        self.encoder = options.get('encoder', None)
        self.decoder = options.get('decoder', None)
        if self.encoder is not None or self.decoder is not None:
            if not callable(self.encoder):
                raise Exception("encoder is not callable funciton")
            if not callable(self.decoder):
                raise Exception("decoder is not callable function")

        # options
        self.host = options.get('host', "localhost")
        self.port = options.get('port', 5000)
        self.layer = options.get('namespace', '/')

        self.bus = network.BusMaster(self.host, self.port)

    def boot(self):
        """Boot server."""
        self.lisner = Listener(self)
        self.sender = Sender(self)

        # registration send callback
        self.computer.set_event("send", self.sender.answer)

        self.bus.up()


class Listener:
    """Listener.

    listen thread.
    """

    def __init__(self, comm):
        """Init."""
        self.comm = comm
        self.registration_events()


    def postjob_exec(self, sid, job):
        """Postjob_exec.

        Submit job to computer.
        """
        # encode
        if self.comm.encoder is not None:
            job = self.comm.encoder(job)
            if job is None:
                LOGGER.warn("encode fail.")
                return self.comm.sender.reject_job()

        # send queue to computer
        if not self.comm.computer.add_queue(job):
            return self.comm.sender.reject_job()

        return self.comm.sender.accept_job()

    def registration_events(self):
        """Events."""
        # common events
        def connect(sid, _environ):
            message = 'new client connected.({})'.format(sid)
            self.comm.bus.emit('broadcast',
                               {'message': message},
                               self.comm.layer)
            LOGGER.info(message)

        def disconnect(sid):
            message = 'client disconnected.({})'.format(sid)
            self.comm.bus.emit('broadcast',
                               {'message': message},
                               self.comm.layer)
            LOGGER.info(message)

        def postjob(sid, data):
            self.postjob_exec(sid, data)

        def broadcast(sid, data):
            # Broadcast specific emit to all clients
            print("broadcast", data["emitName"])
            self.comm.bus.emit(data["emitName"],
                               {"id": sid, "payload": data["payload"]},
                               self.comm.layer)

        self.comm.bus.on('connect', connect, self.comm.layer)
        self.comm.bus.on('broadcast', broadcast, self.comm.layer)
        self.comm.bus.on('postjob', postjob, self.comm.layer)
        self.comm.bus.on('disconnect', disconnect, self.comm.layer)


class Sender:
    """Sender.

    Sender thread.
    """
    def __init__(self, comm):
        """Init."""
        self.comm = comm

    def answer(self, result):
        """Answer."""

        # decode
        if self.comm.decoder is not None:
            result = self.comm.decoder(result)
            if result is None:
                LOGGER.warn("decode fail.")
                return False

        self.comm.bus.emit('answer', result, self.comm.layer)
        return True

    def reject_job(self):
        """Reject job."""
        self.comm.bus.emit("reject", None, self.comm.layer)
        return False

    def accept_job(self):
        """Reject job."""
        self.comm.bus.emit("accept", None, self.comm.layer)
        return True
