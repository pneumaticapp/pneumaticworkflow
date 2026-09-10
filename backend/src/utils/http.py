import ipaddress
from typing import Optional

FORWARDED_SEPARATOR = ','


def get_client_ip(request) -> Optional[str]:

    """ Address of whoever made the request.

        Order of trust: the address set by our own nginx, then the
        first hop of the proxy chain, then the socket address.

        Behind somebody else's balancer the first two are client
        controlled, so the result is only kept when it really is an
        address. Anything else would ride in every event of the
        request, and in every abuse counter keyed by the address, at
        whatever length and value the client chose. """

    meta = request.META
    real_ip = _valid_ip(meta.get('HTTP_X_REAL_IP'))
    if real_ip:
        return real_ip
    forwarded = meta.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        first_hop = _valid_ip(forwarded.split(FORWARDED_SEPARATOR)[0])
        if first_hop:
            return first_hop
    return _valid_ip(meta.get('REMOTE_ADDR'))


def _valid_ip(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    address = value.strip()
    try:
        ipaddress.ip_address(address)
    except ValueError:
        return None
    return address
