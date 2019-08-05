import sys
import numpy as np
from asap3 import EMT
from amp.descriptor.cutoffs import Polynomial
from amp.descriptor.gaussian import make_symmetry_functions

sys.path.insert(1, "../tools")

from create_trajectory import TrajectoryBuilder
from training import Trainer


if __name__ == "__main__":
    system = "copper"
    size = (1, 1, 1)
    temp = 500

    n_test = int(5e2)
    save_interval = 100

    max_steps = int(5e2)
    convergence = {"energy_rmse": 1e-16, "force_rmse": None, "max_steps": max_steps}
    force_coefficient = None
    hidden_layers = (10, 10)
    activation = "tanh"
    cutoff = Polynomial(6.0)

    elements = ["Cu"]
    gammas = [1.0, -1.0]
    nr = 4
    nz = 1
    radial_etas = 10.0 * np.ones(nr)
    centers = np.linspace(0.5, cutoff.Rc + 0.5, nr)
    angular_etas = np.linspace(0.1, 1.0, nr)
    zetas = [4 ** i for i in range(nz)]

    G2 = make_symmetry_functions(
        elements=elements, type="G2", etas=radial_etas, centers=centers
    )
    G5 = make_symmetry_functions(
        elements=elements, type="G5", etas=angular_etas, zetas=zetas, gammas=[1.0, -1.0]
    )
    Gs = G2 + G5

    trn = Trainer(
        convergence=convergence,
        force_coefficient=force_coefficient,
        hidden_layers=hidden_layers,
        activation=activation,
        cutoff=cutoff,
        Gs=Gs,
    )

    trjbd = TrajectoryBuilder()
    n_images = [10, 20, 50, 100]
    train_trajs = ["training_n{}.traj".format(ni) for ni in n_images]
    for i in range(len(n_images)):
        calc = EMT()
        train_atoms = trjbd.build_atoms(system, size, temp, calc)
        n_train = n_images[i] * save_interval
        steps, train_trajs[i] = trjbd.integrate_atoms(
            train_atoms, train_trajs[i], n_train, save_interval
        )

    test_traj = "test.traj"
    calc = EMT()
    test_atoms = trjbd.build_atoms(system, size, temp, calc)
    steps, test_traj = trjbd.integrate_atoms(
        test_atoms, test_traj, n_test, save_interval
    )

    calcs = {}
    for i in range(len(n_images)):
        label = "n{}".format(n_images[i])
        calc = trn.create_calc(label=label, dblabel=label)
        amp_name = trn.train_calc(calc, train_trajs[i])
        calcs[label] = amp_name

    columns = ["Number of images", "Energy RMSE", "Force RMSE"]
    trn.test_calculators(calcs, test_traj, columns)
