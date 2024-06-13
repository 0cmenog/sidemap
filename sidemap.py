import argparse
import ast
from url import URL
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
    parser.add_argument("-be", "--banexts", default=[], help="additional extensions to ban", nargs='+')
    parser.add_argument("-cr", "--cache-results", default=False, help="puts the result in a cache file", action=argparse.BooleanOptionalAction)
    parser.add_argument("-cf", "--cache-file", default=False, help="uses the appropriate cache file to load graph", action=argparse.BooleanOptionalAction)

    args = parser.parse_args()

    toVisitUrls = [URL(str(args.url), isRef=True)]
    maxDepth = int(args.depth)
    verbosity = bool(args.verbose)
    tree = bool(args.tree)
    dim = int(args.dimension)
    xcoef = float(args.xcoef)
    ycoef = float(args.ycoef)
    banExts = args.banexts + ["png", "jpg", "jpeg", "ico", "svg"]
    cacheResult = bool(args.cache_results)
    cacheFile = bool(args.cache_file)
    cacheDir = "cache"
    cacheFilename = re.sub("/", "_", toVisitUrls[0].page)+'.cache'

    graph = {"recap": {"links": [], "outOfScopeURLs": [], "internal": {"nodeSize": 10}}}
    depth = 0
    sizeToVisitUrl = len(toVisitUrls)

    if not(cacheFile):
        for url in toVisitUrls:
            graph["recap"]["outOfScopeURLs"].append(url.page)
            alreadyAddedPages = [url.page]

            if(depth < maxDepth and url.isUrl()):
                if not(url.page in graph): graph[url.page] = {"links": [], "outOfScopeURLs": [], "internal": {"nodeSize": 2}}
                utils.printVerb(verbosity, 'W', "On page " + url.url)
                # get page code
                try:
                    page = utils.doRequest(url.url)
                except:
                    utils.printVerb(verbosity, 'R', "[-] URL " + url.url + " is not recognized")
                    continue
                # find urls
                foundUrls = utils.findUrls(page)

                for foundUrl in foundUrls:
                    foundUrl = URL(foundUrl, refUrl=url)

                    if foundUrl.isUrl():
                        # foundUrl has already been visited from this url
                        if foundUrl.page in alreadyAddedPages:
                            utils.printVerb(verbosity, 'Y', "[-] Found once again " + foundUrl.url)
                            if utils.isInScope(url.domain, foundUrl.domain) and not(foundUrl.getExtension() in banExts): graph[url.page]["links"].append(foundUrl.page)
                        # foundUrl is a new one
                        else:
                            # foundUrl is from a website to map
                            if utils.isInScope(url.domain, foundUrl.domain) and not(foundUrl.getExtension() in banExts):
                                utils.printVerb(verbosity, 'G', "[+] Found a new page to map " + foundUrl.url)
                                graph[url.page]["links"].append(foundUrl.page)
                                # increase degree of the target node
                                graph = utils.increaseNodeDegree(foundUrl.page, graph)
                                # add the found URL to the list of URL to visit
                                if not(foundUrl in toVisitUrls): toVisitUrls.append(foundUrl)
                            
                            else:
                                # foundUrl is not from a website to map or is a file that cannot be read (eg. picture)
                                # add foundURL to url's props
                                utils.printVerb(verbosity, 'G', "[+] Found property page " + foundUrl.url)
                                graph[url.page]["outOfScopeURLs"].append(foundUrl.page)
                        alreadyAddedPages.append(foundUrl.page)

                if(toVisitUrls.index(url)+1 == sizeToVisitUrl):
                    depth += 1
                    sizeToVisitUrl = len(toVisitUrls)

                graph[url.page]["internal"]["nodeSize"] += len(graph[url.page]["links"])
        
        graph["recap"]["outOfScopeURLs"].sort(key=str.lower)

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

    graph = utils.colorNodes(graph)
    g = utils.makeNXGraph(graph)
    utils.drawGravis(g, dim, tree, xcoef, ycoef)

if __name__ == "__main__":
    main()