import copy

from rdkit import Chem

import datamol as dm


def test_to_mol():
    smiles = "O=C(C)Oc1ccccc1C(=O)O"
    mol = dm.to_mol(smiles)
    assert mol.GetNumAtoms() == 13

    smiles = "O=C(C)Oc1ccccc1C(=O)O"
    mol = dm.to_mol(smiles, add_hs=True)
    assert mol.GetNumAtoms() == 21

    smiles = "fake_smiles"
    mol = dm.to_mol(smiles)
    assert mol is None


def test_reorder_atoms():
    smiles = "c1ccc(C(=O)O)c(c1)OC(=O)C"
    mol = dm.to_mol(smiles, add_hs=False, explicit_only=False)

    orders = [a.GetAtomicNum() for a in mol.GetAtoms()]
    assert orders == [6, 6, 6, 6, 6, 8, 8, 6, 6, 8, 6, 8, 6]

    mol = dm.reorder_atoms(mol)
    orders = [a.GetAtomicNum() for a in mol.GetAtoms()]
    assert orders == [6, 8, 8, 8, 6, 6, 6, 6, 8, 6, 6, 6, 6]


def test_randomize_atoms():
    smiles = "c1ccc(C(=O)O)c(c1)OC(=O)C"
    mol = dm.to_mol(smiles)
    orders = [a.GetAtomicNum() for a in mol.GetAtoms()]

    randomized_mol = dm.randomize_atoms(mol)
    randomized_orders = [a.GetAtomicNum() for a in randomized_mol.GetAtoms()]

    assert sum(orders) == sum(randomized_orders)


def test_to_neutral():

    smiles = "[NH4+]"
    mol = dm.to_mol(smiles, add_hs=False, explicit_only=False)

    smiles = dm.to_smiles(dm.to_neutral(mol))
    assert smiles == "[NH4]"

    smiles = "O=C(c1ccccc1)[O-]"
    mol = dm.to_mol(smiles, add_hs=False, explicit_only=False)
    uncharged_mol = dm.to_neutral(mol)
    assert sum([a.GetFormalCharge() for a in uncharged_mol.GetAtoms()]) == 0


def test_sanitize():
    smiles = "CC(=O)Oc1ccccc1C(=O)O"
    mol = dm.to_mol(smiles, sanitize=False)
    mol = dm.sanitize_mol(mol, charge_neutral=True)
    assert dm.to_smiles(mol) == "CC(=O)Oc1ccccc1C(=O)O"

    mol = dm.sanitize_mol(None, charge_neutral=True)
    assert mol is None

    smiles_list = (
        "CC.[H][N:1]1(C)=CC(O)=CC2CCCCC12",  # broken
        "O=c1ccc2ccccc2n1",  # sanitize
        "Cc1nnnn1C",  # none
        "CCc1ccc2nc(=O)c(cc2c1)Cc1nnnn1C1CCCCC1",  # sanitize
        "c1cnc2cc3ccnc3cc12",  # none
        "c1cc2cc3ccnc3cc2n1",  # none
        "O=c1ccnc(c1)-c1cnc2cc3ccnc3cc12",  # sanitize
        "O=c1ccnc(c1)-c1cc1",  # broken
    )

    # check sanitize_mol
    assert dm.to_mol(smiles_list[1]) is None
    assert dm.to_mol(smiles_list[2]) is not None
    assert dm.sanitize_mol(None) is None
    assert dm.sanitize_mol(dm.to_mol(smiles_list[0], sanitize=False)) is None
    assert dm.sanitize_mol(dm.to_mol(smiles_list[1], sanitize=False)) is not None
    assert dm.sanitize_mol(dm.to_mol(smiles_list[2], sanitize=False)) is not None

    mol_2 = dm.sanitize_mol(dm.to_mol(smiles_list[1], sanitize=False))
    assert dm.to_smiles(mol_2) == dm.sanitize_smiles("O=c1ccc2ccccc2[nH]1")

    fixed_smiles = [dm.sanitize_smiles(smiles) for smiles in smiles_list]
    assert len([x for x in fixed_smiles if x is not None]) == 6


def test_sanitize_first():

    smiles = ["fake_smiles", "CC(=O)Oc1ccccc1C(=O)O"]
    mols = [dm.to_mol(s) for s in smiles]
    mol = dm.sanitize_first(mols)
    assert dm.to_smiles(mol) == "CC(=O)Oc1ccccc1C(=O)O"


def test_standardize_mol():
    sm = "[Na]OC1=CC2CCCCC2N=C1"
    sm_standard = dm.to_smiles(dm.standardize_smiles(sm))
    standard_mol = dm.standardize_mol(dm.to_mol(sm), disconnect_metals=True, uncharge=True)
    mol_standard = dm.to_smiles(Chem.MolToSmiles(standard_mol))
    assert sm_standard == mol_standard


