import re
import validators
import utils
from urllib.parse import unquote

class URL:
    """Class that defines different forms and operations for a URL"""

    ### attributes
    # http://host.domain.tld/page/page.ext?key=val#ref
    url = ""
    # host.domain.tld/page/page.ext
    page = ""
    # domain.tld
    domain = ""
    # host.domain.tld
    hostname = ""

    ### methods

    ## constructor
    def __init__(self, url: str, refUrl: str = "", isRef: bool = False) -> None:
        # http://hostname.domain.tld/pages/page.ext?key=value#
        self.url = self._normalize(self._urlDecode(url), refUrl, isRef)
        # hostname.domain.tld/pages/page.ext
        self.page = self._constructPage(self.url)
        # hostname.domain.tld
        self.hostname = self._constructHostname(self.url)
        # domain.tld
        self.domain = self._constructDomain(self.url)

    def __eq__(self, other): 
        if not isinstance(other, URL):
            return NotImplemented

        return self.url == other.url and self.page == other.page and self.hostname == other.hostname and self.domain == other.domain

    ## get info from url

    def isFile(self) -> bool:
        urlParts = self.url.split('/')
        if len(urlParts) >= 2:
            return '.' in urlParts[-1]

    def getExtension(self) -> str:
        return self.page.split('.')[-1]
    
    def isUrl(self) -> bool:
        return validators.url(self.url)

    def _isFile(self, url: str) -> bool:
        urlParts = url.split('/')
        if len(urlParts) >= 2:
            return '.' in urlParts[-1]
        return False

    ## construct from url

    # have '/' at the end if not a file
    def _constructPage(self, url: str) -> str:
        url = re.sub("^((http|https)://)", "", url).split("#")[0].split("?")[0]
        return url + ("" if (self._isFile(url) or url[-1] == "/") else "/")

    # can not have '/' at the end
    def _constructHostname(self, url: str) -> str:
        return self._constructPage(url).split('/')[0]

    # removes the first part of the given URL if there is more than domain.tld
    # can not have '/' at the end
    def _constructDomain(self, url: str) -> str:
        parts = self._constructHostname(url).split('.')
        return '.'.join(parts[1:]) if len(parts) > 2 else '.'.join(parts)

    ## operations on url

    def _urlDecode(self, string: str) -> str:
        return unquote(string)

    # Add the refURL if the found URL is a relative path
    def _normalize(self, url: str, ref, isRef: bool) -> str:
        url = self._urlDecode(url)
        url = utils.removeLastSpecialChar(url)
        if isRef:
            return utils.addScheme(url)
        else:
            # if relative reference
            # WARNING: we suppose that pages to visit are always under the same hostname
            # otherwise, we should adapt the prefix to the reference of the relative path
            if utils.matchScheme(url) == None:
                return utils.addScheme(ref.hostname+"/"+utils.removeStartSlash(url))
            elif url.startswith("//"):
                return utils.addScheme(url[2:])
            # if absolute reference
            else:
                return url

