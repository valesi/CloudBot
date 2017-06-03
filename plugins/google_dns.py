# https://developers.google.com/speed/public-dns/docs/dns-over-https
import requests
from dns import rcode, rdatatype, reversename

from cloudbot import hook


API_URL = "https://dns.google.com/resolve"


@hook.command("dig", "dns")
def google_dns(text):
    """<host> [type] - Queries Google's DNS-over-HTTPS service for <host> with record type [type] (default A)"""
    args = text.split()
    # Convert to punycode
    host = args[0].encode("idna").decode("utf-8").lower()
    qtype = args[1] if len(args) > 1 else "A"

    # Try to autodetect IP for reverse lookups
    try:
        host = reversename.from_address(host).to_text()
        qtype = "ptr"
    except:
        pass

    params = { "name": host, "type": qtype }

    try:
        req = requests.get(API_URL, params=params, timeout=5.0)
        data = req.json()
    except Exception as ex:
        return "Internal error: {}".format(ex)

    if not req.ok:
        return "HTTP {}: {}".format(req.status_code, data.get("Comment", "No info"))

    if data["Status"] != 0:
        info = " [div] [h1]Info:[/h1] " + data["Comment"] if "Comment" in data else ""
        return "{} [div] {}{}".format(host, rcode.to_text(data["Status"]), info)
    elif not data.get("Answer"):
        return "{} [div] No data".format(host)

    answers = []
    # Return up to and including first 3 answers
    for ans in data["Answer"][:3]:
        rtype = rdatatype.to_text(ans["type"])
        ttl = ans.get("TTL", "No TTL")
        answer = ans["data"]
        # Unescape strings in TXT records etc
        if "\\" in answer:
            answer = answer.decode('string_escape')
        answers.append("{} [h3]({}, {})[/h3]".format(answer, rtype, ttl))

    answer = " [div] ".join(answers)

    return "{} [div] {} [div] [h1]DNSSEC:[/h1] {}".format(host, answer, data["AD"])