def test_fix_valence():
    sm = "Cl.[H][N:1]1=CC(O)=CC2CCCCC12"
    mol = Chem.MolFromSmiles(sm, sanitize=False)
    mol.UpdatePropertyCache(False)
    mol_copy = copy.copy(mol)

    nitrogen_atom = [a for a in mol.GetAtoms() if a.GetAtomMapNum() == 1][0]
    nitrogen_valence = nitrogen_atom.GetExplicitValence()
    assert dm.incorrect_valence(nitrogen_atom, True)

    fixed_mol = dm.fix_valence_charge(mol, inplace=False)
    assert dm.to_mol(Chem.MolToSmiles(fixed_mol)) is not None

    # expect nitrogen atom to still be incorrect
    assert dm.incorrect_valence(nitrogen_atom, True)

    # in place fix
    fixed_mol = dm.fix_valence_charge(mol, inplace=True)
    # nitrogen should be charged positively if this was fixed.
    assert nitrogen_atom.GetFormalCharge() == 1

    fixed_mol2 = dm.fix_valence(mol_copy)
    fixed_nitrogen_atom = [a for a in fixed_mol2.GetAtoms() if a.GetAtomMapNum() == 1][0]
    assert fixed_nitrogen_atom.GetExplicitValence() < nitrogen_valence

    # mol should be fixed
    assert dm.to_mol(Chem.MolToSmiles(fixed_mol2)) is not None


def test_adjust_singleton():
    sm = "Cl.[N:1]1=CC(O)=CC2CCCCC12.CC.C"
    mol = dm.to_mol(sm)
    fixed_mol = dm.adjust_singleton(mol)
    assert len(Chem.rdmolops.GetMolFrags(fixed_mol)) == 2
    assert fixed_mol.HasSubstructMatch(Chem.MolFromSmiles("CC"))  # assert ethyl is there


def test_fixmol():
    sm = "C.Cl.CC.[H][N:1]1(C)=CC(O)=CC2CCCCC12"
    mol = Chem.MolFromSmiles(sm, sanitize=False)
    # mol.UpdatePropertyCache(False)
    # Chem.Kekulize(mol)
    res = dm.fix_mol(mol, n_iter=1)  # copy by default

    # should still be invalid in term of valence for nitrogen
    assert not dm.incorrect_valence(res)

    res2 = dm.fix_mol(mol, n_iter=2)
    # not expecting difference between res2 and res3
    assert Chem.MolToSmiles(res) == Chem.MolToSmiles(res2)

    # only largest expected_here
    res_largest = dm.fix_mol(mol, largest_only=True)

    dm.fix_mol(mol, remove_singleton=True, largest_only=True)
    assert len(Chem.rdmolops.GetMolFrags(res_largest)) == 1

    expected_largest_fix = dm.standardize_smiles("OC1=CC2CCCCC2[N:1]=C1")
    assert dm.standardize_smiles(Chem.MolToSmiles(res_largest)) == expected_largest_fix

    res_no_singleton = dm.fix_mol(mol, n_iter=2, remove_singleton=True)
    assert len(Chem.rdmolops.GetMolFrags(res_largest)) == 1
    assert len(Chem.rdmolops.GetMolFrags(res_no_singleton)) == 2


def test_dative_bond():
    smis = "CC1=CC=CC(=C1N\\2O[Co]3(ON(\\C=[N]3\\C4=C(C)C=CC=C4C)C5=C(C)C=CC=C5C)[N](=C2)\\C6=C(C)C=CC=C6C)C"
    expected_result = (
        "CC1=CC=CC(C)=C1N1C=N(C2=C(C)C=CC=C2C)->[Co]2(<-N(C3=C(C)C=CC=C3C)=CN(C3=C(C)C=CC=C3C)O2)O1"
    )

    assert dm.is_transition_metal(Chem.Atom("Co"))

    # sodium is not a transition metal
    assert not dm.is_transition_metal(Chem.Atom("Na"))

    mol = dm.set_dative_bonds(Chem.MolFromSmiles(smis, sanitize=False))
    assert Chem.MolToSmiles(mol) == expected_result
    assert dm.to_mol(Chem.MolToSmiles(mol)) is not None


def test_copy_mol():
    mol = dm.to_mol("OC1=CC2CCCCC2[N:1]=C1")
    new_mol = dm.copy_mol(mol)

    assert dm.to_smiles(mol) == dm.to_smiles(new_mol)


def test_set_mol_props():
    mol = dm.to_mol("CCC")

    props = {}
    props["number"] = 55
    props["float"] = 5.555
    props["string"] = "hello"
    props["something_else"] = type(int)

    dm.set_mol_props(mol, props)

    mol_props = mol.GetPropsAsDict()
    assert mol_props["number"] == props["number"]
    assert mol_props["float"] == props["float"]
    assert mol_props["string"] == props["string"]
    assert mol_props["something_else"] == str(props["something_else"])


def test_copy_mol_props():
    source = dm.to_mol("CCC")
    destination = dm.to_mol("CC")

    props = {}
    props["number"] = 55
    props["float"] = 5.555
    props["string"] = "hello"
    props["something_else"] = type(int)

    dm.set_mol_props(source, props)

    dm.copy_mol_props(source, destination)

    assert destination.GetPropsAsDict() == source.GetPropsAsDict()


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


def test_atom_indices_to_mol():
    mol = dm.to_mol("OC1=CC2CCCCC2[N:1]=C1")
    dm.atom_indices_to_mol(mol)
    for atom in mol.GetAtoms():
        assert atom.GetIntProp("molAtomMapNumber") == atom.GetIdx()
