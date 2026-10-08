# Quobly forge emulator
<img src="https://github.com/quobly-sw/.github/raw/main/Quobly-longeur.png" width=200>

The Quobly-alloy SDK adresses Quobly QPUs such as Alloy Pioneer and their emulators using the forge module.

## Installation

You can install Quobly Alloy with

```bash
pip install quobly-alloy
```

## Use

The minimal program to call an emulator such as the Pioneer emulator is

``` python
from qiskit import QuantumCircuit
from quobly_alloy.forge import PioneerEmulator
from quobly_alloy import QPU

circuit = QuantumCircuit(2)
circuit.rx(1, 1)
circuit.rz(1, 0)
circuit.rx(1, 0)
circuit.rzz(1, 0, 1)
circuit.measure_all()

emulator = PioneerEmulator(QPU.PIONEER_P10)
result = emulator.run_simulation(circuit,shots=1000)
print(result)

```

This code first create a circuit of 2 qubits, then simulate it on the PIONEER_P10 machine using run simulation.
The methods PioneerEmualtor.run_simulation simulate a circuit for one ten shots.
This return a dictionary[str,int] composed of key being the bitstring of the machine and values being the number of time the bitstring appears.

One can also use the function run, that return a QuoblyJob object (inheriting from Qiskit.Job) with the methods QuoblyJob.result that return the same result as run_simulation. This methods exist for adherence
to qiskit framework.

Furthermore, one can fix a seed using

```python
emulator = PioneerEmulator(QPU.PIONEER_P10,seed = 100)
result = emulator.run_simulation(circuit=circuit,shots=1000)
```

In addition one can select the number of core used for the emulation with (note that max_used_core is capped by the number of core of your hardware):

```python
emulator = PioneerEmulator(QPU.PIONEER_P10,max_used_core=6)
result = emulator.run_simulation(circuit=circuit,shots=1000,noise=False)
```

You can also remove the injected noise using:

```python
emulator = PioneerEmulator(QPU.PIONEER_P10)
result = emulator.run_simulation(circuit=circuit,shots=1000,noise=False)
```

Finally you can change the number of qubits using:

```python
emulator = PioneerEmulator(QPU.PIONEER_P10,qubits = 5)
result = emulator.run_simulation(circuit=circuit)
```

[!CAUTION] The number of possible qubits is dependant of the computer memory size.

## Disk-backed noise histories

*Documentation added by Kenny Heitritter in 2026.*

With a SpinPulse build containing
[disk-backed pink-noise support](https://github.com/quobly-sw/SpinPulse/pull/26),
long experiments can keep their complete noise histories on disk:

```python
emulator = PioneerEmulator(
    QPU.PIONEER_P10,
    qubits=10,
    seed=42,
    max_used_core=1,
    noise_directory="/path/to/job-scratch",
)
result = emulator.run_simulation(circuit, shots=1000)
```

The directory must already exist on a disk filesystem. Use a private job
directory and clean it after the job; forced termination can leave temporary
files behind. RAM-backed filesystems such as tmpfs do not save memory.
SpinPulse preserves the complete trace duration and correlations across shots,
using float64 samples. Disk usage grows with trace duration and the number of
qubit and coupling histories. Memory still depends on the constituent FFT sizes
and concurrent workers. Omitting `noise_directory` retains in-memory storage;
`noise=False` does not create noise files.

The new option requires the SpinPulse change above. Before releasing this draft,
replace the CI preview dependency with that published version and raise the
runtime dependency minimum accordingly.

## Transpilation

The transpilation is done internally by the backend.

## Using qiskit-aer-gpu for cuda 12

As of no, qiskit 2.x does not support cuda 12, but conda [does](https://anaconda.org/channels/conda-forge/packages/qiskit-aer/files?file_q=cuda12). 

On your conda environment you can install the correct package using

```bash
conda install -c conda-forge "qiskit-aer=0.17.2=*cuda*" cuda-version=12
```
You can then check if the gpu is correctly found using:

```bash
python -c "from qiskit_aer import AerSimulator; print('GPU' in AerSimulator().available_devices())"
```

You can then use the backend as normal, the backend prioritize the GPU device if found. 
You can force the use of the CPU using:

```python
emulator = PioneerEmulator(QPU.PIONEER_P10,always_use_cpu = True)
```
