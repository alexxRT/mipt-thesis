import json
import logging as l
from pathlib import Path
from graph import MlirGraph

LOG = l.Logger(__name__, l.INFO)

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

    rawJson: Path
    readGraph: MlirGraph

    def __init__(self, jsonFilePath: Path):
        if  not self.checkFormat():
                errMsg = f"Input file {jsonFilePath} has wrong input format to parse!"
                LOG.log(l.ERROR, errMsg)

        self.rawJson = jsonFilePath

    def readMlirGraph(self):
        with open(self.rawJson, "r") as rj:
            jsonObject = json.load(rj)

        # find cpu events
        for e in jsonObject[self.ROOT]:
             if e["name"] == self.HOST:
                  cpuEvents = e
                  break

        events_metadata = cpuEvents[self.EVENT_META]
        stats_metadta = cpuEvents[self.STAT_META]

        for cpuEvents in cpuEvents[self.EVENTS_ARRAY]:
            originTs = int(cpuEvents[self.TS])
            events = cpuEvents[self.EVENTS]

            # bla bla code adding node in MlirGraph
            # logic of separation and insertion on approproate level (ts + offset)
            for event in events:
                pass


    # check input json file has appropriate structure to parse
    def checkFormat(self, obj) -> bool:
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

        getEventsMeta = getCPU.get(self.EVENT_META)
        getStatsMeta = getCPU.get(self.STAT_META)
        getEvents = getCPU.get(self.EVENTS_ARRAY)

        if getEventsMeta is None:
            return False
        if getStatsMeta is None:
            return False
        if getEvents is None:
            return False

        return True

if __name__ == "__main__":
    with open("../profiler_json/trace.xplane.json", "r") as pj:
        jsonRead = json.load(pj)

    print(jsonRead["planes"][0].keys())

