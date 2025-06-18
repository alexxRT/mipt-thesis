from dataclasses import dataclass, InitVar
import logging

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)

@dataclass
class Edge:

    nodeFromUid: int = -1
    nodeToUid: int = -1

    encodedEdge: InitVar[dict] = None

    def __post_init__(self, encodedEdge = None):
        if encodedEdge is not None:
            self.nodeFromUid = int(encodedEdge["edgeFrom"])
            self.nodeToUid = int(encodedEdge["edgeTo"])

    def __dict__(self):

        if self.nodeFromUid == -1 or self.nodeToUid == -1:
            msg = f"Edge nodes were not inited! From __str__() -> str"
            LOG.log(logging.WARNING, msg)

        return {
            "edgeFrom" : self.nodeFromUid,
            "edgeTo" : self.nodeToUid
        }

    @property
    def fromUid(self):
        return self.nodeFromUid
    @property
    def toUid(self):
        return self.nodeToUid
