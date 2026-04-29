# --------------------------------------------------------------------------------------
# Copyright (c) 2026 by Quobly
# --------------------------------------------------------------------------------------
import pytest
from qiskit import QuantumCircuit
from qiskit.compiler import transpile

from quobly_alloy.forge.backend import PioneerEmulator, get_qpu_hw_spec
from quobly_alloy.qpu import QPU


def test_get_qpu_hw_spec_error():
    with pytest.raises(ValueError) as excinfo:
        get_qpu_hw_spec("None")
    assert "Unknown" in str(excinfo.value)


def test_init(emulator):
    assert emulator is not None


def test_execute(emulator, circuit):
    circuit = transpile(circuits=circuit, backend=emulator)
    assert emulator.run_simulation(circuit, 5)


def test_execute_seed_no_superposition(emulator, circuit):
    circuit = transpile(circuits=circuit, backend=emulator)
    r1 = emulator.run_simulation(circuit, 5)
    r2 = emulator.run_simulation(circuit, 5)
    assert list(r1.values()) == list(r2.values())


@pytest.mark.parametrize("qpu", [QPU.PIONEER_P10])
def test_execute_seed_superposition(qpu):
    circuit = QuantumCircuit(3)
    circuit.h(0)
    circuit.h(1)
    circuit.h(2)
    circuit.measure_all()
    backend = PioneerEmulator(qpu, seed=100)
    circuit = transpile(circuits=circuit, backend=backend)
    r1 = backend.run_simulation(circuit, 20)
    r2 = backend.run_simulation(circuit, 20)
    assert list(r1.values()) == list(r2.values())


@pytest.mark.parametrize("qpu", [QPU.PIONEER_P10])
def test_execute_empty_circuit(qpu):
    backend = PioneerEmulator(qpu, seed=100)
    circuit = QuantumCircuit(3)
    circuit = transpile(circuits=circuit, backend=backend)
    r1 = backend.run(circuit, 5)
    assert next(iter(r1.samples.values())) == 5


@pytest.mark.parametrize("nb_qb", [5, 8, 10, 13])
def test_mutiple_qubit(nb_qb):
    backend = PioneerEmulator(QPU.PIONEER_P10, qubits=nb_qb, seed=100)
    circuit = QuantumCircuit(nb_qb)
    circuit = transpile(circuits=circuit, backend=backend)
    r1 = backend.run(circuit, 5)
    assert next(iter(r1.samples.values())) == 5


def test_equivalence_qubits():
    backend = PioneerEmulator(QPU.PIONEER_P10, qubits=10, seed=100)
    circuit = QuantumCircuit(5)
    circuit.h(0)
    circuit.h(1)
    circuit.h(2)
    circuit.measure_all()
    circuit = transpile(circuits=circuit, backend=backend, seed_transpiler=100)
    r1 = backend.run(circuit, 50)

    backend = PioneerEmulator(QPU.PIONEER_P10, seed=100)
    circuit = QuantumCircuit(5)
    circuit.h(0)
    circuit.h(1)
    circuit.h(2)
    circuit.measure_all()
    circuit = transpile(circuits=circuit, backend=backend, seed_transpiler=100)
    r2 = backend.run(circuit, 50)
    assert r1.samples == r2.samples


def test_execute_noiseless(emulator):
    circuit = QuantumCircuit(3)
    circuit.rx(3.14, 0)
    circuit.cx(0, 1)
    circuit.cx(1, 2)
    circuit.measure_all()
    circuit = transpile(circuits=circuit, backend=emulator)
    r1 = emulator.run(circuit, 25, noise=False)
    r2 = emulator.run(circuit, 25)
    assert list(r1.samples.values()) != list(r2.samples.values())

    r1 = emulator.run(circuit, 15, noise=False)
    r2 = emulator.run(circuit, 15, noise=False)
    assert list(r1.samples.values()) == list(r2.samples.values())


def test_too_many_qubit(emulator):
    circuit = QuantumCircuit(550)
    circuit.rx(3.14, 1)
    circuit.measure_all()
    with pytest.raises(ValueError) as excinfo:
        emulator.run_simulation(circuit, 1)
    assert "is too large for the qpu" in str(excinfo.value)


def test_not_enough_shots(emulator):
    circuit = QuantumCircuit(5)
    circuit.rx(3.14, 1)
    circuit.measure_all()

    circuit = transpile(circuits=circuit, backend=emulator)
    with pytest.raises(ValueError) as excinfo:
        emulator.run_simulation(circuit, 0)
    assert "The number of shots" in str(excinfo.value)


def test_bad_circuit(emulator, circuit):
    with pytest.raises(ValueError) as excinfo:
        emulator.run_simulation(circuit, 3)
    assert "is not present" in str(excinfo.value)


def test_max_circuit(emulator):
    assert emulator.max_circuits() == 1
