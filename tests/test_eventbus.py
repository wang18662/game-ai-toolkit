from gameai.core.eventbus import EventBus


class Ping:
    def __init__(self, n: int) -> None:
        self.n = n


def test_publish_delivers_to_subscribers():
    bus = EventBus()
    received: list = []
    bus.subscribe(Ping, lambda e: received.append(e))
    bus.publish(Ping(1))
    bus.publish(Ping(2))
    assert [e.n for e in received] == [1, 2]


def test_unsubscribe_stops_delivery():
    bus = EventBus()
    received: list = []
    handler = lambda e: received.append(e)
    bus.subscribe(Ping, handler)
    bus.publish(Ping(1))
    bus.unsubscribe(Ping, handler)
    bus.publish(Ping(2))
    assert [e.n for e in received] == [1]


def test_subscribers_are_type_scoped():
    bus = EventBus()
    hits = {"ping": 0, "other": 0}

    class Other:
        pass

    bus.subscribe(Ping, lambda e: hits.__setitem__("ping", hits["ping"] + 1))
    bus.subscribe(Other, lambda e: hits.__setitem__("other", hits["other"] + 1))
    bus.publish(Ping(0))
    assert hits == {"ping": 1, "other": 0}
