from dataclasses import dataclass, InitVar
import logging as l

LOG = l.Logger(__name__, l.INFO)

@dataclass
class Edge:

    nodeFromUid: int = -1
    nodeToUid: int = -1

    encodedEdge: InitVar[dict] = None

    def __post_init__(self, encodedEdge = None):
        if encodedEdge is not None:
            self.nodeFromUid = int(encodedEdge["edgeFrom"])
            self.nodeToUid = int(encodedEdge["edgeTo"])

    def __str__(self) -> str:

        if self.nodeFromUid == -1 or self.nodeToUid == -1:
            msg = f"Edge nodes were not inited! From __str__() -> str"
            LOG.log(l.WARNING, msg)

        edgeDict: dict = {
            "edgeFrom" : self.nodeFromUid,
            "edgeTo" : self.nodeToUid
        }

        return edgeDict.__str__()

    @property
    def fromUid(self):
        return self.nodeFromUid
    @property
    def toUid(self):
        return self.nodeToUid
