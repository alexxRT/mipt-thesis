
import json
from dataclasses import dataclass, InitVar
import logging as l

LOG = l.Logger(__name__, l.INFO)

@dataclass
class Node:

    _opName: str = None

    # operation start ts in picoseconds
    _ts: int = 0
    # operation duration in picoseconds
    _duration: int = 0

    # unique id among all nodes in graph
    _uniqueId: int = -1

    encodedEdge: InitVar[dict] = None

    def __post_init__(self, encodedNode = None):
        # list of adj for given node
        self._neighbors = []

        if encodedNode is not None:
            self.name = encodedNode["name"]
            self.ts = int(encodedNode["ts"])
            self.dur = int(encodedNode["duration"])
            self.uid = int(encodedNode["id"])

    def __str__(self) -> str:
        if self.uid == -1 or self.name is None:
            warnMsg = f"Storing node that was not inited! From __str__() -> str"
            LOG.log(l.WARNING, warnMsg)

        nodeDict : dict = {
            "name" : self.name,
            "ts" : self.ts,
            "duration" : self.dur,
            "id" : self.uid,
            "adj" : [n.uid for n in self.getNeighbors()]
        }

        return nodeDict.__str__()

    # getters and setters
    @property
    def ts(self) -> int:
        return self.ts
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
