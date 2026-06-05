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
circuit.rx(3.14, 1)
circuit.rz(3.14 / 3, 0)
circuit.rx(3.14 / 3, 0)
circuit.rzz(0, 0, 1)
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

The backend can also be use in the qiskit transpilation stack:

```python
from qiskit import QuantumCircuit, transpile
from quobly_alloy import QPU
from quobly_alloy.forge import PioneerEmulator
from spin_pulse import PulseCircuit

backend = PioneerEmulator(QPU.PIONEER_P10)
circuit = QuantumCircuit(3)
circuit.cx(0,1)
circuit.cx(0,2)
transpiled_circuit = transpile(qc, backend=emu, optimization_level=1)
result = emulator.run_simulation(circuit=transpiled_circuit)
```
For using the backend with the qiskit transpiler, we recommend fixing the optimization_level to 0 or 1 for a quick transpilation.