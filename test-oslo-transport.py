from oslo_config import cfg
import oslo_messaging
#from oslo_messaging.rpc import dispatcher
from oslo_log import log

DEFAULT_URL = "__default__"
RPC_TARGET = None
TRANSPORTS = {}

transport_url = 'rabbit://openstack:Y62KcEb7xJWOfjsmfMX7cuuaBKtq6rKQpisJRZvp@10.10.149.28:5672//'
service_opts = []

cfg.CONF.register_opts(service_opts)

def setup():
    oslo_messaging.set_transport_defaults('cloudkitty')

def get_transport(url=None, optional=False, cache=True):
    """Initialise the oslo_messaging layer."""
    global TRANSPORTS, DEFAULT_URL
    cache_key = url or DEFAULT_URL
    transport = TRANSPORTS.get(cache_key)
    if not transport or not cache:
        try:
            transport = oslo_messaging.get_rpc_transport(cfg.CONF, url)
        except (oslo_messaging.InvalidTransportURL,
                oslo_messaging.DriverLoadFailure):
            if not optional or url:
                # NOTE(sileht): oslo_messaging is configured but unloadable
                # so reraise the exception
                raise
            return None
        else:
            if cache:
                TRANSPORTS[cache_key] = transport
                print('cache_key:%s transport:%s'%(cache_key,transport))
    return transport

def get_target():
    global RPC_TARGET
    if RPC_TARGET is None:
        RPC_TARGET = oslo_messaging.Target(topic='cloudkitty', version='1.0')
    return RPC_TARGET

def get_client(version_cap=None):
    transport = get_transport(url=transport_url)
    print('get_client: transport: %s'%transport)
    target = get_target()
    return oslo_messaging.RPCClient(transport, target, version_cap=version_cap)

def cleanup():
    """Cleanup the oslo_messaging layer."""
    global TRANSPORTS, NOTIFIERS
    NOTIFIERS = {}
    for url in TRANSPORTS:
        TRANSPORTS[url].cleanup()
        #del TRANSPORTS[url]

if __name__ == '__main__':
    log.register_options(cfg.CONF)
    log.set_defaults()
    log.setup(cfg.CONF, 'cloudkitty')
    setup()
    a = get_transport(url=transport_url)
    print a.__dict__
    
    client = get_client()
    print client
    client = client.prepare(namespace='rating', fanout=True)
    print('%s'%'sssssssssssssssssssssssssssssssssssssss')
    #client.cast({}, 'disable_module', name='pyscripts')
    client.cast({}, 'enable_module', name='pyscripts')
    cleanup()

