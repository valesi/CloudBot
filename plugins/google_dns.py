# https://developers.google.com/speed/public-dns/docs/dns-over-https
import requests
from dns import rcode, rdatatype, reversename

from cloudbot import hook


API_URL = "https://dns.google.com/resolve"


def query_api(host, qtype, reply):
    try:
        req = requests.get(API_URL, params={"name": host, "type": qtype}, timeout=5.0)
        if not req.ok:
            reply("Error: HTTP {}".format(req.status_code))
            return
        data = req.json()
    except Exception as ex:
        reply("Internal error: {}".format(ex))
        raise
    else:
        return data

    return


@hook.command("dig", "dns")
def google_dns(text, reply):
    """<host> [type] - Queries Google's DNS-over-HTTPS for <host> with record [type] (default AAAA and A. MX, SOA, PTR, TXT etc)."""
    args = text.split()
    raw_host = args.pop(0)
    # Convert to punycode
    host = raw_host.encode("idna").decode("utf-8").lower()

    a_and_aaaa = False
    if args:
        qtype = args[0]
    else:
        try:
            # autodetect IP for PTR if rtype wasn't given
            host = reversename.from_address(host).to_text()
            qtype = "PTR"
        except:
            a_and_aaaa = True
            qtype = "AAAA"

    data = query_api(host, qtype, reply)
    # API error
    if not data:
        return

    data.setdefault("Answer", [])

    # Now check A
    if a_and_aaaa:
        ipv4 = query_api(host, "A", reply)
        if not ipv4:
            return
        # Merge into good result
        if data["Status"] is 0 or ipv4["Status"] is 0:
            data["Status"] = 0
        data["Answer"].extend(ipv4.get("Answer", []))

    # Repack and dedupe based on type and data (often CNAME)
    answers = {}
    for ans in data["Answer"]:
        # Suppress hostname
        del ans["name"]
        # (rtype, rdata) tuple is answers key. ans is remaining dict data
        if (ans["type"], ans["data"]) not in answers:
            answers[ans.pop("type"), ans.pop("data")] = ans
    data["Answer"] = answers

    out = []

    if data["Status"] is not 0:
        out.append(rcode.to_text(data["Status"]))
    else:
        if data.get("Answer"):
            def format_answer(key, **kwargs):
                rtype, rdata = key
                return "[h1]{}:[/h1] {} [h3]({})[/h3]".format(
                    # Record type
                    rdatatype.to_text(rtype),
                    # Unescape strings in TXT records etc
                    rdata.decode('string_escape') if "\\" in rdata else rdata,
                    # TTL, and any other value
                    ", ".join([str(kwargs.pop("TTL", ""))] + ["{}: {}".format(k, v) for k, v in kwargs.items()])
                )
            # Return first 4 answers, formatted
            out.extend([format_answer(ans, **attribs) for ans, attribs in data["Answer"].items()][:4])
        else:
            out.append("No data")
    if "Comment" in data:
        out.append(data["Comment"])

    if data["AD"]:
        out.append("[h2]DNSSEC[/h2]")

    if raw_host != host:
        out.append(host)

    return " [div] ".join(out)
