import sys
import numpy as np
from asap3 import EMT
from amp.descriptor.cutoffs import Cosine, Polynomial
from amp.descriptor.gaussian import make_symmetry_functions

sys.path.insert(1, "../tools")

from create_trajectory import TrajectoryBuilder
from training import Trainer


if __name__ == "__main__":
    system = "copper"
    size = (2, 2, 2)
    temp = 500

    n_train = int(8e4)
    n_test = int(2e4)
    save_interval = 100

    max_steps = int(2e3)
    convergence = {"energy_rmse": 1e-16, "force_rmse": None, "max_steps": max_steps}
    force_coefficient = None
    hidden_layers = (10, 10)
    activation = "tanh"
    cutoff = Cosine(6.0)

    trjbd = TrajectoryBuilder()
    calc = EMT()
    train_atoms = trjbd.build_atoms(system, size, temp, calc)
    calc = EMT()
    test_atoms = trjbd.build_atoms(system, size, temp, calc)

    train_traj = "training.traj"
    test_traj = "test.traj"
    steps, train_traj = trjbd.integrate_atoms(
        train_atoms, train_traj, n_train, save_interval
    )
    steps, test_traj = trjbd.integrate_atoms(
        test_atoms, test_traj, n_test, save_interval
    )

    trn = Trainer(
        convergence=convergence,
        force_coefficient=force_coefficient,
        hidden_layers=hidden_layers,
        activation=activation,
        cutoff=cutoff,
    )

    elements = ["Cu"]
    num_radial = [2, 3, 4, 5, 6]
    num_zetas = [1, 1, 1, 1, 2]
    gammas = [1.0, -1.0]
    symm_funcs = {"Default": None}
    for i in range(len(num_radial)):
        nr = num_radial[i]
        nz = num_zetas[i]

        radial_etas = np.logspace(np.log10(1.0), np.log10(20.0), nr)
        centers = np.zeros(nr)
        G2_uncentered = make_symmetry_functions(
            elements=elements, type="G2", etas=radial_etas, centers=centers
        )

        radial_etas = np.logspace(np.log10(5.0), np.log10(20.0), nr)
        centers = np.linspace(1.0, cutoff.Rc - 1.0, nr)
        G2_centered = make_symmetry_functions(
            elements=elements, type="G2", etas=radial_etas, centers=centers
        )

        G2 = G2_uncentered + G2_centered

        angular_etas = np.linspace(0.05, 1.0, 8)
        zetas = [4 ** i for i in range(nz)]
        G4 = make_symmetry_functions(
            elements=elements,
            type="G4",
            etas=angular_etas,
            zetas=zetas,
            gammas=[1.0, -1.0],
        )
        G5 = make_symmetry_functions(
            elements=elements,
            type="G5",
            etas=angular_etas,
            zetas=zetas,
            gammas=[1.0, -1.0],
        )

        label_G4 = "Gs-{}-{}-{}".format(nr, nz, "G4")
        label_G5 = "Gs-{}-{}-{}".format(nr, nz, "G5")

        symm_funcs[label_G4] = G2 + G4
        symm_funcs[label_G5] = G2 + G5

    parameter = "Gs"
    calcs = trn.train_calculators(parameter, symm_funcs, train_traj)
    columns = ["Symmetry function", "Energy RMSE", "Force RMSE"]
    trn.test_calculators(calcs, test_traj, columns)
