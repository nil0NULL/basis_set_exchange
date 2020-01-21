'''
Read a basis set file in a given format
'''

import os
import bz2
from ..skel import create_skel
from ..validator import validate_data
from ..compose import _whole_basis_types
from .turbomole import read_turbomole
from .g94 import read_g94
from .nwchem import read_nwchem
from .gbasis import read_gbasis
from .dalton import read_dalton
from .molcas import read_molcas
from .genbas import read_genbas

_type_readers = {
    'turbomole': {
        'display': 'Turbomole',
        'extension': '.tm',
        'reader': read_turbomole
    },
    'gaussian94': {
        'display': 'Gaussian94',
        'extension': '.gbs',
        'reader': read_g94
    },
    'nwchem': {
        'display': 'NWChem',
        'extension': '.nw',
        'reader': read_nwchem
    },
    'dalton': {
        'display': 'Dalton',
        'extension': '.mol',
        'reader': read_dalton
    },
    'molcas': {
        'display': 'MolCAS',
        'extension': '.molcas',
        'reader': read_molcas
    },
    'cfour': {
        'display': 'CFOUR',
        'extension': '.c4bas',
        'reader': read_genbas
    },
    'genbas': {
        'display': 'Genbas',
        'extension': '.genbas',
        'reader': read_genbas
    },
    'gbasis': {
        'display': 'GBasis',
        'extension': '.gbasis',
        'reader': read_gbasis
    }
}


def _fix_uncontracted(basis):
    '''
    Forces the contraction coefficient of uncontracted shells to 1.0
    '''

    for el in basis['elements'].values():
        if 'electron_shells' not in el:
            continue

        for sh in el['electron_shells']:
            if len(sh['coefficients']) == 1 and len(sh['coefficients'][0]) == 1:
                sh['coefficients'][0][0] = '1.0000000'

            # Some uncontracted shells don't have a coefficient
            if len(sh['coefficients']) == 0:
                sh['coefficients'].append(['1.0000000'])

    return basis


def read_formatted_basis_str(basis_str, file_type, validate=False, as_component=False):
    basis_lines = [x.strip() for x in basis_str.splitlines()]

    element_data = _type_readers[file_type]['reader'](basis_lines)

    # the readers give the 'elements' member of a basis set json
    # We need to do a little fixing up
    if as_component:
        data = create_skel('component')
        data['elements'] = element_data
        for el in data['elements'].values():
            el['references'] = []
        bs_type = 'component'
    else:
        data = create_skel('minimal')
        data['elements'] = element_data
        bs_type = 'minimal'

        # Create the function types
        data['function_types'] = _whole_basis_types(data)

    # It's debateable if I want to do this
    #return _fix_uncontracted(data)

    # Validate if desired
    if validate:
        validate_data(bs_type, data)

    return data


def read_formatted_basis(file_path, file_type=None, encoding='utf-8-sig', validate=False, as_component=False):
    # Note that the default is utf-8-sig, which handles the optional byte order mark

    if not os.path.isfile(file_path):
        raise RuntimeError('Basis file path \'{}\' does not exist'.format(file_path))

    if file_type is None:
        for k, v in _type_readers.items():
            ext = v['extension']
            ext_bz2 = ext + '.bz2'
            if file_path.endswith(ext) or file_path.endswith(ext_bz2):
                file_type = k
                break

        else:
            raise RuntimeError("Unable to determine basis set format of '{}'".format(file_path))
    else:
        file_type = file_type.lower()

    if file_type not in _type_readers:
        raise RuntimeError("Unknown file type to read '{}'".format(file_type))

    # Handle compressed files
    if file_path.endswith('.bz2'):
        with bz2.open(file_path, 'rt', encoding=encoding) as f:
            basis_str = f.read()
    else:
        with open(file_path, 'r', encoding=encoding) as f:
            basis_str = f.read()

    return read_formatted_basis_str(basis_str, file_type, validate, as_component)


def get_reader_formats():
    '''
    Returns the basis set formats that can be read by this library.

    This is returned as an ordered dictionary of key to display name.
    '''

    return {k: v['display'] for k, v in _type_readers.items()}