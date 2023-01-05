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
from omniserver import servers, clients, certs


""" Server Initialization Functions
"""

def tcp_server(port=0, ip='', Handler=servers.TCPHandler, tls=False, context=None, **kwargs):
    """Initialize TCPServer and return its manager object
    
    :param port: Port to listen on (Default: random high port)
    :type port: int
    :param ip: IP address to accept connections with (Default: 0.0.0.0)
    :type ip: str
    :param Handler: servers.TCPHandler class or subclass to process requests with
    :param tls: Attempt to wrap socket in SSL context
    :type tls: bool
    :param context: SSLContext to wrap socket with (If None, create context using **kwargs)
    :type context: ssl.SSLContext
    :param **kwargs: Keyword arguments passed to certs.create_server_context(), if tls enabled

    :returns ServerManager: TCPServerManager object wrapped around TCPServer
    """        
    server = servers.TCPServerManager(servers.TCPServer((ip, port), Handler))    
    if tls:
        if context is None:
            context = certs.create_server_context(**kwargs)
        server.enable_ssl(context)
    return server


def udp_server(port=0, ip='', Handler=servers.UDPHandler):
    """Initialize UDPServer and return its manager object
    
    :param port: Port to listen on (Default: random high port)
    :type port: int
    :param ip: IP address to accept connections with (Default: 0.0.0.0)
    :type ip: str
    :param Handler: servers.UDPHandler class or subclass to process requests with
    
    :returns ServerManager: ServerManager object wrapped around UDPServer
    """
    return servers.ServerManager(servers.UDPServer((ip, port), Handler))


def dns_tcp_server(port=53, ip='', Handler=servers.DNSHandlerTCP, default_ip=None, record=None, zonefile=None):
    """Initialize DNSServerTCP and return its manager object
    
    :param port: Port to listen on (Default: 53)
    :type port: int
    :param ip: IP address to accept connections with (Default: 0.0.0.0)
    :type ip: str
    :param Handler: servers.DNSHandlerTCP class or subclass to process requests with
    :param default_ip: Default IP address to answer DNS queries with, if not resolved by other means
    :type default_ip: str
    :param record: Zone-style DNS record to compare queries against
    :type record: str
    :param zonefile: Zone file of DNS records to populate server's records with
    :type zonefile: str
    
    :returns ServerManager: ServerManager object wrapped around DNSServerTCP
    """        
    server = servers.DNSServerManager(servers.DNSServerTCP((ip, port), Handler, default_ip=default_ip))
    if zonefile:
        server.add_zonefile(zonefile)
    if record:
        server.add_record(record)
    return server


def dns_server(port=53, ip='', Handler=servers.DNSHandler, default_ip=None, record=None, zonefile=None):
    """Initialize DNSServerTCP and return its manager object
    
    :param port: Port to listen on (Default: 53)
    :type port: int
    :param ip: IP address to accept connections with (Default: 0.0.0.0)
    :type ip: str
    :param Handler: servers.DNSHandler class or subclass to process requests with
    :param default_ip: Default IP address to answer DNS queries with, if not resolved by other means
    :type default_ip: str
    :param record: Zone-style DNS record to compare queries against
    :type record: str
    :param zonefile: Zone file of DNS records to populate server's records with
    :type zonefile: str
        
    :returns ServerManager: ServerManager object wrapped around DNSServer
    """        
    server = servers.DNSServerManager(servers.DNSServer((ip, port), Handler, default_ip=default_ip))
    if zonefile:
        server.add_zonefile(zonefile)
    if record:
        server.add_record(record)
    return server    
 
 
def http_server(port=8080, ip='', Handler=servers.HTTPHandler, dir=None, tls=False, context=None, **kwargs):
    """Initialize HTTPServer and return its manager object
    
    :param port: Port to listen on (Default: 8080)
    :type port: int
    :param ip: IP address to accept connections with (Default: 0.0.0.0)
    :type ip: str
    :param Handler: servers.HTTPHandler class or subclass to process requests with
    :param dir: Server's working directory (Default: CWD)
    :type dir: str
    :param tls: Attempt to wrap socket in SSL context
    :type tls: bool
    :param context: SSLContext to wrap socket with (If None, create context using **kwargs)
    :type context: ssl.SSLContext
    :param **kwargs: Keyword arguments passed to certs.create_client_socket(), if tls enabled
    
    :returns ServerManager: ServerManager object wrapped around HTTPHandler
    """
    server = servers.TCPServerManager(servers.HTTPServer((ip, port), Handler, dir))
    if tls:
        if context is None:
            context = certs.create_server_context(**kwargs)
        server.enable_ssl(context)
    return server   



