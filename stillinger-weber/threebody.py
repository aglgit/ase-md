import os
import numpy as np
import matplotlib.pyplot as plt
import ase.io
from ase import Atom, Atoms, units
from asap3 import OpenKIMcalculator
from amp import Amp

if not os.path.exists("amp.amp"):
    print("No trained AMP calculator!")
else:
    amp_calc = Amp.load("amp.amp")

calc = OpenKIMcalculator("SW_StillingerWeber_1985_Si__MO_405512056662_005")
atoms = Atoms([Atom("Si", (1, 2, 3)), Atom("Si", (1, 3, 2)), Atom("Si", (2, 3, 1))])
atoms.set_calculator(calc)

dist = np.linspace(0.0, 1.0, 1000)
pot = np.zeros_like(dist)

for i, r in enumerate(dist):
    print(atoms.positions)
    pot[i] = atoms.get_potential_energy()

plt.plot(dist, pot)
plt.show()
