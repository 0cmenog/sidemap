from networkx.drawing.nx_agraph import graphviz_layout
import networkx as nx
from colorama import Fore
import re
import gravis as gv

# list of char to remove at the end of a URL
lastSpecChar = "/#?"

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

## graph

def treefy(graph: nx.classes.digraph.DiGraph, xCoef: int = 1, yCoef: int = 1) -> nx.classes.digraph.DiGraph:
    # calculate layout to have a tree graph
    pos = graphviz_layout(graph, prog='dot')
    # add node positions as attributes
    for name, (x, y) in pos.items():
        node = graph.nodes[name]
        node['x'] = (x * xCoef)
        node['y'] = (y * yCoef)

    return graph

def makeNXGraph(graph: {}) -> nx.classes.digraph.DiGraph:
    g = nx.DiGraph()
    
    # add starting nodes
    for url in graph.keys():
        g.add_node(url)

    # add edges and attributes
    for url, linksAndProps in graph.items():
        # add edges
        for key, values in linksAndProps.items():
            if(key == "links"):
                for value in values:
                    g.add_edge(url,value)
        # add attributes
        nx.set_node_attributes(g, {url: {"click": '\n'.join(linksAndProps["props"]["outOfScopeURLs"])}})
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

## meta

def bulkApply(func, obj):
    return [function(subObj) for subObj in obj]

def bulkConstruct(func, objs) -> []:
    rets = set()
    for obj in objs:
        rets.add(func(obj))
    return rets
