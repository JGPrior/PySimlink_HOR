import os
import sys

from pysimlink.lib.model_paths import ModelPaths
from pysimlink.utils import annotation_utils as anno


class Model:
    """
    Instance of the simulink mode. This class compiles and imports
    the model once built. You can have multiple instances of the same
    model in one python runtime (although multithreaded *compiling* is not tested).
    """

    model_paths: "anno.ModelPaths"
    compiler: "anno.Compiler"

    def __init__(  # pylint: disable=R0913
        self,
        model_name: str,
        path_to_model: str,
        compile_type: str = "grt",
        suffix: str = "rtw",
        tmp_dir: str = None,
        force_rebuild: bool = False,
    ):

        self.model_paths = ModelPaths(path_to_model, model_name, compile_type, suffix, tmp_dir)
        self.compiler = self.model_paths.compiler_factory()

        ## Check need to compile
        if force_rebuild or self.compiler.needs_to_compile():
            ## Need to compile
            self.compiler.compile()

        sys.path.append(os.path.join(self.model_paths.tmp_dir, "build"))

        import model_interface_c  # pylint: disable=C0415,E0401

        self._model = model_interface_c.Model(self.model_paths.root_model_name)

    def get_params(self) -> "list[anno.ModelInfo]":
        """
        Return an instance of all parameters, blocks, and signals in the _model

        See `lib.model_utils.print_all_params` for iterating and printing the contents of this object

        Returns:
            list[ModelInfo]: List of model info, one for each model (if reference models present). One ModelInfo if no reference models
        """
        return self._model.get_params()

    def reset(self):
        """
        Reset the simulink model. This clears all signal values and reinstantiates the model.
        """
        self._model.reset()

    def step(self, iterations: int = 1):
        """
        Step the simulink model


        Args:
            iterations: Number of timesteps to step internally.
                `model.step(10)` is equivalent to calling `for _ range(10): model.step(1)` functionally, but compiled.

        Raises:
            RuntimeError: If the model encounters an error (these will be raised from simulink). Most commonly, this
                will be `simulation complete`.

        """
        self._model.step(iterations)

    def tFinal(self) -> float:
        """
        Get the final timestep of the model.

        Returns:
            float: Final timestep of the model (seconds from zero).
        """
        return self._model.tFinal()

    def step_size(self) -> float:
        """
        Get the step size of the model

        Returns:
            float: step size of the fixed step solver.
        """
        return self._model.step_size()

    def set_tFinal(self, tFinal: float):
        """
        Change the final timestep of the model

        Args:
            tFinal: New final timestep of the model (seconds from zero).

        Raises:
            ValueError: if tFinal is <= 0
        """
        if tFinal <= 0:
            raise ValueError("new tFinal must be > 0")
        self._model.set_tFinal(tFinal)

    def get_signal(self, block_path, model_name=None, sig_name="") -> "np.ndarray":
        """
        Get the value of a signal

        Args:
            block_path: Path to the originating block
            sig_name: Name of the signal
            model_name: Name of the model provided by "print_all_params". None if there are no model references.

        Returns:
            Value of the signal at the current timestep
        """
        model_name = self.model_paths.root_model_name if model_name is None else model_name
        return self._model.get_signal(model_name, block_path, sig_name)

    def get_models(self) -> "list[str]":
        """
        Gets a list of all reference models (and the root model) in this model.

        Returns:
            list of paths, one for each model
        """
        return self._model.get_models()
