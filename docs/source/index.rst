.. Dynabyte documentation master file, created by
   sphinx-quickstart on Mon Sep 26 17:48:18 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Omniserver Documentation
=========================

*Omniserver* is a Python module designed for quickly creating highly customizable server/client objects, and to provide maximum flexibility using as little boilerplate code as possible. Common uses include prototyping/replicating malicious network communication methods, intercepting/controlling the traffic of "Command and Control"-type malware, or simply being a shortcut for general networking activities.

At its core, *omniserver* is essentially just a wrapper around Python's built-in *socketserver* module (which itself is just a wrapper around *socket*). The goal of *omniserver* is to extend *socketserver* by providing a wider variety of functions, and perhaps a simpler API. All of *omniserver*'s RequestHandler and Server objects are compatible with *socketserver*, and can basically be used in the same way as described in their documentation.

Installation
------------

.. code-block:: console

	$ pip install omniserver


Contents
--------
.. toctree::
	:maxdepth: 2
	
	client_usage
	server_usage
	ssl_usage
	examples
