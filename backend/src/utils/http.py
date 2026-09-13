import ipaddress
from typing import Optional

FORWARDED_SEPARATOR = ','
USER_AGENT_MAX = 500


def get_client_ip(request) -> Optional[str]:

    """ Address of whoever made the request.

        Order of trust: X-Real-IP set by our own nginx, then the
        first hop of the proxy chain, then the REMOTE_ADDR header the
        private server of nginx sets instead of the two above
        (nginx/includes/proxy_to_private_backend.conf, the header the
        private api permissions read too), then the socket address.

        Behind somebody else's balancer the headers are client
        controlled, so the result is only kept when it really is an
        address. Anything else would ride in every event of the
        request at whatever length and value the client chose.

        The file service resolves the same address without the
        X-Forwarded-For step (storage/src/shared_kernel/http_context.py):
        behind our own nginx both read X-Real-IP and agree, behind a
        foreign one the two may differ. """

    meta = request.META
    real_ip = _valid_ip(meta.get('HTTP_X_REAL_IP'))
    if real_ip:
        return real_ip
    forwarded = meta.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        first_hop = _valid_ip(forwarded.split(FORWARDED_SEPARATOR)[0])
        if first_hop:
            return first_hop
    return (
        _valid_ip(meta.get('HTTP_REMOTE_ADDR'))
        or _valid_ip(meta.get('REMOTE_ADDR'))
    )


def get_user_agent_header(request) -> Optional[str]:

    """ Raw User-Agent header, trimmed to a sane length.

        The events of a request carry it, and a header is whatever
        length a client sent. """

    user_agent = request.META.get('HTTP_USER_AGENT')
    if not user_agent:
        return None
    return user_agent[:USER_AGENT_MAX]


def _valid_ip(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    address = value.strip()
    try:
        ipaddress.ip_address(address)
    except ValueError:
        return None
    return address
