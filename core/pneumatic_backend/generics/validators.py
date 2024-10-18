import re
from urllib.parse import urlsplit, urlunsplit
from django.core.validators import (
    URLValidator,
    validate_ipv6_address,
    _lazy_re_compile
)
from django.core.exceptions import ValidationError


class NoSchemaURLValidator(URLValidator):

    """ Allow URL without scheme """

    scheme_delimiter = '://'
    is_relative_url = None

    scheme_regex = r'^(?:[a-z0-9\.\-\+]*)://'
    relative_regex = (
        r'(?:[^\s:@/]+(?::[^\s:@/]*)?@)?'  # user:pass authentication
        r'(?:' + URLValidator.ipv4_re + '|'
        + URLValidator.ipv6_re + '|'
        + URLValidator.host_re + ')'
        r'(?::\d{2,5})?'  # port
        r'(?:[/?#][^\s]*)?'  # resource path
        r'\Z'
    )

    absolute_regex = regex = scheme_regex + relative_regex

    def _validate_url_by_regex(self, value: str):
        if self.is_relative_url:
            regex = _lazy_re_compile(self.relative_regex, re.IGNORECASE)
        else:
            regex = _lazy_re_compile(self.absolute_regex, re.IGNORECASE)
        regex_matches = regex.search(str(value))
        invalid_input = (
            regex_matches if self.inverse_match else not regex_matches
        )
        if invalid_input:
            raise ValidationError(self.message, code=self.code)

    def __call__(self, value):
        self.is_relative_url = self.scheme_delimiter not in value
        url_parts = value.split(self.scheme_delimiter)
        if not self.is_relative_url and len(url_parts) == 2:
            scheme = url_parts[0].lower()
            if scheme not in self.schemes:
                raise ValidationError(self.message, code=self.code)

        # Then check full URL
        try:
            self._validate_url_by_regex(value)
        except ValidationError as e:
            # Trivial case failed. Try for possible IDN domain
            if value:
                try:
                    scheme, netloc, path, query, fragment = urlsplit(value)
                except ValueError:  # for example, "Invalid IPv6 URL"
                    raise ValidationError(self.message, code=self.code)
                try:
                    # IDN -> ACE
                    netloc = netloc.encode('idna').decode('ascii')
                except UnicodeError:  # invalid domain part
                    raise e
                url = urlunsplit((scheme, netloc, path, query, fragment))
                self._validate_url_by_regex(url)
            else:
                raise
        else:
            # Now verify IPv6 in the netloc part
            host_match = re.search(
                r'^\[(.+)\](?::\d{2,5})?$',
                urlsplit(value).netloc
            )
            if host_match:
                potential_ip = host_match.groups()[0]
                try:
                    validate_ipv6_address(potential_ip)
                except ValidationError:
                    raise ValidationError(self.message, code=self.code)

        # The maximum length of a full host name is 253 characters per RFC 1034
        # section 3.1. It's defined to be 255 bytes or less, but this includes
        # one byte for the length of the name and one byte for the trailing dot
        # that's used to indicate absolute names in DNS.
        if len(urlsplit(value).netloc) > 253:
            raise ValidationError(self.message, code=self.code)
