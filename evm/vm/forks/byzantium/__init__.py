from cytoolz import (
    merge,
)

from evm import precompiles
from evm.constants import MAX_UNCLE_DEPTH
from evm.rlp.receipts import (
    Receipt,
)
from evm.utils.address import (
    force_bytes_to_address,
)
from evm.validation import (
    validate_lte,
)

from ..frontier import (
    FRONTIER_PRECOMPILES,
    _make_frontier_receipt,
)
from ..spurious_dragon import SpuriousDragonVM
from ..spurious_dragon.computation import SpuriousDragonComputation

from .constants import EIP649_BLOCK_REWARD
from .headers import (
    create_byzantium_header_from_parent,
    configure_byzantium_header,
)
from .opcodes import BYZANTIUM_OPCODES
from .blocks import ByzantiumBlock


BYZANTIUM_PRECOMPILES = merge(
    FRONTIER_PRECOMPILES,
    {
        force_bytes_to_address(b'\x05'): precompiles.modexp,
        force_bytes_to_address(b'\x06'): precompiles.ecadd,
        force_bytes_to_address(b'\x07'): precompiles.ecmul,
        force_bytes_to_address(b'\x08'): precompiles.ecpairing,
    },
)


def _byzantium_get_block_reward(block_number):
    return EIP649_BLOCK_REWARD


def _byzantium_get_uncle_reward(block_number, uncle):
    validate_lte(uncle.block_number, MAX_UNCLE_DEPTH)
    block_number_delta = block_number - uncle.block_number
    return (8 - block_number_delta) * EIP649_BLOCK_REWARD // 8


def make_byzantium_receipt(vm, transaction, computation):
    old_receipt = _make_frontier_receipt(vm, transaction, computation)
    receipt = Receipt(
        state_root=b'' if computation.is_error else b'\x01',
        gas_used=old_receipt.gas_used,
        logs=old_receipt.logs,
    )
    return receipt


ByzantiumVM = SpuriousDragonVM.configure(
    name='ByzantiumVM',
    # precompiles
    _precompiles=BYZANTIUM_PRECOMPILES,
    # opcodes
    opcodes=BYZANTIUM_OPCODES,
    # State
    _computation_class=SpuriousDragonComputation,
    # RLP
    _block_class=ByzantiumBlock,
    # Methods
    create_header_from_parent=staticmethod(create_byzantium_header_from_parent),
    configure_header=configure_byzantium_header,
    get_block_reward=staticmethod(_byzantium_get_block_reward),
    get_uncle_reward=staticmethod(_byzantium_get_uncle_reward),
    make_receipt=make_byzantium_receipt,
)
