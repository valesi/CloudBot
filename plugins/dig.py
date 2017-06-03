import requests

from cloudbot import hook


@hook.command
def dig(text, nick, message):
    """<domain> <recordtype> returns a list of records for the specified domain valid record types are A, NS, TXT, and MX. If a record type is not chosen A will be the default."""
    try:
        domain, rtype = text.split()
        rtype = rtype.upper()
        if rtype not in ["A", "AAAA", "NS", "MX", "TXT"]:
            rtype = "A"
    except:
        domain = text
        rtype = "A"
    url = "http://dig.jsondns.org/IN/{}/{}".format(domain, rtype)
    results = requests.get(url).json()
    out = "The following records were found for {}: ".format(domain)
    if results['header']['rcode'] == "NXDOMAIN":
        return "no dns record for {} was found".format(domain)
    #message("Records found for $(b){}$(b):".format(domain))
    for r in range(len(results['answer'])):
        domain = results['answer'][r]['name']
        rtype = results['answer'][r]['type']
        ttl = results['answer'][r]['ttl']
        if rtype == "MX":
            rdata = results['answer'][r]['rdata'][1]
        elif rtype == "TXT":
            rdata = results['answer'][r]['rdata'][0]
        else:
            rdata = results['answer'][r]['rdata']
        return "[h1]Name:[/h1] {} [div] [h1]Type:[/h1] {} [div] [h1]Data:[/h1] {} [div] [h1]TTL:[/h1] {}".format(
            domain, rtype, rdata, ttl)
