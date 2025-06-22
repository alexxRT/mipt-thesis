from profiler.utils import MlirGraph
from pathlib import Path
import logging
import json
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import subprocess
import argparse

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)

class DisplayDAG:
    def __init__(self, pathToDag: Path):
        if not pathToDag.exists():
            msg = "Path to graph to display does not exist"
            LOG.log(logging.ERROR, msg)
            raise RuntimeError(msg)

        self.pathToDag : Path = pathToDag
        self.mlirDag : MlirGraph = MlirGraph()

    def readGraph(self):
        with open(self.pathToDag, "r") as rd:
            jsonObj = json.load(rd)

        self.mlirDag.fromJson(jsonObj)

    # available options to store analysis graph
    # - graphml
    # - dot
    # .dot format can be used to generate .svg plots. Rich for visual analysis

    # returns stored graph path
    def storeGraph(self, storeName: str, storeOption: str) -> Path:
        toExport = self.mlirDag.toNetworkx()

        # Check for cycles before any export attempts
        if not nx.is_directed_acyclic_graph(toExport):
            raise RuntimeError("Graph contains cycles - cannot export DAG with cycles")

        store_path = Path(storeName)
        if store_path.suffix:
            base_name = store_path.stem
            store_dir = store_path.parent
        else:
            base_name = store_path.name
            store_dir = store_path.parent

        # get duration values for color mapping
        durations = [toExport.nodes[node].get('duration', 0) for node in toExport.nodes()]
        colorMap, norm = self.__getColorUtils(durations)

        if storeOption.lower() == 'graphml':
            outputFile = store_dir / f"{base_name}.graphml"
            self.__storeGraphml(outputFile, toExport, colorMap, norm)
            return outputFile

        if storeOption.lower() == 'dot':
            outputFile = store_dir / f"{base_name}.gv"
            self.__storeDot(outputFile, toExport, colorMap, norm)
            return outputFile

        msg = f"Unsupported store option: {storeOption}. Supported options: graphml, dot"
        LOG.log(logging.ERROR, msg)
        raise RuntimeError(msg)

    def plotGraphSvg(self, pathToDot: Path, outputFile: Path):
        if not pathToDot.exists():
            msg = f".gv file does not exist {pathToDot} when storing to .svg"
            LOG.log(logging.ERROR, msg)
            raise RuntimeError(msg)

        if pathToDot.suffix != ".gv":
            msg = f"input file has invalid suffix {pathToDot.suffix}. Supported: .gv"
            LOG.log(logging.ERROR, msg)
            raise RuntimeError(msg)

        # store to .svg:
        subprocess.run(['dot', '-Tsvg', str(pathToDot), '-o', str(outputFile)],
                        check=True, capture_output=True)

    # utils methods
    def __getColorUtils(self, durations: list):
        min_duration = min(durations)
        max_duration = max(durations)

        cmap = plt.cm.get_cmap('coolwarm')

        if max_duration > min_duration:
            norm = mcolors.Normalize(vmin=min_duration, vmax=max_duration)
        else:
            norm = mcolors.Normalize(vmin=0, vmax=1)

        return cmap, norm

    def __storeGraphml(self, store: Path, toExport: nx.DiGraph, cmap, norm):
        # add color attribute to every node
        for node in toExport.nodes():
            duration = toExport.nodes[node].get('duration', 0)

            color_val = norm(duration)
            rgb = cmap(color_val)
            hex_color = mcolors.rgb2hex(rgb)

            toExport.nodes[node]['color'] = hex_color

        nx.write_graphml(toExport, store)

    def __storeDot(self, store: Path, toExport: nx.DiGraph, cmap, norm):
        dotContent = ["digraph G {"]
        dotContent.append("    rankdir=TB;")
        dotContent.append("    node [shape=box];")

        for node in toExport.nodes():
            attrs = toExport.nodes[node]
            duration = attrs.get('duration', 0)
            ts = attrs.get('ts', 0)
            name = attrs.get('name', str(node))

            color_val = norm(duration)
            rgb = cmap(color_val)
            hex_color = mcolors.rgb2hex(rgb)

            label = f"{name}\\nduration: {duration}\\nts: {ts}"
            dotContent.append(f'    "{node}" [label="{label}", fillcolor="{hex_color}", style=filled];')

        for edge in toExport.edges():
            dotContent.append(f'    "{edge[0]}" -> "{edge[1]}";')

        dotContent.append("}")

        with open(store, 'w') as f:
            f.write('\n'.join(dotContent))


def main():
    parser = argparse.ArgumentParser(description="Plot Graph Script")
    parser.add_argument('--path-to-mlir-graph', '-t', required=True, type=str, help='Path to the input serilized .json DAG')
    parser.add_argument('--store-output', '-o', required=True, type=str, help='Path to store the output')
    parser.add_argument('--store-only', '-s', required=False, action='store_true', help='Store graph to .graphml format')
    args = parser.parse_args()

    inputGraph = Path(args.path_to_mlir_graph)
    output = Path(args.store_output)

    displayManager = DisplayDAG(inputGraph)
    displayManager.readGraph()

    if args.store_only:
        outputGraphPath = displayManager.storeGraph(output, "graphml")
    else:
        outputDotPath = displayManager.storeGraph(output, "dot")
        if output.suffix == ".svg":
            displayManager.plotGraphSvg(outputDotPath, output)

    LOG.log(logging.INFO, f"Successfully stored graph to {outputGraphPath}")

# usage example
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        msg = "Failed to store/display input graph"
        LOG.log(logging.ERROR, msg)
