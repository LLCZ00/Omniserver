#
# Copyright (C) 2023 LLCZ00
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.  
#
"""
omniserver.clients:
    - Classes for client objects

Main inheritable classes:
    TCPClient
    UDPClient
    DNSClient
    DNSClientTCP
    HTTPClient
    
TODO:
"""   
import socket
import http.client
import logging
import struct
import os
from time import sleep
from dnslib import DNSRecord

from omniserver import certs

__all__ = ["TCPClient", "UDPClient", "DNSClientTCP", 
            "DNSClient", "HTTPClient"]


"""ClientHandler classes
- Inherited by ClientHandler subclasses in omniserver.clients to provide overridable data handling methods
"""

class BaseClientHandler:
    """Base class for TCP and UDP Client subclasses

    Contains overridable methods for finer control over socket, data, and client actions.
    Subclasses must override send() and recv() with their specific implimentations.
    The send/recv and send_data/recv_data methods are seperated so as to easily 
    allow for bypassing the incoming/outgoing filter methods, if necessary
    """
    def __init__(self, remote_addr: tuple, socket=None):
        self.remote_addr = remote_addr
        self.sock = socket     
        if self.sock is None:
            self.sock_setup()
            
    def __enter__(self):
        return self
        
    def __exit__(self, type, val, traceback):
        try:
            self.close()
        except:
            pass
            
    def sock_setup(self):
        """Overridable method to initialize protocol-specific socket
        
        Required
        """
        raise NotImplementedError
            
    def incoming(self, data):
        """Process incoming data as it's recieved from self.recv()
        """
        try:
            data = data.decode()
        except:
            pass
        return data.strip()
        
    def outgoing(self, resp):
        """Process outgoing response/data before it's sent via self.send()
        """
        if type(resp) is not bytes:
            resp = f"{resp}\n".encode("utf-8")
        return resp
        
    def close(self):
        try:
            if self.sock:
                self.sock.close()
        except:
            pass
 

"""Public ClientHandler subclasses
"""
class TCPClient(BaseClientHandler):
    """Handler class for TCP client objects
    
    Used for exchanging data with remote TCP socket.
    TLS/SSL compatible.
    """
    def sock_setup(self):
        """Initialize TCP socket and 'connected flag'
        """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.connected = False
        
    def __enter__(self):
        self.connect()
        return self
        
    def recv(self, buffer=1024):
        """Protocol specific method for recieving data from remote socket
        
        :param buffer: Size of recieve buffer
        :type buffer: int
        :returns data: Data recieved, after being processed through self.incoming()
        """
        if not self.connected:
            raise Exception("Not connected to remote server")
        data = self.incoming(self.sock.recv(buffer))
        logging.info(f"[{self.remote_addr[0]}:{self.remote_addr[1]}] Data recieved: {data}")
        return data
        
    def send(self, data):
        """Protocol specific method for sending data to remote socket
        
        :param data: Data to be sent to remote socket, after it's been passed through self.outgoing()
        """
        if not self.connected:
            raise Exception("Not connected to remote server")
        self.sock.sendall(self.outgoing(data))
        logging.info(f"[{self.remote_addr[0]}:{self.remote_addr[1]}] Data sent.")
        
    def connect(self):
        """Attempt to connect to remote address
        
        :rtype: bool
        """
        if self.connected:
            return True
        try:
            self.sock.connect(self.remote_addr)
        except:
            logging.error(f"[{self.remote_addr[0]}:{self.remote_addr[1]}] Failed to establish TCP connection.")
            return False
        else:
            logging.info(f"[{self.remote_addr[0]}:{self.remote_addr[1]}] TCP connection established.")
            self.connected = True
            return True
        
    def enable_ssl(self, context=None, server_hostname=None):
        """Enable TLS/SSL on client socket
        
        :param context: SSLContext to wrap socket with
        :type context: SSLContext
        :param server_hostname: Hostname of remote server
        :type server_hostname: str
        
        :rtype: bool
        """
        if context is None:
            context = certs.create_client_context() # default context
        if server_hostname is None:
            server_hostname = self.remote_addr[0]
        try:
            self.sock = context.wrap_socket(self.sock, server_side=False, server_hostname=server_hostname)
        except Exception as e:
            logging.exception("TLS/SSL failed.")
            raise e    
        return True
            
    def beacon(self, freq=5, tries=0, timeout=None):
        """Periodically attempt to connect to remote socket
        
        :param freq: Frequency, in seconds, to attempt connection
        :type freq: float
        :param tries: Total number of connection attempts before returning False (0=infinity)
        :type param: int
        :param timeout: Set socket timeout time, in seconds
        
        :rtype: bool
        """
        self.sock.settimeout(timeout)
        attempt = 1
        while attempt != tries:
            if self.connect():
                return True
            attempt += 1
            sleep(freq)
        return False
        
    def close(self):
        """Shutdown and close socket
        """
        try:
            if self.sock:
                self.sock.shutdown(1)
                self.sock.close()
                self.connected = False
        except:
            pass


