from unittest import TestCase, main

from Rammbock.networking import TCPServer

LOCAL_IP = '127.0.0.1'

ports = {'SERVER_PORT': 8008}


class _NetworkingTests(TestCase):

    def setUp(self):
        self.sockets = []
        for key in ports:
            ports[key] += 1

    def tearDown(self):
        for sock in self.sockets:
            sock.close()
        return TestCase.tearDown(self)

    def _assert_receive(self, receiver, msg):
        print(msg)
        self.assertEqual(receiver.receive(), msg)

    def _tcp_server(self, server_port, timeout=20):
        server = TCPServer(LOCAL_IP, server_port, timeout=timeout)
        self.sockets.append(server)
        return server


class TestNetworking(_NetworkingTests):

    def test_server_send_tcp(self):
        server = self._tcp_server(ports['SERVER_PORT'])
        server.accept_connection()
        msg = server.receive_from(timeout=20)
        print(msg)


if __name__ == "__main__":
    main()
