import os
from re import compile as re_compile
from re import search
from typing import Final, Iterable, Any
from urllib.parse import urlparse, urlunparse, unquote
from wsgiref.types import WSGIEnvironment
from requests.models import PreparedRequest

HTTP_REQUEST_METHOD: Final = "http.request.method"
HTTP_FLAVOR: Final = "http.flavor"
HTTP_HOST: Final = "http.host"
HTTP_SCHEME: Final = "http.scheme"
HTTP_USER_AGENT: Final = "http.user_agent"
HTTP_SERVER_NAME: Final = "http.server_name"
SERVER_ADDRESS: Final = "server.address"
SERVER_PORT: Final = "server.port"
URL_PATH: Final = "url.path"
URL_QUERY: Final = "url.query"
CLIENT_ADDRESS: Final = "client.address"
CLIENT_PORT: Final = "client.port"
URL_FULL: Final = "url.full"

HTTP_REQUEST_BODY_SIZE: Final = "http.request.body.size"
HTTP_REQUEST_HEADER: Final = "http.request.header"
HTTP_REQUEST_SIZE: Final = "http.request.size"
HTTP_RESPONSE_BODY_SIZE: Final = "http.response.body.size"
HTTP_RESPONSE_HEADER: Final = "http.response.header"
HTTP_RESPONSE_SIZE: Final = "http.response.size"
HTTP_RESPONSE_STATUS_CODE: Final = "http.response.status_code"
HTTP_ROUTE = "http.route"


def collect_request_attributes(environ: WSGIEnvironment):

    attributes: dict[str] = {}

    request_method = environ.get("REQUEST_METHOD", "")
    request_method = request_method.upper()
    attributes[HTTP_REQUEST_METHOD] = request_method
    attributes[HTTP_FLAVOR] = environ.get("SERVER_PROTOCOL", "")
    attributes[HTTP_SCHEME] = environ.get("wsgi.url_scheme", "")
    attributes[HTTP_SERVER_NAME] = environ.get("SERVER_NAME", "")
    attributes[HTTP_HOST] = environ.get("HTTP_HOST", "")
    host_port = environ.get("SERVER_PORT")
    if host_port:
        attributes[SERVER_PORT] = host_port
    target = environ.get("RAW_URI")
    if target is None:
        target = environ.get("REQUEST_URI")
    if target:
        path, query = _parse_url_query(target)
        attributes[URL_PATH] = path
        attributes[URL_QUERY] = query
    remote_addr = environ.get("REMOTE_ADDR", "")
    attributes[CLIENT_ADDRESS] = remote_addr
    attributes[CLIENT_PORT] = environ.get("REMOTE_PORT", "")
    remote_host = environ.get("REMOTE_HOST")
    if remote_host and remote_host != remote_addr:
        attributes[CLIENT_ADDRESS] = remote_host
    attributes[HTTP_USER_AGENT] = environ.get("HTTP_USER_AGENT", "")
    return attributes


def collect_attributes_from_request(request: PreparedRequest) -> dict[str]:
    attributes: dict[str] = {}

    url = remove_url_credentials(request.url)
    attributes[HTTP_REQUEST_METHOD] = request.method
    attributes[URL_FULL] = url
    parsed_url = urlparse(url)
    if parsed_url.scheme:
        attributes[HTTP_SCHEME] = parsed_url.scheme
    if parsed_url.hostname:
        attributes[HTTP_HOST] = parsed_url.hostname
    if parsed_url.port:
        attributes[SERVER_PORT] = parsed_url.port
    return attributes


def url_disabled(url: str, excluded_urls: Iterable[str]) -> bool:
    """
    Check if the url is disabled.
    Args:
        url: The url to check.
        excluded_urls: The excluded urls.
    Returns:
        True if the url is disabled, False otherwise.
    """
    if excluded_urls is None:
        return False
    regex = re_compile("|".join(excluded_urls))
    return search(regex, url)


def get_excluded_urls(instrumentation: str) -> list[str]:
    """
    Get the excluded urls.
    Args:
        instrumentation: The instrumentation to get the excluded urls for.
    Returns:
        The excluded urls.
    """

    excluded_urls = os.environ.get(f"{instrumentation}_EXCLUDED_URLS")

    return parse_excluded_urls(excluded_urls)


def parse_excluded_urls(excluded_urls: str) -> list[str]:
    """
    Parse the excluded urls.
    Args:
        excluded_urls: The excluded urls.
    Returns:
        The excluded urls.
    """
    if excluded_urls:
        excluded_url_list = [
            excluded_url.strip() for excluded_url in excluded_urls.split(",")
        ]
    else:
        excluded_url_list = []

    return excluded_url_list


def remove_url_credentials(url: str) -> str:
    """Given a string url, remove the username and password only if it is a valid url"""

    try:
        parsed = urlparse(url)
        if all([parsed.scheme, parsed.netloc]):  # checks for valid url
            parsed_url = urlparse(url)
            _, _, netloc = parsed.netloc.rpartition("@")
            return urlunparse(
                (
                    parsed_url.scheme,
                    netloc,
                    parsed_url.path,
                    parsed_url.params,
                    parsed_url.query,
                    parsed_url.fragment,
                )
            )
    except ValueError:  # an unparsable url was passed
        pass
    return url


def parser_host_port_url_from_asgi(scope: dict[str, Any]):
    """Returns (host, port, full_url) tuple."""
    server = scope.get("server") or ["0.0.0.0", 80]
    port = server[1]
    server_host = server[0] + (":" + str(port) if str(port) != "80" else "")
    full_path = scope.get("path", "")
    http_url = scope.get("scheme", "http") + "://" + server_host + full_path
    return server_host, port, http_url


def collect_request_attributes_asgi(scope: dict[str, Any]):
    attributes: dict[str] = {}
    server_host, port, http_url = parser_host_port_url_from_asgi(scope)
    query_string = scope.get("query_string")
    if query_string and http_url:
        if isinstance(query_string, bytes):
            query_string = query_string.decode("utf8")
        http_url += "?" + unquote(query_string)
    attributes[HTTP_REQUEST_METHOD] = scope.get("method", "")
    attributes[HTTP_FLAVOR] = scope.get("http_version", "")
    attributes[HTTP_SCHEME] = scope.get("scheme", "")
    attributes[HTTP_HOST] = server_host
    attributes[SERVER_PORT] = port
    attributes[URL_FULL] = remove_url_credentials(http_url)
    attributes[URL_PATH] = scope.get("path", "")
    header = scope.get("headers")
    if header:
        for key, value in header:
            if key == b"user-agent":
                attributes[HTTP_USER_AGENT] = value.decode("utf8")

    client = scope.get("client")
    if client:
        attributes[CLIENT_ADDRESS] = client[0]
        attributes[CLIENT_PORT] = client[1]

    return attributes


def _parse_url_query(url: str):
    parsed_url = urlparse(url)
    path = parsed_url.path
    query_params = parsed_url.query
    return path, query_params
