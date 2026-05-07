# --------------------------------------------------------------------------------------
# Copyright (c) 2026 by Quobly
# --------------------------------------------------------------------------------------
"""Pioneer-P10 10 qubits hardware device description."""

from typing import Final

import numpy as np
from qiskit.circuit import Measure
from qiskit.circuit.library import RXGate, RYGate, RZGate, RZZGate
from qiskit.providers import Options
from qiskit.transpiler import CouplingMap, InstructionProperties, Target
from spin_pulse import ExperimentalEnvironment, HardwareSpecs, Shape
from spin_pulse.environment.noise import NoiseType

_DEFAULT_QUBIT: Final[int] = 10
"""Max default number of qubits in the QPU"""

_NATIVE_GATE_SET: Final[list[str]] = ["rx", "rz", "ry", "rzz"]
"""Native gate set of the QPU"""

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
) -> tuple[Target, Options, list[str], CouplingMap]:
    """Generate the qpu environnement and target.

    Args:
        nb_qubit (int | None): Number of qubit of the qpu, set to None to use
        the DEFAULT_QUBIT of the QPU.

    """
    if nb_qubit is None:
        nb_qubit = _DEFAULT_QUBIT

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

    env: ExperimentalEnvironment = ExperimentalEnvironment(
        specs,
        noise_type=NoiseType.PINK,
        T2S=_T2S,
        TJS=_TJS,
        duration=2**20,
        segment_duration=2**20,
        only_idle=False,
        seed=seed,
    )

    coupling: list[list[int]] = []
    for qubit in range(nb_qubit - 1):
        coupling.append([qubit, qubit + 1])
    for qubit in range(nb_qubit - 1, 0, -1):
        coupling.append([qubit, qubit - 1])

    coupling_map: CouplingMap = CouplingMap(coupling)
    """Coupling map of the QPU (LINEAR)"""

    target = Target(num_qubits=nb_qubit)

    rx_ry_qubit_target = {  # Qubit Targeting for rx and ry gate
        (q,): InstructionProperties(duration=0.000001) for q in range(nb_qubit)
    }

    rz_qubit_target = {  # Qubit Targeting for rz gate
        (q,): InstructionProperties(duration=0.0000001) for q in range(nb_qubit)
    }

    target.add_instruction(RXGate(theta=0), rx_ry_qubit_target)
    target.add_instruction(RYGate(theta=0), rx_ry_qubit_target)
    target.add_instruction(RZGate(phi=0), rz_qubit_target)
    target.add_instruction(Measure(), rx_ry_qubit_target)

    two_qubit_target = {  # Qubit Targeting for rzz and ry gate
        (ctrl, tgt): InstructionProperties(duration=0.000003)
        for ctrl, tgt in coupling_map
    }
    target.add_instruction(RZZGate(theta=0), two_qubit_target)

    option = Options(specs=specs, env=env)

    return target, option, _NATIVE_GATE_SET, coupling_map
