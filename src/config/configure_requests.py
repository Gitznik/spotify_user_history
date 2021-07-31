import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import http

def configure_request(debug_level: int = 0, retries: int = 3) -> requests.Session:
    http.client.HTTPConnection.debuglevel = debug_level

    request_session = requests.Session()

    assert_status_hook = (lambda response, *args, **kwargs: 
                            response.raise_for_status())
    request_session.hooks['response'] = [assert_status_hook]

    retry_strategy = Retry(
        total=retries
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    request_session.mount("https://", adapter)
    request_session.mount("http://", adapter)

    return request_session


