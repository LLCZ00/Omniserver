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
omniserver.utilities:
    - SSL wrappers/handles

Command to generate self-signed TLS certificate & private key:
openssl req -new -newkey rsa:4096 -x509 -sha256 -days 365 -nodes -out cert.crt -keyout private.key

Server certs signed by CA reference: https://gist.github.com/toolness/3073310

TODO:
    - Add CSR stuff
"""
import subprocess
import logging
import os
import sys
import ssl


__all__ = ["create_client_context", "create_server_context",
            "update_ca"]
if sys.platform == "linux":
    __all__.extend(["create_cert_key", "read_cert"])

"""
TLS/SSL Functions
"""
def create_client_context(protocol=ssl.PROTOCOL_TLS_CLIENT,
        cert_required=True,
        ca_cert=None,
        ca_path=None,
        ca_data=None,
        certfile=None,
        keyfile=None):
        """Create SSL context for client sockets
        
        Arguments can be passed to initialization functions as **kwargs,
        or this function can be called directly.
        
        :param protocol: Protocol to be passed to ssl.SSLContext()
        :param cert_required: Require a valid certificate from the server
        :type cert_required: bool
        :param ca_cert: Path to certificate to be used to verify server against
        :type ca_cert: str
        :param ca_path: Path to folder with certificates to verify server against
        :type ca_path: str
        :param ca_data: Ascii string of PEM-encoded cert, or DER-encoded bytes
        :param certfile: Certificate to be sent if asked to verify self
        :type certfile: str
        :param keyfile: Private key file
        :type keyfile: str
        
        :returns context: SSLContext that can be used to wrap a client socket
        :rtype: ssl.SSLContext
        """      
        ctx = ssl.SSLContext(protocol)
        if cert_required:
            ctx.check_hostname = True
            ctx.verify_mode = ssl.CERT_REQUIRED
            if ca_cert or ca_path or ca_data:
                try:
                    ctx.load_verify_locations(ca_cert, ca_path, ca_data)
                except Exception as e:
                    logging.exception("Exception occured loading CA certs")
            else:
                ctx.load_default_certs()
        else: 
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        if certfile:
            ctx.load_cert_chain(certfile, keyfile)     
        return ctx
        
def create_server_context(protocol=ssl.PROTOCOL_TLS_SERVER,
        certfile=None,
        keyfile=None):
        """Create SSL context for server sockets
        
        Arguments can be passed to initialization functions as **kwargs,
        or this function can be called directly.
        
        :param protocol: Protocol to be passed to ssl.SSLContext()
        :param certfile: Certificate to be sent if asked to verify self
        :type certfile: str
        :param keyfile: Private key file (Not required if in certfile)
        :type keyfile: str
        
        :returns context: SSLContext that can be used to wrap a server socket
        :rtype: ssl.SSLContext
        """
        ctx = ssl.SSLContext(protocol)
        ctx.load_cert_chain(certfile, keyfile)
        return ctx

def create_cert_key(cert="ca.crt", key="private.key", keysize=4096, days=365, **kwargs):
    """Generate self signed cert and private key
    
    Create self signed CA cert and private key, primarily for use by servers.
    Currently only available on Linux.
    
    :param cert: Name of created cert
    :type cert: str
    :param key: Name of created private key
    :type key: str
    :param keysize: Bit-size of private key encryption
    :type keysize: int
    :param days: Days
    :type days: int
    :param **kwargs: Cert subj information (C, ST, L, O, OU, CN)
    
    :returns cert_key: Absolute path to cert and private key
    :rtype: tuple
    """
    if sys.platform == "win32":
        raise NotImplementedError

    cmd = f"openssl req -new -newkey rsa:{str(keysize)} -x509 -sha256 -days {str(days)} -nodes -out {cert} -keyout {key}".split(" ")
    subj_cmd = ""

    subj = {
        "C":"US",
        "ST":"ND",
        "L":"Fargo",
        "O":"",
        "OU":"",
        "CN":"placeholder.com"
    }
    # Probably a better way to do this
    for arg in kwargs:
        if arg in subj:
            subj[arg] = kwargs[arg]
    
    for topic in subj:
        if subj[topic]:
            subj_cmd += f"/{topic}={subj[topic]}"

    if subj_cmd:
        cmd.append("-subj")
        cmd.append(subj_cmd)

    proc = subprocess.run(cmd)
    if proc.returncode != 0:
        logging.error("Error generating cert/private key")
        return None
        
    return os.path.abspath(cert), os.path.abspath(key)


def update_ca(certfile: str, remove: bool = False):
    """Add or remove root certificate to list of trusted certs 
    
    :param certfile: Path to CA file
    :type certfile: str
    :param remove: Remove given cert from trust CA list
    :type remove: bool
    """
    if not remove and not os.path.exists(certfile):
        raise Exception(f"Certificate not found '{certfile}'")
    
    if sys.platform == "linux":
        if remove:
            subprocess.run(["sudo", "update-ca-certificates", "--fresh"], check=True)
        else:
            subprocess.run(["sudo", "cp", certfile, "/usr/local/share/ca-certificates/"], check=True)
            subprocess.run(["sudo", "update-ca-certificates"], check=True)
        
    elif sys.platform == "win32":
        if remove:
            certid = "0x15" # Run command to get certid for certfile
            subprocess.run(['certutil', '-delstore', '"ROOT"', certid], check=True)
        else:
            subprocess.run(['certutil', '-addstore', '-f', '"ROOT"', certfile], check=True)
    else:
        print(f"Failed to install CA, unsupported platform '{sys.platform}'")


def read_cert(certpath):
    """Print certificate information
    
    Linux only
    """
    if sys.platform == "win32":
        raise NotImplementedError
    subprocess.run(f"openssl x509 -in {certpath} -text -noout".split(" "))

