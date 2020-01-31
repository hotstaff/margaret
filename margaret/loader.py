# coding: UTF-8
# Copyright 2019 Hideto Manjo.
#
# Licensed under the MIT License

"""Loader module."""
import onnx

class OnnxLoader:
    """Onnx Loader.

    onnx_loader reads a file written in onnx format and prepares it
    for execution. Loader basically provides only __run __() as
    the only method.
    """

    def __init__(self, onnx_model_pb_path, backend="caffe2"):
        """Init."""
        if backend == "caffe2":
            from caffe2.python.onnx.backend import prepare
        else:
            raise RuntimeError("Backend {} is a non-configurable value."
                               .format(backend))

        onnx_model = onnx.load(onnx_model_pb_path)
        self.model = prepare(onnx_model)

    def __call__(self, inputs):
        """Call."""
        return self.model.run(inputs)
