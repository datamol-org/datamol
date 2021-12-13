from rdkit import Chem

import datamol as dm


def test_enumerate_tautomers():
    mol = dm.to_mol("OC1=CC2CCCCC2[N:1]=C1")

    mols = dm.enumerate_tautomers(mol, n_variants=10)

    assert {dm.to_smiles(m) for m in mols} == {"O=C1C=[N:1]C2CCCCC2C1", "OC1=CC2CCCCC2[N:1]=C1"}


def test_enumerate_stereo():
    mol = dm.to_mol("OC1=CC2CCCCC2[N:1]=C1")

    mols = dm.enumerate_stereoisomers(mol, n_variants=10)

    assert {dm.to_smiles(m) for m in mols} == {
        "OC1=C[C@@H]2CCCC[C@@H]2[N:1]=C1",
        "OC1=C[C@@H]2CCCC[C@H]2[N:1]=C1",
        "OC1=C[C@H]2CCCC[C@@H]2[N:1]=C1",
        "OC1=C[C@H]2CCCC[C@H]2[N:1]=C1",
    }


def test_enumerate_structural():
    mol = dm.to_mol("CCCCC")  # pentane has only three structural isomers
    mols_iso = dm.enumerate_structisomers(
        mol,
        n_variants=5,
        allow_cycle=False,
        depth=2,
        allow_double_bond=False,
        allow_triple_bond=False,
    )
    mols_cyclo_iso = dm.enumerate_structisomers(mol, n_variants=5, depth=2, allow_cycle=True)

    assert {dm.to_smiles(m) for m in mols_iso} == {"CCC(C)C", "CC(C)(C)C"}
    # expect 3 molecules with cycles
    assert sum([Chem.rdMolDescriptors.CalcNumRings(x) == 1 for x in mols_cyclo_iso]) == 3  # type: ignore

    # mols_cyclo_iso_double = dm.enumerate_structisomers(
    #     mol, n_variants=10, allow_cycle=True, allow_double_bond=True
    # )
    # should have mol with double link
    # assert sum(["=" in dm.to_smiles(x) for x in mols_cyclo_iso_double]) > 0


def test_canonical_tautomer():
    smiles = "Oc1c(cccc3)c3nc2ccncc12"
    mol = dm.to_mol(smiles)

    canonical_mol = dm.canonical_tautomer(mol)

    assert dm.to_smiles(canonical_mol) == "O=c1c2ccccc2[nH]c2ccncc12"
    assert dm.to_inchikey(canonical_mol) == dm.to_inchikey(mol)


def test_remove_stereochemistry():
    mol = dm.to_mol("C[C@H]1CCC[C@@H](C)[C@@H]1Cl")
    mol_no_stereo = dm.remove_stereochemistry(mol)
    assert dm.to_smiles(mol_no_stereo) == "CC1CCCC(C)C1Cl"
