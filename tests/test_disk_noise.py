# Copyright (c) 2026 by Quobly.
# Added by Kenny Heitritter in 2026 to verify disk-backed noise integration.
from pathlib import Path

import numpy as np
import pytest
from qiskit import QuantumCircuit
from spin_pulse import PulseCircuit

from quobly_alloy import QPU
from quobly_alloy.forge import PioneerEmulator


def circuit():
    value = QuantumCircuit(2)
    value.rx(1, 1)
    value.rz(1, 0)
    value.rx(1, 0)
    value.rzz(1, 0, 1)
    value.measure_all()
    return value


def test_disk_environment_matches_default(tmp_path):
    memory = PioneerEmulator(QPU.PIONEER_P10, qubits=2, seed=42)
    disk = PioneerEmulator(QPU.PIONEER_P10, qubits=2, seed=42, noise_directory=tmp_path)
    specs = memory.options.get("specs")
    pulse = PulseCircuit.from_circuit(specs.gate_transpile(circuit()), specs)
    expected = memory._env_generative_function(specs, pulse, 100, 42)
    pulse.t_lab = 0
    actual = disk._env_generative_function(specs, pulse, 100, 42)
    assert actual.duration == expected.duration
    for left, right in zip(
        expected.time_traces + expected.time_traces_coupling,
        actual.time_traces + actual.time_traces_coupling,
        strict=True,
    ):
        assert isinstance(right.values, np.memmap)
        assert Path(right.values.filename).is_relative_to(tmp_path)
        np.testing.assert_array_equal(left.values, right.values)


def test_documented_thousand_shot_circuit_has_same_seeded_counts(tmp_path):
    program = circuit()
    expected = PioneerEmulator(QPU.PIONEER_P10, qubits=2, seed=42).run_simulation(
        program, shots=1000
    )
    actual = PioneerEmulator(
        QPU.PIONEER_P10, qubits=2, seed=42, noise_directory=tmp_path
    ).run_simulation(program, shots=1000)
    assert sum(actual.values()) == 1000
    assert actual == expected


def test_noiseless_execution_does_not_access_noise_directory(tmp_path):
    directory = tmp_path / "does-not-exist"
    emulator = PioneerEmulator(
        QPU.PIONEER_P10, qubits=2, seed=42, noise_directory=directory
    )
    counts = emulator.run_simulation(circuit(), shots=20, noise=False)
    assert sum(counts.values()) == 20
    assert not directory.exists()


def test_empty_noise_directory_does_not_use_working_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    emulator = PioneerEmulator(QPU.PIONEER_P10, qubits=2, noise_directory="")
    with pytest.raises(ValueError, match="noise_directory must name"):
        emulator.run_simulation(circuit(), shots=1)
    assert list(tmp_path.iterdir()) == []
