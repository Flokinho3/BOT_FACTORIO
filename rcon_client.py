#!/usr/bin/env python3
import socket
import struct

class FactorioRCON:
    def __init__(self, host='localhost', port=27015, password=''):
        self.host = host
        self.port = port
        self.password = password
        self.socket = None
        self.request_id = 0

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))

        # Autentica
        self._send_packet(3, self.password)
        response = self._receive_packet()
        if response is None:
            raise Exception('Nenhuma resposta do servidor RCON durante a autenticação')
        request_id, packet_type, body = response
        if request_id == -1:
            raise Exception('Falha na autenticação RCON')

    def _send_packet(self, packet_type, body):
        self.request_id += 1
        body_bytes = body.encode('utf-8') + b'\x00\x00'
        size = len(body_bytes) + 8
        packet = struct.pack('<i', size)
        packet += struct.pack('<i', self.request_id)
        packet += struct.pack('<i', packet_type)
        packet += body_bytes
        self.socket.sendall(packet)
        return self.request_id

    def _receive_packet(self):
        size_data = self._recv_all(4)
        if not size_data:
            return None
        size = struct.unpack('<i', size_data)[0]
        data = self._recv_all(size)
        if not data or len(data) < 8:
            return None
        request_id = struct.unpack('<i', data[0:4])[0]
        packet_type = struct.unpack('<i', data[4:8])[0]
        # body ends with two null bytes
        body = data[8:-2].decode('utf-8', errors='ignore')
        return (request_id, packet_type, body)

    def _recv_all(self, n):
        data = b''
        while len(data) < n:
            chunk = self.socket.recv(n - len(data))
            if not chunk:
                break
            data += chunk
        return data

    def command(self, cmd):
        self._send_packet(2, cmd)
        resp = self._receive_packet()
        return resp[2] if resp else ''

    def send_monika_message(self, message):
        # Use the mod's command name `/monika_msg` (o mod usa este comando)
        return self.command(f"/monika_msg {message}")

    def close(self):
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
