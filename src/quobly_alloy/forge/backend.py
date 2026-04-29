# --------------------------------------------------------------------------------------
# Copyright (c) 2026 by Quobly
# --------------------------------------------------------------------------------------
"""Module containing the Quobly Noise Accurate Simulator"""

from qiskit import QuantumCircuit
from qiskit.providers import Job, Options
from qiskit.providers.fake_provider import GenericBackendV2
from qiskit.transpiler import CouplingMap, Target
from qiskit_aer import AerSimulator
from spin_pulse import PulseCircuit

from quobly_alloy.qpu import QPU


def get_qpu_hw_spec(
    qpu: QPU, qubits: int | None = None, seed: int | None = None
) -> tuple[Target, Options, list[str], CouplingMap]:
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
            from quobly_alloy.forge.pioneer_p10 import generate_environment

            return generate_environment(qubits, seed)
        case _:
            raise ValueError(f"Unknown qpu {qpu}")


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

    _target: Target
    """Backend target, qiskit framework specification"""
    _options: Options
    """Qiskit backend options, qiskit framework specification"""
    native_gate: list[str]
    """List of bakcend's native gate"""
    _coupling_map: CouplingMap
    """Backend coupling map, qiskit framework specification"""
    _seed: int | None
    """Seed"""

    def __init__(
        self, target_qpu: QPU, qubits: int | None = None, seed: int | None = None
    ):
        if target_qpu not in [QPU.PIONEER_P10]:
            raise ValueError(f"{target_qpu} is not supported by PioneerEmulator.")
        self._target, self._options, self.native_gate, self._coupling_map = (
            get_qpu_hw_spec(target_qpu, qubits=qubits, seed=seed)
        )
        self._seed = seed

    @property
    def target(self) -> Target:
        """Return the backend target, qiskit framework specification"""
        return self._target

    def max_circuits(self) -> int:
        """Return the max number of parallel circuit the backend can run,
        qiskit framework specification
        """
        return 1

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

        for gate in circuit.data:
            if (
                not (gate.name in self.native_gate and gate.is_standard_gate())
                and gate.name != "barrier"
                and gate.name != "measure"
            ):
                raise ValueError(
                    f"{gate.name} is not present in the native set {self.native_gate}."
                )
        if self._seed is not None:
            self.options.get("env").seed = self._seed
        self._state_vector_simulator = AerSimulator(
            method="density_matrix",
            matrix_product_state_max_bond_dimension=int(2e10),
            matrix_product_state_truncation_threshold=10e-3,
            seed_simulator=self._seed,
        )
        res: dict[str, int] = {}

        pulse_circ: PulseCircuit = PulseCircuit.from_circuit(
            circ=circuit,
            hardware_specs=self.options.get("specs"),
            exp_env=self.options.get("env") if noise else None,
        )
        for shot in range(shots):
            # Each shot need to regenerate the noise with spin-pulse attach_time_traces
            circ = pulse_circ.to_circuit(True)
            result = (
                self._state_vector_simulator.run([(circ)], shots=1).result().get_counts()
            )
            for state, sample in result.items():
                k_sample = state.split(" ")[0]
                if k_sample in res:
                    res[k_sample] += sample
                else:
                    res[k_sample] = sample

            if noise:
                pulse_circ.attach_time_traces(self.options.get("env"))
            if self._seed:  # The seed is changed in a deterministic way
                # to simulate time going forward. the 70 factor is arbitrary
                self._state_vector_simulator = AerSimulator(
                    method="density_matrix",
                    matrix_product_state_max_bond_dimension=int(2e10),
                    matrix_product_state_truncation_threshold=10e-3,
                    seed_simulator=self._seed + 70 * shot,
                )

        logical_q: dict[str, int] = {}
        for key in res:
            logical_q[pulse_circ.get_logical_bitstring(key)] = res[key]
        return dict(
            sorted(logical_q.items(), key=lambda key: int(key[0], max(2, len(key[0]))))
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
