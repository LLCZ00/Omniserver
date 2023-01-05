Enabling TLS/SSL
================

Creating Contexts
-----------------
When calling *enable_ssl()* on any given TCP object, the **kwargs will be passed to one of the two context functions below. Alternatively, you can call these functions separately (or create your own context) and pass it to *enable_ssl()*.


.. autofunction:: omniserver.certs.create_client_context

.. autofunction:: omniserver.certs.create_server_context


Generating Certificates
-----------------------
Server-side TLS/SSL requires a certificate of some sort. They can be generated with the following function:


.. autofunction:: omniserver.certs.create_cert_key