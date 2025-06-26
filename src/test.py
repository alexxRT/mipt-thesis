import tensorflow as tf
import numpy as np
from tensorflow.python.profiler import profiler_v2 as profiler
import argparse
from pathlib import Path


class SimpleModel(tf.Module):

    @tf.function(input_signature=[
        tf.TensorSpec(shape=[1000, 1000], dtype=tf.float32),
        tf.TensorSpec(shape=[1000, 1000], dtype=tf.float32),
        tf.TensorSpec(shape=[1000, 1000], dtype=tf.float32)
    ])
    def forward(self, a, b, c):

        matmul_result = tf.linalg.matmul(a, b)
        add_result = tf.add(matmul_result, c)
        relu_result = tf.nn.relu(add_result)
        reduce_sum_result = tf.reduce_sum(relu_result)

        return reduce_sum_result


def profile_tf_operations(logDir: Path):
    a = tf.constant(np.random.random((1000, 1000)), dtype=tf.float32)
    b = tf.constant(np.random.random((1000, 1000)), dtype=tf.float32)
    c = tf.constant(np.random.random((1000, 1000)), dtype=tf.float32)

    model = SimpleModel()

    profiler.start(str(logDir))
    try:
        with tf.name_scope("test_operations"):
            model.forward(a, b, c)
    finally:
        profiler.stop()


def main():
    parser = argparse.ArgumentParser(description="Collect model profile")
    parser.add_argument('--logdir', '-l', required=True, type=str, help='Directory where to save profile and models graph')
    args = parser.parse_args()

    logDir = Path(args.logdir)

    # collect profile
    profile_tf_operations(logDir)

    # save models graph
    model: SimpleModel = SimpleModel()
    tf.saved_model.save(model, logDir / "saved_model")

if __name__ == "__main__":
    main()
