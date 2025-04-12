import requests
import lxml.html
from urllib.parse import urlparse


def get_email(url):
    u = urlparse(url)
    if u.netloc != "facebook.com":
        u = u._replace(netloc="facebook.com")
    url = u.geturl()

    if url[-1] != "/":
        url += "/"

    if url[-6:] != "about/":
        url += "about/"

    r = requests.get(url)
    root = lxml.html.fromstring(r.text)

    email_link = root.xpath("//a[contains(@href,'mailto')]/@href")

    if email_link:
        return email_link[0].replace("mailto:", "")
    else:
        return None
