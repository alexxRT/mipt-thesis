# this script runs whole pipeline for automatic tf mlir annoatations

import subprocess
from pathlib import Path
import configparser
import logging
from display import DisplayDAG
import pandas as pd
import argparse

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)

"""
- Read supporting for annotaions operations.
- Its user responsibility to make sure its supported.
- If not -> no annotations will be added, script result surpressed.
"""
confParser = configparser.ConfigParser()
confParser.read("operations.cfg")

def getSupportedOps(parser):
    supportedOps = []
    for key in parser.keys():
        ops = parser[str(key)]
        keyOps = [str(op) for k, op in ops.items() if k != "description"]

        supportedOps.extend(keyOps)
    return supportedOps

supportedOps: list[str] = getSupportedOps(confParser)

print(supportedOps)

"""
This class designed to run end-to-end tool for autonomative mlir annotations with profile data

Input:
inputProfile: Path - path to python program written in tensorflow framework

Output:
output: Path - path to directory where to store:
    1. visual/stored graph representation (.graphml, .svg, .dot)
    2. annotated mlir
"""

class Pipeline:

    # store some intermidiate results here
    TMP_DIR: Path = Path("./cache")

    def __init__(self, inputProfile: Path, output: Path, eraseCache: bool=True):
        if not inputProfile.exists() or inputProfile.is_dir():
            errMsg = f"Bad pipeline init! Input file {inputProfile} does not exist or not a file"
            LOG.log(logging.ERROR, errMsg)
            raise RuntimeError(errMsg)

        if inputProfile.suffix != ".py":
            errMsg = f"Bad pipeline init! Input file extension {inputProfile.suffix}. Supported: .py"
            LOG.log(logging.ERROR, errMsg)
            raise RuntimeError(errMsg)

        self.input: Path = inputProfile
        self.outputDir: Path = output
        self.clean = eraseCache

        self.outputDir.mkdir(exist_ok=True)

        if self.TMP_DIR.exists():
            dialogMsg = \
f"{self.TMP_DIR} already exists. Override cache or store new location?\n \
{'-'*40}\n\n \
0 - override\n \
1 - specify new store locationn\n\n \
{'-'*40}\n"
            print(dialogMsg)
            try:
                option = int(input())
                if option != 0 and option != 1:
                    errMsg = f"Bad pipeline init! Specified option {option}. Supported: 0, 1"
                    LOG.log(logging.ERROR, errMsg)
                    raise RuntimeError(errMsg)
            except Exception as e:
                raise RuntimeError(f"Bad pipeline init! {e}")

            if option == 1:
                print(f"Input new cache store location: ", end="")
                self.TMP_DIR = Path(input())

            if option == 0:
                removeCacheCmd = f"rm -rf {self.TMP_DIR}"
                subprocess.run(removeCacheCmd.split(), check=True)

        self.TMP_DIR.mkdir(exist_ok=True)
        LOG.log(logging.INFO, "Pipeline inited successfully! Ready to annotate your mlir!")

    def run(self):
        pathToModel: Path = self.TMP_DIR / "saved_model"
        pathToProfile: Path = self.TMP_DIR / "profile.pb"

        # collect profile for input programm and save model
        print(f"0. {'-'*10} Collect profile with TensorFlow Profiler and saving model {'-'*10}")
        collectCmd = f"python3 {self.input} --l logdir"
        subprocess.run(collectCmd.split(), check=True)
        moveOutputCmd = f'mv `find ./logdir/plugins -name "*.pb"` {pathToProfile} && mv logdir/saved_model {pathToModel} && rm -rf logdir'
        subprocess.run(moveOutputCmd, shell=True, check=True)

        print(f"1. {'-'*10} Serilizing TensorFlow Profiler output {'-'*10}")
        readOutput = self.TMP_DIR / 'read_profile.json'
        readProfileCmd: str = f"python3 -m profiler.traceReader -t {pathToProfile} -o {readOutput}"
        subprocess.run(readProfileCmd.split(), check=True)

        print(f"2. {'-'*10} Read DAG {'-'*10}")
        DAG: DisplayDAG = DisplayDAG(readOutput)
        DAG.readGraph()

        print(f"3. {'-'*10} Storing operation statistic for annotations {'-'*10}")
        annotateProfile: Path = self.TMP_DIR / "profile.csv"
        operationStats: pd.DataFrame = DAG.getOpStats(supportedOps)
        operationStats.to_csv(annotateProfile , index=False)

        print(f"4. {'-'*10} Storing graph for structural analysis {'-'*10}")
        storePath: Path = self.outputDir / "dag"
        DAG.storeGraph(storePath, "graphml")
        DAG.storeGraph(storePath, "dot")
        DAG.plotGraphSvg(Path(f"{storePath}.gv"), Path(f"{storePath}.svg"))

        print(f"5. {'-'*10} Dumping initial MLIR {'-'*10}")
        pathToMLIR: Path = self.TMP_DIR / "initial.mlir"
        translateCmd = f"tf-mlir-translate --savedmodel-objectgraph-to-mlir {pathToModel} -o {pathToMLIR}"
        subprocess.run(translateCmd.split(), check=True)

        print(f"6. {'-'*10} Annotate initial MLIR with profile data {'-'*10}")
        pathToAnnotatedMLIR: Path = self.outputDir / "annotated.mlir"
        annotateCmd = f"tf-opt --tf-pgo-pipeline=path-to-profile={annotateProfile} {pathToMLIR} -o {pathToAnnotatedMLIR}"
        subprocess.run(annotateCmd.split(), check=True)

        if self.clean:
            cleanCmd = f"rm -rf {self.TMP_DIR}"
            subprocess.run(cleanCmd.split())


def main():
    parser = argparse.ArgumentParser(description="End-to-End TensorFLow MLIR annotations")
    parser.add_argument('--path-to-model', '-m', required=True, type=str, help='Path to model python code. Supported .py')
    parser.add_argument('--output-dir', '-o', required=True, type=str, help='Directory where store plots and final mlir')
    args = parser.parse_args()

    inputModel = Path(args.path_to_model)
    outputDir = Path(args.output_dir)

    pipeline = Pipeline(inputModel, outputDir, eraseCache=False)
    pipeline.run()

if __name__ == "__main__":
    try:
        main()
        LOG.log(logging.INFO, f"Pipelined succeed! See your results!")
    except Exception as e:
        errMsg = f"Pipeline failed! {e}"
        LOG.log(logging.ERROR, errMsg)
