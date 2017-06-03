import requests

from cloudbot import hook

api_url = 'http://api.mathjs.org/v1/'

@hook.command('calc', 'ca')
def calc(text):
    """<expression> - Simple calculator with units. (http://api.mathjs.org/)"""

    params = {
        'expr': text.strip(),
        'precision': ''
    }
    request = requests.get(api_url, params=params, timeout=10.0)

    if request.status_code != requests.codes.ok:
        return "HTTP {}: {}".format(request.status_code, request.text if request.text else 'Empty response')

    return request.text 
