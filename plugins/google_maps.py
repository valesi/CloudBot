import requests

from cloudbot import hook

# Define some constants
base_url = 'https://maps.googleapis.com/maps/api/'
geocode_api = base_url + 'geocode/json'

# Change this to a ccTLD code (eg. uk, nz) to make results more targeted towards that specific country.
# <https://developers.google.com/maps/documentation/geocoding/#RegionCodes>
bias = None

dev_key = None

API_STATUS_ERROR = {
    'REQUEST_DENIED': 'The geocode API is off in the Google Developers Console.',
    'ZERO_RESULTS': 'No results found.',
    'OVER_QUERY_LIMIT': 'The geocode API quota has run out.',
    'UNKNOWN_ERROR': 'Unknown Error.',
    'INVALID_REQUEST': 'Invalid Request.',
    'OK': None
}


@hook.on_start(api_keys=["google_dev_key"])
def load_key(bot):
    """ Loads the API key for Google APIs """
    global dev_key
    dev_key = bot.config.get("api_keys", {}).get("google_dev_key", None)


def query_geocoding_api(address):
    '''Returns the `results` list from the Geocoding API, or a string of the API error status.
    (https://developers.google.com/maps/documentation/geocoding/intro#GeocodingResponses)'''
    if not dev_key:
        return 'google_maps.py plugin must be enabled for geocoding'

    params = {"address": address, "key": dev_key}
    if bias:
        params['region'] = bias

    r = requests.get(geocode_api, params=params)
    r.raise_for_status()
    json = r.json()

    error = API_STATUS_ERROR.get(json['status'])
    if error is not None:
        return error

    return json['results']


@hook.command()
def maps(text):
    """<location> -- Finds <location> on Google Maps."""
    if not dev_key:
        return "This command requires a Google Developers Console API key."

    # Use the Geocoding API to get co-ordinates from the input
    result = query_geocoding_api(text)
    if isinstance(result, str):
        return result

    result = result[0]
    location_name = result['formatted_address']
    location = result['geometry']['location']
    formatted_location = "{lat},{lng},16z".format(**location)

    url = "https://google.com/maps/@" + formatted_location + "/data=!3m1!1e3"
    tags = result['types']

    # if 'political' is not the only tag, remove it.
    if not tags == ['political']:
        tags = [x for x in result['types'] if x != 'political']

    tags = ", ".join(tags).replace("_", " ")

    return "[h1]Maps:[/h1] {} [div] {} [div] [h3]{}[/h3]".format(location_name, url, tags)
