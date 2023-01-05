Clients
=======
Client objects are used to establish connections and/or exchange data with a remote server. Client objects can be quickly initialized with their respective initialization function, or an instance can be declared manually from a Handler class.

All client objects are derived from *Handler* classes, which can be subclassed for greater control over data and adding additional functionality. For example, all data sent via *send()* or recieved via *recv()* is passed through the *outgoing()* and *incoming()* methods, respectivly. Overriding the latter methods allows you to customize the processing of data in any way you should so choose.


Base Client Class
-----------------
.. autofunction:: omniserver.clients.BaseClientHandler

TCP
---
TCP clients are used to establish a connection and communicate with TCP servers. Establishing a connection can be accomplished with the *connect()* method, or by using the *with* keyword on the TCPClient object, which automatically calls *connect()* and *close()* on the socket. The built-in *beacon()* method can also be used, as it calls the *connect()* method until it is successful.

TCP client objects, and any object that inherits them, are capable of TLS/SSL connections using the *enable_ssl()* method. See TLS/SSL section for more details.

Initialization Function
^^^^^^^^^^^^^^^^^^^^^^^
.. autofunction:: omniserver.core.tcp_client

Handler Class
^^^^^^^^^^^^^
.. autofunction:: omniserver.clients.TCPClient

.. autofunction:: omniserver.clients.TCPClient.send

.. autofunction:: omniserver.clients.TCPClient.recv

.. autofunction:: omniserver.clients.TCPClient.connect

.. autofunction:: omniserver.clients.TCPClient.enable_ssl

.. autofunction:: omniserver.clients.TCPClient.beacon

.. autofunction:: omniserver.clients.TCPClient.close

UDP
---
UDP clients are used to exchange data with a remote UDP socket. Since UDP is connectionless, there is no *connect()* method. The *with* keyword can still be used, but it's mostly a style choice since UDP "connections" don't need to be established or closed.

Initialization Function
^^^^^^^^^^^^^^^^^^^^^^^
.. autofunction:: omniserver.core.udp_client

Handler Class
^^^^^^^^^^^^^
.. autofunction:: omniserver.clients.UDPClient

.. autofunction:: omniserver.clients.UDPClient.send

.. autofunction:: omniserver.clients.UDPClient.recv

.. autofunction:: omniserver.clients.UDPClient.beacon

DNS
---
DNS clients can be used to send queries to remote DNS servers. They use the *query()* method instead of *send()* or *recv()*, but otherwise work the same as their parent protocol (TCP or UDP).

Initialization Functions
^^^^^^^^^^^^^^^^^^^^^^^^
.. autofunction:: omniserver.core.dns_client

.. autofunction:: omniserver.core.dns_tcp_client

Handler Class
^^^^^^^^^^^^^
.. autofunction:: omniserver.clients.DNSClient

.. autofunction:: omniserver.clients.DNSClientTCP

The methods for TCP and UDP DNS clients are the same, they just handle their sockets differently.

.. autofunction:: omniserver.clients.DNSClient.query

HTTP
----
HTTP clients are used for issuing GET and POST requests to a remote web server.

Initialization Function
^^^^^^^^^^^^^^^^^^^^^^^
.. autofunction:: omniserver.core.http_client

Handler Class
^^^^^^^^^^^^^
.. autofunction:: omniserver.clients.HTTPClient

.. autofunction:: omniserver.clients.HTTPClient.get

.. autofunction:: omniserver.clients.HTTPClient.post

.. autofunction:: omniserver.clients.HTTPClient.connect

.. autofunction:: omniserver.clients.HTTPClient.enable_ssl