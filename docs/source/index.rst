.. Dynabyte documentation master file, created by
   sphinx-quickstart on Mon Sep 26 17:48:18 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Dynabyte Documentation
=========================

*Omniserver* is a Python module designed for quickly prototyping controllers/intercepting malicious network communications, and replicating various types of backdoor traffic. It is capable of quickly starting up highly customizable client and server objects, the goal being to provide maximum flexibility with the smallest amount of boilerplate code possible.

This documentation is to provide details on *Omniserver*'s overridable classes, as well as examples of its usage.

Installation
------------

.. code-block:: console

	$ pip install dynabyte


Contents
--------
.. toctree::
	:maxdepth: 2
	
	client_usage
	server_usage
	ssl_usage
	examples