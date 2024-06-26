import argparse
import ast
import url as urlmod
import utils
from os import path, makedirs
import re

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--url", help="url of the siteweb to map", required=True)
    parser.add_argument("-d", "--depth", default=2, help="maximum hops from the given url")
    parser.add_argument("-v", "--verbose", default=False, help="increases verbosity", action=argparse.BooleanOptionalAction)
    parser.add_argument("-t", "--tree", default=False, help="displays tree graphs", action=argparse.BooleanOptionalAction)
    parser.add_argument("-dim", "--dimension", default=2, help="dimensions of the graph (2d/3d)")
    parser.add_argument("-x", "--xcoef", default=1, help="x-axis node gap coefficient")
    parser.add_argument("-y", "--ycoef", default=1, help="y-axis node gap coefficient")
    parser.add_argument("-be", "--banexts", default=["png", "jpg", "jpeg", "ico", "svg"], help="additional extensions to ban", nargs='+')
    parser.add_argument("-cr", "--cache-results", default=False, help="puts the result in a cache file", action=argparse.BooleanOptionalAction)
    parser.add_argument("-cf", "--cache-file", default=False, help="uses the appropriate cache file to load graph", action=argparse.BooleanOptionalAction)
    parser.add_argument("-c", "--cookie", default=[], help="space separated list of cookies to include to the request", nargs='+')

    args = parser.parse_args()

    toVisitUrls = [urlmod.URL(str(args.url), isRef=True)]
    maxDepth = int(args.depth)
    verbosity = bool(args.verbose)
    tree = bool(args.tree)
    dim = int(args.dimension)
    xcoef = float(args.xcoef)
    ycoef = float(args.ycoef)
    banExts = args.banexts
    cacheResult = bool(args.cache_results)
    cacheFile = bool(args.cache_file)
    cacheDir = "cache"
    cacheFilename = re.sub("/", "_", toVisitUrls[0].page)+'.cache'
    cookies = args.cookie

    wellKnowns = [urlmod.URL(knownPage, refUrl=toVisitUrls[0]) for knownPage in ["robots.txt", "security.txt", "sitemap.xml", "xmlrpc.php", "wp-admin/login.php", "wp-admin/wp-login.php", "login.php", "wp-login.php", "admin"]]
    graph = {"recap": {"links": [], "outOfScopeURLs": [], "internal": {"nodeSize": 10}}, "known pages": {"links": [], "outOfScopeURLs": [], "internal": {"nodeSize": 2}}, toVisitUrls[0].page: {"links": [{"page": "known pages", "params": [], "method": "GET", "edgeSize": 2}], "outOfScopeURLs": [], "internal": {"nodeSize": 2}}}
    depth = 0
    sizeToVisitUrl = len(toVisitUrls)

    if not(cacheFile):
        # well known pages
        for wellKnown in wellKnowns:
            try:
                statusCode = utils.getStatusCode(wellKnown.url)
            except:
                utils.printVerb(verbosity, 'R', "[-] Error with the URL " + wellKnown.url)
                continue

            # if page exists
            if statusCode == 200:
                utils.printVerb(verbosity, 'G', "[+] Found known page " + wellKnown.url)

                # add to the recap and known pages
                graph["recap"]["outOfScopeURLs"].append(wellKnown.page)
                graph["known pages"]["outOfScopeURLs"].append(wellKnown.page)

                # create and link a new node for the known page
                graph[wellKnown.page] = {"links": [], "outOfScopeURLs": [], "internal": {"nodeSize": 2}}
                graph["known pages"]["links"].append({"page": wellKnown.page, "params": [], "method": "GET", "edgeSize": 2})

                # increase known pages node degree
                graph["known pages"]["internal"]["nodeSize"] += 1

            else:
                utils.printVerb(verbosity, 'Y', "[-] Known page " + wellKnown.url + " returned " + str(statusCode))            

        # other URL on the page
        for url in toVisitUrls:
            graph["recap"]["outOfScopeURLs"].append(url.page)

            if(depth < maxDepth and url.isUrl()):
                if not(url.page in graph): graph[url.page] = {"links": [], "outOfScopeURLs": [], "internal": {"nodeSize": 1}}
                utils.printVerb(verbosity, 'W', "On page " + url.url)
                # get page code
                try:
                    pageCode = utils.doRequest(url.url, cookies=cookies)
                except:
                    utils.printVerb(verbosity, 'R', "[-] URL " + url.url + " is not recognized")
                    continue
                
                # find urls
                urlsAndReqs = urlmod.findReqs(pageCode, url)

                for urlAndReq in urlsAndReqs:
                    foundUrl = urlmod.URL(urlAndReq[0], refUrl=url)
                    foundReq = urlAndReq[1]

                    if foundUrl.isUrl():
                        # foundUrl is from a website to map
                        if utils.isInScope(url.domain, foundUrl.domain) and not(foundUrl.getExtension() in banExts):
                            utils.printVerb(verbosity, 'G', "[+] Found a new page to map " + foundUrl.url)
                            graph[url.page]["links"].append(foundReq)
                            # increase degree of the target node
                            graph = utils.increaseNodeDegree(foundUrl.page, graph, foundReq["edgeSize"])
                            # add the found URL to the list of URL to visit
                            if not(foundUrl in toVisitUrls): 
                                toVisitUrls.append(foundUrl)
                        
                        else:
                            # foundUrl is not from a website to map or is a file that cannot be read (eg. picture)
                            # add foundURL to url's props
                            utils.printVerb(verbosity, 'G', "[+] Found property page " + foundUrl.url)
                            if not(foundUrl.page in graph[url.page]["outOfScopeURLs"]): graph[url.page]["outOfScopeURLs"].append(foundUrl.page)

                if(toVisitUrls.index(url)+1 == sizeToVisitUrl):
                    depth += 1
                    sizeToVisitUrl = len(toVisitUrls)

                graph[url.page]["internal"]["nodeSize"] += len(graph[url.page]["links"])
        
        graph["recap"]["outOfScopeURLs"] = sorted(list(set(graph["recap"]["outOfScopeURLs"])), key=str.lower)

    else:
        try:
            with open(path.join(cacheDir, cacheFilename), "r") as cf:
                graph = ast.literal_eval(cf.read())
        except:
            print("Cache file not found")

    if cacheResult:
        if not(path.isdir(cacheDir)):
            makedirs(cacheDir)
        with open(path.join(cacheDir, cacheFilename), 'w') as cf:
            cf.write(str(graph))

    graph = utils.computeGlobalLinkSize(graph)
    graph = utils.colorNodes(graph)
    graph = utils.colorEdges(graph, toVisitUrls[0].page)
    g = utils.makeNXGraph(graph)
    utils.drawGravis(g, dim, tree, xcoef, ycoef)

if __name__ == "__main__":
    main()