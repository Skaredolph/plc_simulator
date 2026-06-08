from observer import Subject, Observer


class TestObserver(Observer):
    def __init__(self, name: str):
        self.name = name
        self.events = []

    def update(self, event_type: str, data: dict) -> None:
        self.events.append((event_type, data))
        print(f"{self.name} received:", event_type, data)


class BadObserver(Observer):
    def update(self, event_type: str, data: dict) -> None:
        print("BadObserver crashed!")
        raise RuntimeError("fail")


def main():
    subject = Subject()

    obs1 = TestObserver("OBS1")
    obs2 = TestObserver("OBS2")

    print("=== SUBSCRIBE ===")
    subject.subscribe(obs1)
    subject.subscribe(obs2)

    print("Observers:", subject._observers)

    print("\n=== NOTIFY 1 ===")
    subject.notify("temperature", {"value": 42})

    print("OBS1 events:", obs1.events)
    print("OBS2 events:", obs2.events)

    print("\n=== UNSUBSCRIBE OBS1 ===")
    subject.unsubscribe(obs1)

    print("Observers:", subject._observers)

    print("\n=== NOTIFY 2 ===")
    subject.notify("event", {"x": 1})

    print("OBS1 events:", obs1.events)
    print("OBS2 events:", obs2.events)

    print("\n=== BAD OBSERVER TEST ===")
    bad = BadObserver()
    subject.subscribe(bad)

    subject.notify("test", {"a": 100})

    print("OBS2 final events:", obs2.events)


if __name__ == "__main__":
    main()