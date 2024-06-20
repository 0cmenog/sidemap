from networkx.drawing.nx_agraph import graphviz_layout
import networkx as nx
from colorama import Fore
import re
import gravis as gv
from math import log
from urllib.request import Request, urlopen, HTTPError

# list of char to remove at the end of a URL
lastSpecChar = "/#?"
# user agent used in the request
userAgent = 'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-GB; rv:1.9.0.5) Gecko/2008120122 Firefox/3.0.5'


## operations on url

def matchScheme(url: str) -> str:
    return re.match("^((http|https):)?//", url)

def addScheme(string: str) -> str:
    return string if matchScheme(string) != None else "https://"+string

def removeScheme(url: str) -> str:
    return re.sub("^((http|https):)?//", "", url)

def removeStartSlash(url: str) -> str:
    return re.sub("^/+", "", url)

def removeLastSpecialChar(string: str) -> str:
    return string[:-1] if string[-1] in lastSpecChar else string

def isFile(string: str) -> bool:
    urlParts = string.split('/')
    if len(urlParts) >= 2:
        return '.' in urlParts[-1]

def getExtension(string: str) -> str:
    return string.split('.')[-1]

def removeDots(string: str) -> str:
    # does not manage cases where ../ lead out of the domain 
    parts = string.split("/")
    for i in range(parts.count("..")):
        parts.remove(parts[parts.index("..")-1])
        parts.remove(parts[parts.index("..")])
    for i in range(parts.count(".")):
        parts.remove(parts[parts.index(".")])
        
    return "/".join(parts)

## graph

def increaseNodeDegree(page: str, graph: {}, degree: int = 2) -> {}:
    if page in graph:
        graph[page]["internal"]["nodeSize"] += degree - 1
    else:
        # minimal nodeSize + 1
        graph[page] = {"links": [], "outOfScopeURLs": [], "internal": {"nodeSize": 2}}
    return graph

def computeLinkSize(urlsAndLinks: []) -> []:
    # [(url1, links1), (url2, links2), ...]
    for index, urlAndLink1 in enumerate(urlsAndLinks):
        # TODO: some identical URL can be specified in different manners here
        size = urlsAndLinks.count(urlAndLink1)
        # remove duplicate dicts of the list
        if size > 1:
            for urlAndLink2 in urlsAndLinks:
                if urlAndLink1[1]["page"] == urlAndLink2[1]["page"] and urlAndLink1[1]["method"] == urlAndLink2[1]["method"] and sorted(urlAndLink1[1]["params"]) == sorted(urlAndLink2[1]["params"]):
                    urlsAndLinks.remove(urlAndLink2)
        # define edge size
        urlsAndLinks[index][1]["edgeSize"] = size+1
    return urlsAndLinks

def computeGlobalLinkSize(graph: {}) -> {}:
    for page, attributes in graph.items():
        links = attributes["links"]
        newLinks = []
        alreadyAddedLinks = []
        for link1 in links:
            if (link1["page"], sorted(link1["params"]), link1["method"]) in alreadyAddedLinks:
                continue
            size = link1["edgeSize"]
            for link2 in links:
                if link1["page"] == link2["page"] and link1["method"] == link2["method"] and sorted(link1["params"]) == sorted(link2["params"]):
                        size += link2["edgeSize"] - 1
            alreadyAddedLinks.append((link1["page"], sorted(link1["params"]), link1["method"]))
            newLinks.append({"page": link1["page"], "params": link1["params"], "method": link1["method"], "edgeSize": size})
        graph[page]["links"] = newLinks
    return graph