"""Client Initialization Functions
"""

def tcp_client(remote_addr: tuple, Handler=clients.TCPClient, tls=False, context=None, hostname=None, **kwargs):
    """Initialize and return clients.TCPClient object
    
    :param remote_addr: IP address (or hostname) and port of remote socket
    :type remote_addr: tuple
    :param Handler: clients.TCPClient class or subclass to handle data exchange
    :type Handler: clients.TCPClient
    :param tls: Attempt to wrap socket in SSL context
    :type tls: bool
    :param context: SSLContext to wrap socket with (If None, create context using **kwargs)
    :type context: ssl.SSLContext
    :param hostname: Hostname of remote server (Required for SSL, unless hostname defined in remote_addr)
    :type hostname: str    
    :param **kwargs: Keyword arguments passed to certs.create_client_context(), if tls enabled
    
    :returns TCPClient: Client object for exchanging data with remote TCP server
    """
    client = Handler(remote_addr)
    if tls:
        if context is None:
            context = certs.create_client_context(**kwargs)
        client.enable_ssl(context, hostname)
    return client


def udp_client(remote_addr: tuple, Handler=clients.UDPClient):
    """Initialize and return clients.UDPClient object
    
    :param remote_addr: IP address (or hostname) and port of remote socket
    :type remote_addr: tuple
    :param Handler: clients.UDPClient class or subclass to handle data exchange
    :type Handler: clients.UDPClient
    
    :returns UDPClient: Client object for exchanging data with remote UDP server
    """
    return Handler(remote_addr)


def dns_client(remote_addr: tuple, Handler=clients.DNSClient):
    """Initialize and return clients.DNSClient object (UDP)
    
    :param remote_addr: IP address (or hostname) and port of remote socket
    :type remote_addr: tuple
    :param Handler: clients.DNSClient class or subclass to handle data exchange
    :type Handler: clients.DNSClient
    
    :returns DNSClient: Client object for sending queries to remote DNS server (UDP)
    """
    return udp_client(remote_addr, Handler)


def dns_tcp_client(remote_addr: tuple, Handler=clients.DNSClientTCP, tls=False, **kwargs):
    """Initialize and return clients.DNSClientTCP object (TCP)
    
    :param remote_addr: IP address (or hostname) and port of remote socket
    :type remote_addr: tuple
    :param Handler: clients.DNSClientTCP class or subclass to handle data exchange
    :type Handler: clients.DNSClientTCP
    :param tls: Attempt to wrap socket in SSL context
    :type tls: bool
    :param **kwargs: Keyword arguments passed to certs.create_client_context(), if tls enabled
    
    :returns DNSClientTCP: Client object for sending queries to remote DNS server (TCP)
    """
    return tcp_client(remote_addr, Handler, tls, **kwargs)


def http_client(remote_addr: tuple, 
    Handler=clients.HTTPClient, 
    dir=None, 
    tls: bool = False,
    context=None,
    hostname=None, 
    **kwargs):
    """Initialize and return clients.HTTPClient object
    
    :param remote_addr: IP address (or hostname) and port of remote socket
    :param Handler: clients.HTTPClient class or subclass to handle data exchange
    :type Handler: clients.HTTPClient
    :param dir: Working directory (Default: CWD)
    :type dir: str
    :param tls: Attempt to wrap socket in SSL context
    :type tls: bool
    :param context: SSLContext to wrap socket with (If None, create context using **kwargs)
    :type context: ssl.SSLContext
    :param hostname: Hostname of remote server (Required for SSL, unless hostname defined in remote_addr)
    :type hostname: str
    :param **kwargs: Keyword arguments passed to certs.create_client_socket(), if tls enabled
    
    :returns HTTPClient: Client object for exchanging data with remote web server (via GET and POST requests)
    """
    client = Handler(remote_addr, dir)
    if tls:
        if context is None:
            context = certs.create_client_context(**kwargs)
        client.enable_ssl(context, hostname)
    return client









    


