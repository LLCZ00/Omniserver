Servers
=======
Server objects create listening sockets and await requests from remote clients. All servers are threaded by default, and can be run all at once or individually. Server instances are tracked internally by *Omniserver*, to ensure all threads are closed before the program exits.

All server objects are derived from *Handler* classes, which can be subclassed for greater control over data and adding additional functionality. For example, overriding the *incoming()* and *outgoing()* methods allows for data processing to customized any way you desire, as all incoming and outgoing data flows through them.


All the server/handler classes can be used pretty much the same way as their socketserver counterparts.

Server Manager
--------------
Upon spawning a server with its initialization function, a ServerManager object is returned. It acts as a wrapper around the server object, providing methods for starting and stopping the server thread/process.

.. autofunction:: omniserver.servers.ServerManager

.. autofunction:: omniserver.servers.ServerManager.start

.. autofunction:: omniserver.servers.ServerManager.wait

.. autofunction:: omniserver.servers.ServerManager.stop

If more than one server has been initialized, the following functions can be used to start/wait on threads all at once:

.. autofunction:: omniserver.servers.start_all

.. autofunction:: omniserver.servers.wait_all

.. autofunction:: omniserver.servers.stop_all

TCP
---
TCP server objects listen and await TCP requests. TLS/SSL capable.

Initialization Function
^^^^^^^^^^^^^^^^^^^^^^^
.. autofunction:: omniserver.core.tcp_server

Handler Class
^^^^^^^^^^^^^
.. autofunction:: omniserver.servers.TCPHandler

UDP
---
UDP server objects listen and await UDP data.

Initialization Function
^^^^^^^^^^^^^^^^^^^^^^^
.. autofunction:: omniserver.core.udp_server

Handler Class
^^^^^^^^^^^^^
.. autofunction:: omniserver.servers.UDPHandler

DNS
---
DNS server objects are capable of recieving and responding to DNS requests.

Initialization Functions
^^^^^^^^^^^^^^^^^^^^^^^^
.. autofunction:: omniserver.core.dns_server

.. autofunction:: omniserver.core.dns_tcp_server

Handler Classes
^^^^^^^^^^^^^^^
.. autofunction:: omniserver.servers.DNSHandler

.. autofunction:: omniserver.servers.DNSHandlerTCP


HTTP
----
HTTP server objects work basically the same as http.server. In fact they're basically just a wrapper. They accept GET/POST requests, and the files available to them depend on their working directory.
As they are a subclass of omniserver.servers.TCPServer, they are TLS/SSL compatible.


Initialization Function
^^^^^^^^^^^^^^^^^^^^^^^
.. autofunction:: omniserver.core.http_server

Handler Class
^^^^^^^^^^^^^
.. autofunction:: omniserver.servers.HTTPHandler
