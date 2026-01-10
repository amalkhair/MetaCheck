import dns.resolver
from urllib.parse import urlparse

def check_spamhaus_dbl(url: str):
    domain = urlparse(url).hostname
    query = f"{domain}.dbl.spamhaus.org"
    try:
        dns.resolver.resolve(query, "A")
        print(f"⚠️ Domain {domain} is LISTED in Spamhaus DBL.")
    except dns.resolver.NXDOMAIN:
        print(f"✅ Domain {domain} is NOT listed in Spamhaus DBL.")
    except Exception as e:
        print(f"Error checking {domain}: {e}")

if __name__ == "__main__":
    check_spamhaus_dbl("https://pornkai.com/view?key=xv62373615")
