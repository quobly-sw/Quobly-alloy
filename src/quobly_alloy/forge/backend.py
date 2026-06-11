# --------------------------------------------------------------------------------------
# Copyright (c) 2026 by Quobly
# --------------------------------------------------------------------------------------
"""Module containing the Quobly Noise Accurate Simulator"""

from typing import Callable

from qiskit import QuantumCircuit
from qiskit.providers import Job, Options
from qiskit.providers.fake_provider import GenericBackendV2
from qiskit_aer import AerSimulator
from spin_pulse import PulseCircuit

from quobly_alloy.qpu import QPU


def get_qpu_hw_spec(
    qpu: QPU, qubits: int | None = None, seed: int | None = None
) -> tuple[Options, int, list[str], list, Callable]:
    """
    Return a tuple describing the configured target qpu.

    Args:
        qpu (QPU): target qpu
        qubits (int | None): Number of qubits for the qpu, set to none for default value.
        seed (int | None): Seed for the environment. Set to None for no seed.
    Returns:
        tuple[HardwareSpecs, ExperimentalEnvironment, CouplingMap, list[str], CouplingMap]

    """
    match qpu:
        case QPU.PIONEER_P10:
            from quobly_alloy.forge.pioneer_p10 import (
                attach_env_to_circuit,
                generate_environment,
            )

            return (*generate_environment(qubits, seed), attach_env_to_circuit)
        case _:
            raise ValueError(f"Unknown qpu {qpu}")


def _seed_continuation(old_seed: int) -> int:
    """Return a new seed following an arithmetic series."""
    return old_seed + 70


class QuoblyJob(Job):
    """
    Qiskit job implementation for qiskit.

    """

    samples: dict[str, int]
    """Sampled state of the circuit."""

    def __init__(self, sample: dict[str, int]):
        self.samples = sample
        super().__init__()

    def result(self) -> dict[str, int]:
        """Return a dictionary [bitstring(str), sampling(int)] of sampled state

        Return:
            dict[str,int]: measured value

        """
        return self.samples


class PioneerEmulator(GenericBackendV2):
    """Pioneer Quobly Hardware Qpu emulator using Spin Pulse."""

    _options: Options
    """Qiskit backend options, qiskit framework specification"""
    _seed: int | None
    """Seed"""
    _always_use_cpu: bool
    """Force the backend to always use the CPU qiskit aer, otherwise the backend
    will use the gpu if possible."""
    _env_generative_function: Callable
    """Function to generate and attach the environment to the pulse circuit."""

    def __init__(
        self,
        target_qpu: QPU,
        qubits: int | None = None,
        seed: int | None = None,
        always_use_cpu: bool = False,
    ):
        self._always_use_cpu = always_use_cpu
        if target_qpu not in [QPU.PIONEER_P10]:
            raise ValueError(f"{target_qpu} is not supported by PioneerEmulator.")
        options, nb_qbit, basis_gates, coupling_map, self._env_generative_function = (
            get_qpu_hw_spec(target_qpu, qubits=qubits, seed=seed)
        )
        self._seed = seed
        super().__init__(
            num_qubits=nb_qbit, basis_gates=basis_gates, coupling_map=coupling_map
        )
        self._options = options

    def max_circuits(self) -> int:
        """Return the max number of parallel circuit the backend can run,
        qiskit framework specification
        """
        return 1

    def _get_state_vector_simulator(self, seed: int | None) -> AerSimulator:
        """Return an AerSimulator using the GPU if available, otherwise a CPU one."""
        if "GPU" in AerSimulator().available_devices():
            return AerSimulator(
                method="statevector",
                device="GPU",
                seed_simulator=seed,
            )
        else:
            return AerSimulator(
                method="statevector",
                seed_simulator=seed,
            )

    def run_simulation(
        self,
        circuit: QuantumCircuit,
        shots: int,
        noise: bool = True,
    ) -> dict[str, int]:
        """Start the job on the sampler, return a dictionary of measured state.

        Args:
            circuit (QuantumCircuit): circuit to execute.
            shots (int): Shots is the number of time the circuit shall be run
            noise (bool) : Activate the noise environment.
        Returns:
            dict[str,int]: dictionary[bitstring;sampled value] of measured state
                of the logical qubits.

        """
        if self.num_qubits < circuit.num_qubits:
            raise ValueError(
                f"The number of qubits {circuit.num_qubits} "
                f"is too large for the qpu ({self.num_qubits} qubits)."
            )
        if shots < 1:
            raise ValueError(
                f"The number of shots {shots} is too small for the qpu (1 minimum)."
            )

        self._state_vector_simulator = self._get_state_vector_simulator(self._seed)

        hardware_spec = self.options.get("specs")
        pulse_circ: PulseCircuit = PulseCircuit.from_circuit(
            circ=hardware_spec.gate_transpile(circuit),
            hardware_specs=self.options.get("specs"),
            exp_env=None,
        )
        if noise:
            env = self._env_generative_function(
                self.options.get("specs"), pulse_circ, shots, self._seed
            )
        else:
            env = None
        result = pulse_circ.run_experiment(
            env,
            self._state_vector_simulator,
            shots,
            False,
            _seed_continuation if self._seed else None,
        )

        qreg = {}
        for key in result:
            qreg[key.split(" ")[0]] = result[key]
        return dict(
            sorted(qreg.items(), key=lambda key: int(key[0], max(2, len(key[0]))))
        )

    def run(
        self,
        circuit: QuantumCircuit,
        shots: int,
        noise: bool = True,
    ) -> QuoblyJob:
        """Start the job on the sampler, return a QuoblyJob.

        Args:
            circuit (QuantumCircuit): circuit to execute.
            shots (int): number of shots for simulating the circuit.
            noise (bool): If the noise is active
        Returns:
            QuoblyJob: Job containing the result.

        """
        return QuoblyJob(self.run_simulation(circuit=circuit, shots=shots, noise=noise))
