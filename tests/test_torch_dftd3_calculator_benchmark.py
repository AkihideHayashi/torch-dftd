import tempfile
from typing import List

import numpy as np
import pytest
from ase import Atoms
from ase.build import fcc111, molecule
from ase.calculators.dftd3 import DFTD3
from ase.units import Bohr
from torch_dftd.torch_dftd3_calculator import TorchDFTD3Calculator


def _create_atoms() -> List[Atoms]:
    """Initialization"""
    atoms = molecule("CH3CH2OCH3")

    slab = fcc111("Au", size=(2, 1, 3), vacuum=80.0)
    slab.pbc = np.array([True, True, True])
    return [atoms, slab]


def calc_energy(calculator, atoms):
    calculator.reset()
    atoms.calc = calculator
    e1 = atoms.get_potential_energy()
    return True


def calc_force_stress(calculator, atoms):
    calculator.reset()
    atoms.calc = calculator
    f1 = atoms.get_forces()
    if np.all(atoms.pbc == np.array([True, True, True])):
        s1 = atoms.get_stress()
    return True


@pytest.mark.parametrize("atoms", _create_atoms())
def test_dftd3_calculator_benchmark(atoms, benchmark):
    damping = "bj"
    xc = "pbe"
    old = False
    cutoff = 95 * Bohr
    with tempfile.TemporaryDirectory() as tmpdirname:
        dftd3_calc = DFTD3(
            damping=damping, xc=xc, grad=True, old=old, cutoff=cutoff, directory=tmpdirname
        )
        benchmark.pedantic(
            calc_force_stress,
            kwargs=dict(calculator=dftd3_calc, atoms=atoms),
            rounds=3,
            iterations=5,
        )


@pytest.mark.parametrize("atoms", _create_atoms())
@pytest.mark.parametrize("device", ["cpu", "cuda:0"])
def test_torch_dftd3_calculator_benchmark(atoms, device, benchmark):
    damping = "bj"
    xc = "pbe"
    old = False
    cutoff = 95 * Bohr
    dftd3_calc = TorchDFTD3Calculator(
        damping=damping,
        xc=xc,
        grad=True,
        old=old,
        cutoff=cutoff,
        device=device,
    )
    # Dry run once
    calc_force_stress(calculator=dftd3_calc, atoms=atoms),

    benchmark.pedantic(
        calc_force_stress, kwargs=dict(calculator=dftd3_calc, atoms=atoms), rounds=3, iterations=5
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