class UDPClient(BaseClientHandler):
    """Handler class for UDP client objects
    
    Used to exchange data with remote UDP server.
    """
    def sock_setup(self):
        """initialize UDP socket
        """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
    def recv(self, buffer=1024):
        """Protocol specific method for recieving data from remote socket
        
        :param buffer: Size of recieve buffer
        :type buffer: int
        :returns data: Data recieved, after being processed through self.incoming()
        """
        try:
            data = self.incoming(self.sock.recv(buffer))
        except:
            logging.error("Unable to reach remote server")
            return None
        logging.info(f"[{self.remote_addr[0]}:{self.remote_addr[1]}] UDP data recieved: {data}")
        return data
        
    def send(self, data):
        """Protocol specific method for sending data to remote socket
        
        Sends data after it's been passed through self.outgoing()
        
        :param data: Data to be sent to remote socket
        """
        self.sock.sendto(self.outgoing(data), self.remote_addr)
        logging.info(f"[{self.remote_addr[0]}:{self.remote_addr[1]}] Data sent.")
        
    def beacon(self, msg="Beacon message", freq=5, tries=0, timeout=None):
        """Periodically attempt to connect to remote socket
        
        Returns True upon recieving UDP data back from remote socket.
        
        :param msg: Default data/message to send to remote socket
        :type msg: str
        :param freq: Frequency, in seconds, to attempt connection
        :type freq: float
        :param tries: Total number of connection attempts before returning False (0=infinity)
        :type param: int
        :param timeout: Set socket timeout time, in seconds
        
        :rtype: bool
        """
        self.sock.settimeout(timeout)
        attempt = 1
        while attempt != tries:
            self.send(msg)
            if self.recv():
                return True
            attempt += 1
            sleep(freq)
        return False


class DNSClientMixIn:
    """MixIn class to extend UDPClient or TCPClient with DNS-specific methods
    
    Overrides incoming() and outgoing() methods, adds query() method
    """
    def incoming(self, data):
        """
        Process incoming data as it's recieved from remote server
        """
        try:
            response = str(DNSRecord.parse(data.strip()).get_a().rdata)
        except:
            raise Exception("Error parsing DNS response")
        return response
        
    def outgoing(self, query):
        """
        Process outgoing response/data before it's sent to remote server
        """
        if type(query) is not bytearray:
            try:
                query = query.pack()
            except:
                raise Exception("Error packing DNS query")
        return query
        
    def query(self, domain, record_type="A"):
        """Send given query to remote server
        
        :param domain: Domain name to query
        :type domain: str
        :param record_type: Record type to query for
        :type record_type: str
        
        :returns answer: IP address returned from DNS server
        :rtype: str
        """
        query = DNSRecord.question(domain, qtype=record_type)
        self.send(query)
        return self.recv()
        
        
class DNSClientTCP(DNSClientMixIn, TCPClient):
    """
    Handler Class for DNS client objects (TCP)
    
    Overrides serveral BaseClientHandler methods to provide DNS-specific 
    functionality by inheriting DNSClientMixIn.
    Inherits socket-specific functionality from TCPClient
    """
    def recv(self, buffer: int = 8192):
        """
        Main method to be used for recieving data
        - Returns data from recv(), after being passed through incoming()
        """
        if not self.connected:
            raise Exception("Not connected to remote server")
        data = self.sock.recv(buffer).strip()
        sz = struct.unpack('>H', data[:2])[0]
        if sz < len(data) - 2:
            raise Exception("Wrong size of TCP packet")
        elif sz > len(data) - 2:
            raise Exception("Too big TCP packet")
        response = self.incoming(data[2:])
        logging.info(f"[{self.remote_addr[0]}:{self.remote_addr[1]}] DNS response:")
        
    def send(self, resp):
        """
        Main method to be used for sending data
        - Sends data after it's passed through outgoing()
        """
        if not self.connected:
            raise Exception("Not connected to remote server")
        data = self.outgoing(resp)
        sz = struct.pack('>H', len(data))
        self.sock.sendall(sz + data)
        logging.info(f"[{self.remote_addr[0]}:{self.remote_addr[1]}] DNS query sent.")


