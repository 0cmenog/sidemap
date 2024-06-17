from networkx.drawing.nx_agraph import graphviz_layout
import networkx as nx
from colorama import Fore
import re
import gravis as gv
from math import log
from urllib.request import Request, urlopen

# list of char to remove at the end of a URL
lastSpecChar = "/#?"
# user agent used in the request
userAgent = 'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-GB; rv:1.9.0.5) Gecko/2008120122 Firefox/3.0.5'


## search for url

def findUrls(page: str) -> []:
    return re.findall('href=[\'"]?([^\'" >]+)', page)

## operations on url

def matchScheme(url: str) -> str:
    return re.match("^((http|https):)?//", url)

def addScheme(string: str) -> str:
    return string if matchScheme(string) != None else "http://"+string

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

def increaseNodeDegree(page: str, graph: {}) -> {}:
    if page in graph:
        graph[page]["internal"]["nodeSize"] += 1
    else:
        # minimal nodeSize + 1
        graph[page] = {"links": [], "outOfScopeURLs": [], "internal": {"nodeSize": 2}}
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

def treefy(graph: nx.classes.digraph.DiGraph, xCoef: int = 1, yCoef: int = 1) -> nx.classes.digraph.DiGraph:
    # calculate layout to have a tree graph
    pos = graphviz_layout(graph, prog='dot')
    # add node positions as attributes
    for name, (x, y) in pos.items():
        node = graph.nodes[name]
        node['x'] = (x * xCoef)
        node['y'] = (y * yCoef)

    return graph

def makeNXGraph(graph: {}, root: str = "") -> nx.classes.digraph.DiGraph:
    g = nx.DiGraph()
    
    # add starting nodes
    for page in graph.keys():
        g.add_node(page, size=(10*log(graph[page]["internal"]["nodeSize"])), color=graph[page]["internal"]["color"])

    # add edges and attributes
    for page, linksAndProps in graph.items():
        # add edges
        for key, values in linksAndProps.items():
            if(key == "links"):
                for value in set(values):
                    if page == root and value == "known pages":
                        color = "lightgrey"
                    else: 
                        color = "black"
                    g.add_edge(page, value, size=log(values.count(value)+1), color=color)
        # add attributes
        nx.set_node_attributes(g, {page: {"click": '\n'.join(linksAndProps["outOfScopeURLs"])}})
    
    g.nodes["recap"]["x"] = -300
    g.nodes["recap"]["y"] = 300
    return g

def drawGravis(graph: nx.classes.digraph.DiGraph, dim: int = 2, tree: bool = False, xCoef: int = 1, yCoef: int = 1) -> None:
    if tree:
        graph = treefy(graph, xCoef, yCoef)
    if dim == 2:
        g = gv.d3(graph, show_node_label=True, show_edge_label=False, node_drag_fix=True, layout_algorithm_active=True, graph_height=500, details_height=200, show_details=True, show_menu=True)
    else:
        g = gv.three(graph, show_node_label=True, show_edge_label=False, node_drag_fix=True, layout_algorithm_active=True, graph_height=500, details_height=200, show_details=True, show_menu=True)

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
    return urlopen(url).getcode()

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
