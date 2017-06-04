import requests
from cloudbot import hook


@hook.command(autohelp=False)
def cats():
    """gets a fucking fact about cats."""
    try:
        r = requests.get('https://catfacts-api.appspot.com/api/facts?number=1', timeout=10.0)
        j = r.json()
    except:
        return "there was an error finding a cat fact for you."
    return j.get('facts')


@hook.command(autohelp=False)
def catgifs():
    """gets a fucking cat gif."""
    params = { "type": "gif" }
    try:
        r = requests.get("http://thecatapi.com/api/images/get", params=params, timeout=10.0)
    except:
        return "there was an error finding a cat gif for you."
    return "OMG A CAT GIF: {}".format(r.url)


@hook.command(autohelp=False)
def catpic():
    """gets a fucking cat pic."""
    params = { "type": "jpg,png" }
    try:
        r = requests.get("http://thecatapi.com/api/images/get", params=params, timeout=10.0)
    except:
        return "there was an error finding a cat pic for you."
    return "Kitty! {}".format(r.url)
