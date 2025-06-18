from dataclasses import dataclass, InitVar
import logging

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)

@dataclass
class Node:

    _opName: str = None

    # operation start ts in picoseconds
    _ts: int = 0
    # operation duration in picoseconds
    _duration: int = 0

    # unique id among all nodes in graph
    _uniqueId: int = -1

    encodedNode: InitVar[dict] = None

    def __post_init__(self, encodedNode = None):
        # list of adj for given node
        self._neighbors = []

        if encodedNode is not None:
            self.name = encodedNode["name"]
            self.ts = int(encodedNode["ts"])
            self.dur = int(encodedNode["duration"])
            self.uid = int(encodedNode["id"])

    def __dict__(self):
        if self.uid == -1 or self.name is None:
            warnMsg = f"Storing node that was not inited! From __str__() -> str"
            LOG.log(logging.WARNING, warnMsg)

        return {
            "name" : self.name,
            "ts" : self.ts,
            "duration" : self.dur,
            "id" : self.uid,
            "adj" : [n.uid for n in self.getNeighbors()]
        }

    def isParallelNode(self, node) -> bool:
        if not isinstance(node, Node):
            return False

        if node.ts >= self.ts and node.ts <= self.ts + self.dur or \
           self.ts >= node.ts and self.ts <= node.ts + node.dur:
                return True
        return False

    # getters and setters
    @property
    def ts(self) -> int:
        return self._ts
    @ts.setter
    def ts(self, ts: int):
        self._ts = ts

    @property
    def name(self) -> str:
        return self._opName
    @name.setter
    def name(self, name: str):
        self._opName = name

    @property
    def dur(self) -> int:
        return self._duration
    @dur.setter
    def dur(self, duration: int):
        self._duration = duration

    @property
    def uid(self):
        return self._uniqueId
    @uid.setter
    def uid(self, newId: int):
        self._uniqueId = newId

    def addNeighbor(self, node):
        self._neighbors.append(node)
    def getNeighbors(self) -> list:
        return self._neighbors
