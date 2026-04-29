import pytest
from qiskit import QuantumCircuit

from quobly_alloy.forge import PioneerEmulator
from quobly_alloy.qpu import QPU


@pytest.fixture()
def circuit() -> QuantumCircuit:
    circuit = QuantumCircuit(2)
    circuit.cx(0, 1)
    return circuit


@pytest.fixture()
def emulator() -> PioneerEmulator:
    return PioneerEmulator(QPU.PIONEER_P10, seed=100)
