# Copyright 2019 Hideto Manjo.
#
# Licensed under the MIT License

"""Socket-IO data connection modules."""

import logging

LOGGER = logging.getLogger(__name__)

class DefaultConnectionEvents:

    def registration_events(bus, namespace):
        """Events."""
        # common events
        def connect(sid, _environ):
            message = 'new client connected.({})'.format(sid)
            bus.emit('broadcast', {'message': message}, namespace)
            LOGGER.info(message)

        def disconnect(sid):
            message = 'client disconnected.({})'.format(sid)
            bus.emit('broadcast', {'message': message}, namespace)
            LOGGER.info(message)

        def broadcast(sid, data):
            # Broadcast specific emit to all clients
            print("broadcast", data["emitName"])
            bus.emit(data["emitName"],
                     {"id": sid, "payload": data["payload"]},
                     namespace)

        bus.on('connect', connect, namespace)
        bus.on('broadcast', broadcast, namespace)
        bus.on('disconnect', disconnect, namespace)

    @staticmethod
    def reject(bus, namespace):
        """Reject job."""
        bus.emit("reject", None, namespace)

    @staticmethod
    def accept(bus, namespace):
        """Reject job."""
        bus.emit("accept", None, namespace)
