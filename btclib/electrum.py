#!/usr/bin/env python3

# Copyright (C) 2017-2020 The btclib developers
#
# This file is part of btclib. It is subject to the license terms in the
# LICENSE file found in the top-level directory of this distribution.
#
# No part of btclib including this file, may be copied, modified, propagated,
# or distributed except according to the terms contained in the LICENSE file.

"""Electrum entropy / mnemonic / seed functions.

Electrum mnemonic is versioned, conveying BIP32 derivation rule too.
"""

import hmac
from hashlib import pbkdf2_hmac, sha512
from typing import Tuple

from .entropy import (BinStr, Entropy, _entropy_from_indexes,
                      _indexes_from_entropy, binstr_from_entropy)
from .mnemonic import (Mnemonic, _indexes_from_mnemonic,
                       _mnemonic_from_indexes, _wordlists)

_MNEMONIC_VERSIONS = {
    'standard': '01',  # P2PKH and P2MS-P2SH wallets
    'segwit': '100',  # P2WPKH and P2WSH wallets
    '2fa': '101',  # Two-factor authenticated wallets
    '2fa_segwit': '102',  # Two-factor authenticated wallets, using segwit
}


def version_from_mnemonic(mnemonic: Mnemonic) -> str:
    """Return the Electrum version embedded in the mnemonic sentence."""

    s = hmac.new(b"Seed version", mnemonic.encode(), sha512).hexdigest()

    if s.startswith(_MNEMONIC_VERSIONS['standard']):
        return 'standard'
    if s.startswith(_MNEMONIC_VERSIONS['segwit']):
        return 'segwit'
    if s.startswith(_MNEMONIC_VERSIONS['2fa']):
        return '2fa'
    if s.startswith(_MNEMONIC_VERSIONS['2fa_segwit']):
        return '2fa_segwit'

    raise ValueError(f"unknown electrum mnemonic version ({s[:3]})")


def mnemonic_from_entropy(entropy: Entropy, version: str = 'standard',
                          lang: str = "en") -> Mnemonic:
    """Convert input entropy to Electrum versioned mnemonic sentence.

    Input entropy can be expressed as
    binary 0/1 string, bytes-like, or integer.

    In the case of binary 0/1 string and bytes-like,
    leading zeros are considered redundant padding.
    """

    if version not in _MNEMONIC_VERSIONS:
        m = f"mnemonic version '{version}' not in electrum allowed "
        m += f"mnemonic versions {list(_MNEMONIC_VERSIONS.keys())}"
        raise ValueError(m)
    version = _MNEMONIC_VERSIONS[version]

    binstr_entropy = binstr_from_entropy(entropy)
    int_entropy = int(binstr_entropy, 2)
    base = _wordlists.language_length(lang)
    invalid = True
    while invalid:
        # electrum considers entropy as integer, losing any leading zero
        # so the value of binstr_entropy before the while must be updated
        nbits = int_entropy.bit_length()
        binstr_entropy = binstr_from_entropy(int_entropy, nbits)
        indexes = _indexes_from_entropy(binstr_entropy, base)
        mnemonic = _mnemonic_from_indexes(indexes, lang)
        # version validity check
        s = hmac.new(b"Seed version",
                     mnemonic.encode(), sha512).hexdigest()
        if s.startswith(version):
            invalid = False
        # next trial
        int_entropy += 1

    return mnemonic


def entropy_from_mnemonic(mnemonic: Mnemonic, lang: str = "en") -> BinStr:
    "Return the entropy from the Electrum versioned mnemonic sentence."

    # verify that it is a valid Electrum mnemonic sentence
    _ = version_from_mnemonic(mnemonic)
    indexes = _indexes_from_mnemonic(mnemonic, lang)
    base = _wordlists.language_length(lang)
    entropy = _entropy_from_indexes(indexes, base)
    return entropy


def _seed_from_mnemonic(mnemonic: Mnemonic,
                        passphrase: str) -> Tuple[str, bytes]:
    "Return (version, seed) from the provided Electrum mnemonic."

    version = version_from_mnemonic(mnemonic)

    hf_name = 'sha512'
    password = mnemonic.encode()
    salt = ('electrum' + passphrase).encode()
    iterations = 2048
    dksize = 64
    return version, pbkdf2_hmac(hf_name, password, salt, iterations, dksize)
