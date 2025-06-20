import json
from pathlib import Path
from utils.graph import MlirGraph
from utils.node import Node
from tqdm import tqdm
from google.protobuf.json_format import MessageToJson
from tensorflow.core.profiler.protobuf import xplane_pb2
import argparse
import logging

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)

NANOSEC_TO_PICOSEC = 1000

class JsonTFReader:

    # keys that persist in valid json
    ROOT = "planes"
    EVENTS_ARRAY = "lines"
    EVENTS = "events"
    TS = "timestamp_ns"
    EVENT_META = "event_metadata"
    STAT_META = "stat_metadata"

    # platform name from which to extract events
    HOST = "/host:CPU"

    def __init__(self, jsonFilePath: Path):
        if not self.checkFormat(jsonFilePath):
                errMsg = f"Input file {jsonFilePath} has wrong input format to parse!"
                LOG.log(logging.ERROR, errMsg)
                raise RuntimeError("Bad input profile file format!")

        self.rawJsonPath: Path = jsonFilePath
        self.readGraph: MlirGraph = MlirGraph()

    def readMlirGraph(self):
        with open(self.rawJsonPath, "r") as rj:
            jsonObject = json.load(rj)

        # find cpu events
        for e in jsonObject[self.ROOT]:
             if e["name"] == self.HOST:
                  cpuEvents = e
                  break

        events_metadata = cpuEvents[self.EVENT_META]
        # stats_metadta = cpuEvents[self.STAT_META] # TODO: support stats in nodes

        for lineEvents in tqdm(cpuEvents[self.EVENTS_ARRAY], "Read CPU events in graph", leave=False):
            originTs = int(lineEvents[self.TS])
            events = lineEvents[self.EVENTS]

            # slice for now, too many nodes
            events = events[:10000]

            # add all nodes in graph first
            for event in tqdm(events, f"Adding events id = {lineEvents['id']}", leave=False):
                nodeName = events_metadata[event["metadata_id"]].get("display_name")
                if nodeName is None:
                    nodeName = events_metadata[event["metadata_id"]]["name"]
                nodeTs = originTs * NANOSEC_TO_PICOSEC + int(event["offset_ps"])
                nodeDuration = 0 if event.get("duration_ps") is None else int(event["duration_ps"])

                self.readGraph.addNode(Node(nodeName, nodeTs, nodeDuration))

        # only one nodes level in graph -> return, no edges needed
        if len(self.readGraph.nodeGroups) == 1:
            return

        # traverse levels and add all edges
        for parentLevel, levelNodes in enumerate(self.readGraph.nodeGroups[1:]):
            for node in levelNodes:
                isEdgeAdded = False
                nodeParents = self.readGraph.nodeGroups[parentLevel]
                for parent in nodeParents:
                    if not parent.getNeighbors():
                        self.readGraph.addEdge(parent, node)
                        isEdgeAdded = True
                        break

                if not isEdgeAdded:
                    self.readGraph.addEdge(nodeParents[-1], node)

    # check input json file has appropriate structure to parse
    def checkFormat(self, rawJsonPath: Path) -> bool:
        with open(rawJsonPath, "r") as rj:
            obj = json.load(rj)

        getRoot = obj.get(self.ROOT)

        if getRoot is None:
            return False

        getCPU = None
        for e in obj[self.ROOT]:
            if e["name"] == self.HOST:
                getCPU = e
                break

        if getCPU is None:
            return False
        if getCPU.get(self.EVENT_META) is None:
            return False
        if getCPU.get(self.EVENTS_ARRAY)is None:
            return False
        # if getCPU.get(self.STAT_META) is None: TODO: support stats in nodes
        #     return False

        return True

    def dumpJson(self, dumpPath: Path):
        graphJson = self.readGraph.toJson()

        if not dumpPath.parent.exists():
            dumpPath.parent.mkdir(exist_ok=False)

        with open(dumpPath, "w") as dumpJs:
            json.dump(graphJson, dumpJs, indent=2)

class ProtobufTFReader:

    def __init__(self, rawTracePath: Path):
        if not rawTracePath.exists():
            msg = f"File .pb {rawTracePath} does not exist!"
            LOG.log(logging.ERROR, msg)
            raise RuntimeError(msg)

        self.rawPbPath: Path = rawTracePath

    def readToJson(self):
        with open(self.rawPbPath, 'rb') as f:
            data = f.read()

        xspace = xplane_pb2.XSpace()
        xspace.ParseFromString(data)
        jsonOutput = MessageToJson(xspace, preserving_proto_field_name=True)

        # store json trace object internaly
        self.jsonObject = json.loads(jsonOutput)

    def dumpJson(self, dumpPath: Path):
        if not dumpPath.parent.exists():
            dumpPath.parent.mkdir(exist_ok=False)

        with open(dumpPath, "w") as dumpJs:
            json.dump(self.jsonObject, dumpJs, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Trace Reader Script")
    parser.add_argument('--path-to-trace', '-t', required=True, type=str, help='Path to the input trace file. Supported formats: .pb, .json')
    parser.add_argument('--store-output', '-o', required=True, type=str, help='Path to store the output')
    args = parser.parse_args()

    inputTrace = Path(args.path_to_trace)
    output = Path(args.store_output)

    cleanProgram = False
    programFile = Path("./traceReader.json")

    if inputTrace.suffix == ".pb":
        pbReader = ProtobufTFReader(inputTrace)
        pbReader.readToJson()
        pbReader.dumpJson(programFile)
        cleanProgram = True
    elif inputTrace.suffix == ".json":
        programFile = inputTrace
    else:
        msg = f"Unsupported input trace file format {inputTrace.suffix}!"
        LOG.log(logging.ERROR, msg)
        raise RuntimeError(msg)

    jsonReader = JsonTFReader(programFile)
    jsonReader.readMlirGraph()
    jsonReader.dumpJson(output)

    if cleanProgram:
        programFile.unlink()

if __name__ == "__main__":
    try:
        main()
        print("Trace read successful!")
    except Exception as e:
        print(f"Trace read unseccessful! Programm finished with exception {e}")

