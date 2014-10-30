from unittest import TestCase, main
from websocket_handlers import MessageHandler


class TestMessageHandler(TestCase):
    def test___init__(self):
        raise NotImplementedError()

    def test_get_current_user(self):
        raise NotImplementedError()

    def test_on_message(self):
        raise NotImplementedError()

    def test_listen(self):
        raise NotImplementedError()

    def test_callback(self):
        raise NotImplementedError()

    def test_on_close(self):
        raise NotImplementedError()


if __name__ == "__main__":
    main()
