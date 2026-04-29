# --------------------------------------------------------------------------------------
# Copyright (c) 2026 by Quobly
# --------------------------------------------------------------------------------------
from qiskit.providers import Options
from qiskit.transpiler import CouplingMap, Target

from quobly_alloy import QPU
from quobly_alloy.forge.backend import get_qpu_hw_spec


# This test read the entire QPUS namespace and check the existence of every qpu
# If it fail it mean the failed qpu_id associated qpu does not exist.
def test_qpu_exist():
    for qpu_id in QPU:
        res = get_qpu_hw_spec(qpu_id)
        assert isinstance(res[0], Target)
        assert isinstance(res[1], Options)
        assert isinstance(res[2], list)
        assert isinstance(res[3], CouplingMap)
