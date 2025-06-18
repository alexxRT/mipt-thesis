import json
from .node import Node
from .edge import Edge
import networkx as nx
import logging as l


LOG = l.Logger(__name__, l.INFO)

class MlirGraph:
    VERSION = "1.0.0"

    nodes: list[Node] = []
    edges: list[Edge] = []

    nodeGroups: list[list] = []

    nodeID = 0

    # returns parent source level
    def addNode(self, node: Node, index: int = None):
        node.uid = self.nodeID
        # add by index or append
        if index is None:
            self.nodes.append(node)
        else:
            self.nodes[index] = node

        self.nodeID += 1

        lastLevel = self.nodeGroups.__len__()
        addLevel = lastLevel
        insertGroup = []

        for level, groupNodes in enumerate(self.nodeGroups):
            insideLevel = all([n.isParallelNode(node) for n in groupNodes])
            if insideLevel:
                addLevel = level
                break
            if not insideLevel and node.ts < groupNodes[0].ts:
                insertGroup.append(node)
                addLevel = level
                break

        if insertGroup:
            self.nodeGroups.insert(addLevel, insertGroup)
        else:
            if addLevel == len(self.nodeGroups):
                self.nodeGroups.append([node])
            else:
                self.nodeGroups[addLevel].append(node)


    def addEdge(self, nodeFrom: Node, nodeTo: Node):
        assert nodeFrom is not None
        assert nodeTo is not None

        if nodeFrom.uid >= self.nodeID or \
           nodeTo.uid >= self.nodeID or \
           nodeFrom.uid < 0 or \
           nodeTo.uid < 0:
                msg = f"Invalid nodes: both nodes must exist in graph to add new edge!"
                LOG.log(l.ERROR, msg)
                raise RuntimeError(msg)

        self.edges.append(Edge(nodeFrom.uid, nodeTo.uid))
        nodeFrom.addNeighbor(nodeTo)

    # has many rich internal visulize api and build-in on graph algorithms
    def toNetworkx(self) -> nx.DiGraph:

        nxGraph: nx.DiGraph = nx.DiGraph()

        for node in self.nodes:
            nxGraph.add_node(node.uid, duration=node.dur, ts=node.ts, name=node.name)

            for nNeighbor in node.getNeighbors():
                nxGraph.add_edge(node.uid, nNeighbor.uid)

        return nxGraph


    # convert graph to compact json
    def toJson(self):
        graphDict: dict = {
            "version" : self.VERSION,
            "nodes" : [n.__dict__() for n in self.nodes],
            "edges" : [e.__dict__() for e in self.edges]
        }

        graphStr = json.dumps(graphDict)
        return json.loads(graphStr)

    # init graph from json object
    def fromJson(self, jsonObj):
        if not self.checkJsonValid(self, jsonObj):
            msg = f"Bad input json format! {json.dumps(jsonObj, indent=2)[:100]} ..."
            LOG.log(l.ERROR, msg)
            raise RuntimeError(msg)

        version = jsonObj["version"]
        if version != self.VERSION:
            msg = f"Incompatible input format version! Input: {version}, support: {self.VERSION}"
            raise RuntimeError(msg)

        graphSize = len(jsonObj["nodes"])
        self.nodes = [None] * graphSize
        self.nodeID = graphSize
        self.edges.clear()
        self.nodeGroups.clear()

        for nEncoded in jsonObj["nodes"]:
            graphNode = Node(nEncoded)
            self.addNode(graphNode, graphNode.uid)

        for eEncoded in jsonObj["edges"]:
            graphEdge = Edge(eEncoded)
            self.addEdge(self.nodes[graphEdge.fromUid], self.nodes[graphEdge.toUid])

    def checkJsonValisd(self, js) -> bool:
        getVersion = js.get("version")
        getNodes = js.get("nodes")
        getEdges = js.get("edges")

        if getVersion is None:
            return False
        if getNodes is None:
            return False
        if getEdges is None:
            return False

        return True

