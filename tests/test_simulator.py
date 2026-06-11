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
    assert emulator.run_simulation(circuit, 5)


def test_execute_seed_no_superposition(emulator, circuit):
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
    r1 = backend.run_simulation(circuit, 20)
    r2 = backend.run_simulation(circuit, 20)
    assert list(r1.values()) == list(r2.values())


@pytest.mark.parametrize("qpu", [QPU.PIONEER_P10])
def test_execute_empty_circuit(qpu):
    backend = PioneerEmulator(qpu, seed=100)
    circuit = QuantumCircuit(3)
    r1 = backend.run(circuit, 5)
    assert next(iter(r1.samples.values())) == 5


@pytest.mark.parametrize("nb_qb", [5, 8, 10, 13])
def test_mutiple_qubit(nb_qb):
    backend = PioneerEmulator(QPU.PIONEER_P10, qubits=nb_qb, seed=100)
    circuit = QuantumCircuit(nb_qb)
    r1 = backend.run(circuit, 5)
    assert next(iter(r1.samples.values())) == 5


def test_equivalence_qubits():
    backend = PioneerEmulator(QPU.PIONEER_P10, qubits=10, seed=100)
    circuit = QuantumCircuit(5)
    circuit.h(0)
    circuit.h(1)
    circuit.h(2)
    circuit.measure_all()
    r1 = backend.run(circuit, 50)

    backend = PioneerEmulator(QPU.PIONEER_P10, seed=100)
    circuit = QuantumCircuit(5)
    circuit.h(0)
    circuit.h(1)
    circuit.h(2)
    circuit.measure_all()
    r2 = backend.run(circuit, 50)
    assert r1.samples == r2.samples


def test_non_equivalence_qubits():
    backend = PioneerEmulator(QPU.PIONEER_P10)
    circuit = QuantumCircuit(5)
    circuit.h(0)
    circuit.h(1)
    circuit.h(2)
    circuit.measure_all()
    r1 = backend.run(circuit, 50)

    backend = PioneerEmulator(QPU.PIONEER_P10)
    circuit = QuantumCircuit(5)
    circuit.h(0)
    circuit.h(1)
    circuit.h(2)
    circuit.measure_all()
    r2 = backend.run(circuit, 50)
    assert r1.samples != r2.samples


def test_execute_noiseless(emulator):
    circuit = QuantumCircuit(3)
    circuit.rx(3.14, 0)
    circuit.cx(0, 1)
    circuit.cx(1, 2)
    circuit.measure_all()
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

    with pytest.raises(ValueError) as excinfo:
        emulator.run_simulation(circuit, 0)
    assert "The number of shots" in str(excinfo.value)


def test_max_circuit(emulator):
    assert emulator.max_circuits() == 1


@pytest.mark.parametrize("nb_qb", [2, 3, 5])
def test_noiseless_ghz_is_clean(nb_qb):
    """A noiseless GHZ circuit must only ever measure all-zeros or all-ones.

    Regression test: ``run_simulation`` must echo every ``rzz`` gate before pulse
    conversion. Otherwise each ``rzz`` leaks a large spurious single-qubit Z (Stark)
    phase from the detuning pulses and the prepared state collapses into a spread of
    incorrect bitstrings (GHZ-2 fidelity was ~0.64 before the fix).
    """
    backend = PioneerEmulator(QPU.PIONEER_P10, qubits=nb_qb, seed=100)
    circuit = QuantumCircuit(nb_qb)
    circuit.h(0)
    for target in range(1, nb_qb):
        circuit.cx(0, target)
    circuit.measure_all()

    counts = backend.run_simulation(circuit, 50, noise=False)

    expected = {"0" * nb_qb, "1" * nb_qb}
    assert set(counts) <= expected, (
        f"noiseless GHZ produced non-GHZ outcomes: {set(counts) - expected}"
    )
    assert sum(counts.values()) == 50


def test_time_duration():
    emu = PioneerEmulator(QPU.PIONEER_P10, qubits=11, seed=1)
    qc = QuantumCircuit(11)
    qc.h(0)
    for k in range(1, 11):
        qc.cx(0, k)
    tc = transpile(qc, backend=emu, optimization_level=1)

    emu.run_simulation(tc, 5)


def test_seed_regression(emulator):
    circuit = QuantumCircuit(3)
    circuit.rx(3.14, 0)
    circuit.cx(0, 1)
    circuit.cx(1, 2)
    circuit.measure_all()
    r1 = emulator.run(circuit, 25)
    assert len(r1.samples.values()) > 1
