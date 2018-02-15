# https://developers.google.com/speed/public-dns/docs/dns-over-https
import requests
from dns import rcode, rdatatype, reversename

from cloudbot import hook


API_URL = "https://dns.google.com/resolve"


@hook.command("dig", "dns")
def google_dns(text, reply):
    """<host> [type] - Queries Google's DNS-over-HTTPS for <host> with record [type] (default A. AAAA, MX, SOA, PTR, TXT etc)."""
    args = text.split()
    raw_host = args.pop(0)
    # Convert to punycode
    host = raw_host.encode("idna").decode("utf-8").lower()

    qtype = args[0] if args else "A"
    # autodetect IP for PTR if rtype wasn't given
    if not args:
        try:
            host = reversename.from_address(host).to_text()
            qtype = "PTR"
        except:
            pass

    try:
        req = requests.get(API_URL, params={"name": host, "type": qtype}, timeout=5.0)
        if not req.ok:
            return "Error: HTTP {}".format(req.status_code)
        data = req.json()
    except Exception as ex:
        reply("Internal error: {}".format(ex))
        raise

    out = []

    if data["Status"] is not 0:
        out.append(rcode.to_text(data["Status"]))
    else:
        if data.get("Answer"):
            # Suppress host
            def format_answer(name, type, data, **kwargs):
                return "[h1]{}:[/h1] {} [h3]({})[/h3]".format(
                    # Record type
                    rdatatype.to_text(type),
                    # Unescape strings in TXT records etc
                    data.decode('string_escape') if "\\" in data else data,
                    # TTL, and any other value
                    ", ".join([str(kwargs.pop("TTL", ""))] + ["{}: {}".format(k, v) for k, v in kwargs.items()])
                )
            # Return first 3 answers, formatted
            out.extend([format_answer(**ans) for ans in data["Answer"][:3]])
        else:
            out.append("No data")
    if "Comment" in data:
        out.append(data["Comment"])

    if data["AD"]:
        out.append("[h2]DNSSEC[/h2]")

    if raw_host != host:
        out.append(host)

    return " [div] ".join(out)