def colorNodes(graph: {}) -> {}:
    # colors from matplotlib.colors.TABLEAU_COLORS
    colors = ['blue', 'orange', 'green', 'red', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']
    foundExts = []
    colorIndex = 0
    for page in graph:
        # add color for a file node
        if isFile(page):
            ext = getExtension(page)
            if ext in foundExts:
                color = colors[foundExts.index(ext) % len(colors)]
            else:
                color = colors[colorIndex % len(colors)]
                colorIndex += 1
                foundExts.append(ext)
        # let page nodes in black
        else:
            color = "black"
        graph[page]["internal"]["color"] = color
    return graph

def colorEdges(graph: {}, root: str) -> {}:
    # colors from matplotlib.colors.TABLEAU_COLORS
    colors = ['blue', 'orange', 'green', 'red', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']
    foundMethods = []
    colorIndex = 0
    for pageName, attributes in graph.items():
        # add color if not a GET method
        for index, link in enumerate(attributes["links"]):
            method = link["method"]
            if pageName == root and link["page"] == "known pages":
                color = "lightgrey"
            else:
                if method != "GET":
                    if method in foundMethods:
                        color = colors[foundMethods.index(method) % len(colors)]
                    else:
                        color = colors[colorIndex % len(colors)]
                        colorIndex += 1
                        foundMethods.append(method)
                # let GET methods in black
                else:
                    color = "black"
            graph[pageName]["links"][index]["color"] = color
    return graph

def treefy(graph: nx.classes.multidigraph.MultiDiGraph, xCoef: int = 1, yCoef: int = 1) -> nx.classes.multidigraph.MultiDiGraph:
    # calculate layout to have a tree graph
    pos = graphviz_layout(graph, prog='dot')
    # add node positions as attributes
    for name, (x, y) in pos.items():
        node = graph.nodes[name]
        node['x'] = (x * xCoef)
        node['y'] = (y * yCoef)

    return graph

def makeNXGraph(graph: {}) -> nx.classes.multidigraph.MultiDiGraph:
    g = nx.MultiDiGraph()
    for page, linksAndProps in graph.items():
        # add starting nodes
        g.add_node(page, size=(10*log(graph[page]["internal"]["nodeSize"])), color=graph[page]["internal"]["color"])
        # add edges
        for key, reqss in linksAndProps.items():
            if(key == "links"):
                for reqs in reqss:
                    g.add_edge(page, reqs["page"], size=log(reqs["edgeSize"]), color=reqs["color"], label='\n'.join(reqs["params"]))
        # add attributes
        nx.set_node_attributes(g, {page: {"click": '\n'.join(linksAndProps["outOfScopeURLs"])}})
        previousPage = ""
        for link in linksAndProps["links"]:
            if previousPage != link["page"]:
                index = 0
            nx.set_edge_attributes(g, {(page, link["page"], index): {"click": "" if link["params"] == [] else '\n'.join(link["params"])}})
            index += 1
            previousPage = link["page"]
    
    g.nodes["recap"]["x"] = -300
    g.nodes["recap"]["y"] = 300
    return g

def drawGravis(graph: nx.classes.multidigraph.MultiDiGraph, dim: int = 2, tree: bool = False, xCoef: int = 1, yCoef: int = 1) -> None:
    if tree:
        graph = treefy(graph, xCoef, yCoef)
    if dim == 2:
        g = gv.d3(graph, show_node_label=True, show_edge_label=True, edge_label_data_source='label', node_drag_fix=True, layout_algorithm_active=True, graph_height=500, details_height=200, show_details=True, show_menu=True, edge_curvature=0.2)
    else:
        g = gv.three(graph, show_node_label=True, show_edge_label=True, edge_label_data_source='label', node_drag_fix=True, layout_algorithm_active=True, graph_height=500, details_height=200, show_details=True, show_menu=True, edge_curvature=0.2)

    g.display()

## misc

def printVerb(verbosity: bool, color: str = 'N', message: str = "") -> None:
    if verbosity:
        if color == 'G':
            print(Fore.GREEN + message)
        elif color == 'Y':
            print(Fore.YELLOW + message)
        elif color == 'R':
            print(Fore.RED + message)
        elif color == 'W':
            print(Fore.WHITE + message)
        else:
            print(Fore.RESET + message)

def doRequest(url: str, cookies: [] = []) -> str:
    req = Request(url)
    req.add_header('User-Agent', userAgent)
    req.add_header('Cookie', "; ".join(cookies))
    return(urlopen(req).read().decode('utf-8'))

def getStatusCode(url: str) -> int:
    try:
        code = urlopen(url).code
    except HTTPError as e:
        code = e.code
    return code

def isInScope(refDomain: str, domain: str) -> bool:
    return re.match("(\.|^)"+refDomain, domain)

## meta

def bulkApply(func, obj):
    return [function(subObj) for subObj in obj]

def bulkConstruct(func, objs) -> []:
    rets = set()
    for obj in objs:
        rets.add(func(obj))
    return rets
