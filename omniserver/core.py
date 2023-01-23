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
omniserver.core:
    - Main module functions for initializing client and server objects

TODO:
    - 
"""
from omniserver import servers, clients


""" Server Initialization Functions
"""

def tcp_server(port=0, ip='', *, RequestHandler=servers.TCPHandler, ServerHandler=servers.TCPServer, sslcontext=None):
    """Initialize TCPServer and return its manager object
    
    :param port: Port to listen on (Default: random high port)
    :type port: int
    :param ip: IP address to accept connections with (Default: 0.0.0.0)
    :type ip: str
    :param RequestHandler: servers.TCPHandler class or subclass to process requests with
    :param ServerHandler: servers.TCPServer class or subclass to handle server socket
    :param sslcontext: SSLContext to wrap socket with
    :type context: ssl.SSLContext

    :returns ServerManager: ServerManager object wrapped around TCPServer
    """        
    server = servers.ServerManager(ServerHandler((ip, port), RequestHandler))    
    if sslcontext:
        server.enable_ssl(context)
    return server


def udp_server(port=0, ip='', *, RequestHandler=servers.UDPHandler, ServerHandler=servers.UDPServer):
    """Initialize UDPServer and return its manager object
    
    :param port: Port to listen on (Default: random high port)
    :type port: int
    :param ip: IP address to accept connections with (Default: 0.0.0.0)
    :type ip: str
    :param RequestHandler: servers.UDPHandler class or subclass to process requests with
    :param ServerHandler: servers.UDPServer class or subclass to handle server socket
    
    :returns ServerManager: ServerManager object wrapped around UDPServer
    """
    return servers.ServerManager(ServerHandler((ip, port), RequestHandler))


def dns_tcp_server(port=53, ip='', *, RequestHandler=servers.DNSHandlerTCP, ServerHandler=servers.DNSServerTCP, default_ip=None, record=None, zonefile=None, sslcontext=None):
    """Initialize DNSServerTCP and return its manager object
    
    :param port: Port to listen on (Default: 53)
    :type port: int
    :param ip: IP address to accept connections with (Default: 0.0.0.0)
    :type ip: str
    :param RequestHandler: servers.DNSHandlerTCP class or subclass to process requests with
    :param ServerHandler: servers.DNSServerTCP class or subclass to handle server socket
    :param default_ip: Default IP address to answer DNS queries with, if not resolved by other means
    :type default_ip: str
    :param record: Zone-style DNS record to compare queries against
    :type record: str
    :param zonefile: Zone file of DNS records to populate server's records with
    :type zonefile: str
    :param sslcontext: SSLContext to wrap socket with
    :type sslcontext: ssl.SSLContext
    
    :returns ServerManager: ServerManager object wrapped around DNSServerTCP
    """        
    server = servers.ServerManager(ServerHandler((ip, port), RequestHandler, default_ip=default_ip))
    if zonefile:
        server.add_zonefile(zonefile)
    if record:
        server.add_record(record)
    if sslcontext:
        server.enable_ssl(context)
    return server


def dns_server(port=53, ip='', *, RequestHandler=servers.DNSHandler, ServerHandler=servers.DNSServer, default_ip=None, record=None, zonefile=None):
    """Initialize DNSServerTCP and return its manager object
    
    :param port: Port to listen on (Default: 53)
    :type port: int
    :param ip: IP address to accept connections with (Default: 0.0.0.0)
    :type ip: str
    :param RequestHandler: servers.DNSHandler class or subclass to process requests with
    :param ServerHandler: servers.DNSServer class or subclass to handle server socket
    :param default_ip: Default IP address to answer DNS queries with, if not resolved by other means
    :type default_ip: str
    :param record: Zone-style DNS record to compare queries against
    :type record: str
    :param zonefile: Zone file of DNS records to populate server's records with
    :type zonefile: str
        
    :returns ServerManager: ServerManager object wrapped around DNSServer
    """        
    server = servers.ServerManager(ServerHandler((ip, port), RequestHandler, default_ip=default_ip))
    if zonefile:
        server.add_zonefile(zonefile)
    if record:
        server.add_record(record)
    return server    
 
 
def http_server(port=8080, ip='', *, RequestHandler=servers.HTTPHandler, ServerHandler=servers.HTTPServer, dir=None, sslcontext=None):
    """Initialize HTTPServer and return its manager object
    
    :param port: Port to listen on (Default: 8080)
    :type port: int
    :param ip: IP address to accept connections with (Default: 0.0.0.0)
    :type ip: str
    :param RequestHandler: servers.HTTPHandler class or subclass to process requests with
    :param ServerHandler: servers.HTTPServer class or subclass to handle server socket
    :param dir: Server's working directory (Default: CWD)
    :type dir: str
    :param sslcontext: SSLContext to wrap socket with
    :type context: ssl.SSLContext    
    :returns ServerManager: ServerManager object wrapped around HTTPHandler
    """
    server = servers.ServerManager(ServerHandler((ip, port), RequestHandler, dir))
    if sslcontext:
        server.enable_ssl(context)
    return server   



"""Client Initialization Functions
"""

def tcp_client(remote_addr: tuple, *, Handler=clients.TCPClient, sslcontext=None, hostname=None):
    """Initialize and return clients.TCPClient object
    
    :param remote_addr: IP address (or hostname) and port of remote socket
    :type remote_addr: tuple
    :param Handler: clients.TCPClient class or subclass to handle data exchange
    :type Handler: clients.TCPClient
    :param sslcontext: SSLContext to wrap socket with (If None, create context using **kwargs)
    :type sslcontext: ssl.SSLContext
    :param hostname: Hostname of remote server (Required for SSL, unless hostname defined in remote_addr)
    :type hostname: str       
    :returns TCPClient: Client object for exchanging data with remote TCP server
    """
    client = Handler(remote_addr)
    if sslcontext:
        client.enable_ssl(sslcontext, hostname)
    return client


def udp_client(remote_addr, *, Handler=clients.UDPClient):
    """Initialize and return clients.UDPClient object
    
    :param remote_addr: IP address (or hostname) and port of remote socket
    :type remote_addr: tuple
    :param Handler: clients.UDPClient class or subclass to handle data exchange
    :type Handler: clients.UDPClient    
    :returns UDPClient: Client object for exchanging data with remote UDP server
    """
    return Handler(remote_addr)


def dns_client(remote_addr, *, Handler=clients.DNSClient):
    """Initialize and return clients.DNSClient object (UDP)
    
    :param remote_addr: IP address (or hostname) and port of remote socket
    :type remote_addr: tuple
    :param Handler: clients.DNSClient class or subclass to handle data exchange
    :type Handler: clients.DNSClient   
    :returns DNSClient: Client object for sending queries to remote DNS server (UDP)
    """
    return Handler(remote_addr)


def dns_tcp_client(remote_addr, *, Handler=clients.DNSClientTCP, sslcontext=None):
    """Initialize and return clients.DNSClientTCP object (TCP)
    
    :param remote_addr: IP address (or hostname) and port of remote socket
    :type remote_addr: tuple
    :param Handler: clients.DNSClientTCP class or subclass to handle data exchange
    :type Handler: clients.DNSClientTCP
    :param sslcontext: SSLContext to wrap socket with (If None, create context using **kwargs)
    :type sslcontext: ssl.SSLContext    
    :returns DNSClientTCP: Client object for sending queries to remote DNS server (TCP)
    """
    client = Handler(remote_addr)
    if sslcontext:
        client.enable_ssl(sslcontext, hostname)
    return client


def http_client(remote_addr, *, Handler=clients.HTTPClient, dir=None, sslcontext=None, hostname=None):
    """Initialize and return clients.HTTPClient object
    
    :param remote_addr: IP address (or hostname) and port of remote socket
    :type remote_addr: tuple
    :param Handler: clients.HTTPClient class or subclass to handle data exchange
    :type Handler: clients.HTTPClient
    :param dir: Working directory (Default: CWD)
    :type dir: str
    :param sslcontext: SSLContext to wrap socket with (If None, create context using **kwargs)
    :type sslcontext: ssl.SSLContext
    :param hostname: Hostname of remote server (Required for SSL, unless hostname defined in remote_addr)
    :type hostname: str
    :returns HTTPClient: Client object for exchanging data with remote web server (via GET and POST requests)
    """
    client = Handler(remote_addr, dir)
    if sslcontext:
        client.enable_ssl(context, hostname)
    return client









    