class DNSClient(DNSClientMixIn, UDPClient):
    """
    Handler Class for DNS client objects (UDP)
    
    Overrides serveral BaseClientHandler methods to provide DNS-specific 
    functionality by inheriting DNSClientMixIn.
    Inherits socket-specific functionality from UDPClient
    """
    pass


class HTTPClient(http.client.HTTPConnection):
    """Handler Class for HTTP client objects
    
    Used for issuing requests to remote HTTP/S server.
    Subclass of http.client.HTTPConnection
    """
    proto = "HTTP"
    def __init__(self, remote_addr, dir=None):
        super().__init__(host=remote_addr[0], port=remote_addr[1], timeout=socket._GLOBAL_DEFAULT_TIMEOUT, source_address=None, blocksize=8192)
        self.dir = dir if dir else os.getcwd()
        self.tls = False
        self.context = None
        self.hostname = None
        
    def __enter__(self):
        self.connect()
        return self
        
    def __exit__(self, type, val, traceback):
        pass # HTTPConnection closes automatically anyway
        
    def __str__(self):
        return f"[{self.host}:{self.port}] {self.proto}"
        
    def incoming(self, url, response):
        """Process response data recieved from get()
        
        Default: Write data to file
        """
        if response.getcode() == 200:
            with open(os.path.join(self.dir, os.path.basename(url)), "wb") as file:
                file.write(response.read())
        
    def get(self, url, body=None, headers={}, *, encode_chunked=False):
        """Send GET request to remote server
        
        :param url: URL of resource to request
        :type url: str
        :param body: Data to be sent after headers are finished
        :param headers: HTTP headers
        :type headers: dict
        :param encode_chunked: Chunk-encode body
        :type encode_chunked: bool
        """
        self._send_request("GET", url, body, headers, encode_chunked) # http.client.HTTPConnection
        resp = self.getresponse()
        logging.info(f"{self} request: 'GET {url}' -> {resp.getcode()}")
        self.incoming(url, resp)
        return resp.getcode()
        
    def post(self, url, body=None, headers={}, *, encode_chunked=False):
        """Send POST request to remote server
        
        :param url: URL of resource to request
        :type url: str
        :param body: Data to be sent after headers are finished
        :param headers: HTTP headers
        :type headers: dict
        :param encode_chunked: Chunk-encode body
        :type encode_chunked: bool
        """
        self._send_request("POST", url, body, headers, encode_chunked) # http.client.HTTPConnection
        resp = self.getresponse()
        logging.info(f"{self} request: 'POST {url}' -> {resp.getcode()}")
        return resp.getcode()
        
    def connect(self):
        """Establish connection to remote server
        """
        if self.sock is None:
            super().connect()
            if self.tls:
                self.enable_ssl()    

    def enable_ssl(self, context=None, server_hostname=None):
        """Enable TLS/SSL on client socket
        
        :param context: SSLContext to wrap socket with
        :type context: SSLContext
        :param server_hostname: Hostname of remote server
        :type server_hostname: str
        
        :rtype: bool
        """
        self.tls = True
        if context is None:
            if self.context is None:
                context = certs.create_client_context() # Default context
            else:
                context = self.context
            
        if server_hostname:
            self.hostname = server_hostname
        elif self.hostname is None:
            self.hostname = self.host
            
        if self._http_vsn == 11:
            context.set_alpn_protocols(['http/1.1'])
        if context.post_handshake_auth is not None:
            context.post_handshake_auth = True
            
        if self.sock is None: # Assign self.context and return if socket hasn't been declared yet
            self.context = context
            return False

        try:
            self.sock = context.wrap_socket(self.sock, server_side=False, server_hostname=self.hostname)
        except Exception as e:
            logging.exception("TLS/SSL failed.")
            raise e
        
        self.context = context
        self.proto = "HTTPS"
        return True
    
    
