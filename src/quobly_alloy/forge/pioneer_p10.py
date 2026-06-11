# --------------------------------------------------------------------------------------
# Copyright (c) 2026 by Quobly
# --------------------------------------------------------------------------------------
"""Pioneer-P10 10 qubits hardware device description."""

from typing import Final

import numpy as np
from qiskit.providers import Options
from spin_pulse import ExperimentalEnvironment, HardwareSpecs, PulseCircuit, Shape
from spin_pulse.environment.noise import NoiseType

_DEFAULT_QUBIT: Final[int] = 10
"""Max default number of qubits in the QPU"""

_QUBIT_MAX: Final[int] = 29
"""Max number of qubit for this family."""

_t_z = 100
_t_x = 1_000
_t_zz = 1_000

_coeff_duration = 5
_ramp_duration = 5

_sigma_z = _t_z / _coeff_duration
_sigma_x = _t_x / _coeff_duration
_sigma_zz = _t_zz / _coeff_duration

_delta = np.pi / (np.sqrt(2 * np.pi) * _sigma_z)
_B0 = np.pi / (np.sqrt(2 * np.pi) * _sigma_x)
_J_coupling = np.pi / (2 * np.sqrt(2 * np.pi) * _sigma_zz)
_T2S = 10000
_TJS = 5_000


def generate_environment(
    nb_qubit: int | None, seed: int | None = None
) -> tuple[Options, int, list[str], list]:
    """Generate the qpu environnement and target.

    Args:
        nb_qubit (int | None): Number of qubit of the qpu, set to None to use
        the DEFAULT_QUBIT of the QPU.

    """
    if nb_qubit is None:
        nb_qubit = _DEFAULT_QUBIT
    if nb_qubit > _QUBIT_MAX:
        raise ValueError(f"Max number of qubit for Pioneer is {_QUBIT_MAX} qubits.")
    # Spin pulse hardware specs & environnement
    specs: HardwareSpecs = HardwareSpecs(
        num_qubits=nb_qubit,
        B_field=_B0,
        delta=_delta,
        J_coupling=_J_coupling,
        rotation_shape=Shape.GAUSSIAN,
        ramp_duration=_ramp_duration,
        coeff_duration=_coeff_duration,
    )

    option = Options(specs=specs)

    return option, nb_qubit, specs.basis_gates, specs.coupling_map


def attach_env_to_circuit(
    specs, circuit: PulseCircuit, shots_number: int, seed: int | None
) -> ExperimentalEnvironment:
    duration = circuit.duration * max(10, shots_number)
    if duration % 2 == 1:  # Odd value are not accepted by spin pulse.
        duration += 1
    if duration == 0:  # Edge case of empty circuit
        duration = 2
    env: ExperimentalEnvironment = ExperimentalEnvironment(
        specs,
        noise_type=NoiseType.PINK,
        T2S=_T2S,
        TJS=_TJS,
        duration=duration,
        segment_duration=duration,
        only_idle=False,
        seed=seed,
    )
    circuit.attach_time_traces(env)
    return env
