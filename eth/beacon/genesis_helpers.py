from typing import (
    Any,
    Dict,
    List,
    TYPE_CHECKING,
)

from eth_typing import (
    Hash32,
)

from eth.constants import (
    ZERO_HASH32,
)
from eth.beacon.types.active_state import ActiveState
from eth.beacon.types.block import Block
from eth.beacon.types.crosslink_record import CrosslinkRecord
from eth.beacon.types.crystallized_state import CrystallizedState
from eth.beacon.helpers import (
    get_new_shuffling,
)

if TYPE_CHECKING:
    from eth.beacon.types.validator_record import ValidatorRecord  # noqa: F401


def get_genesis_active_state(config: Dict[str, Any]) -> ActiveState:
    recent_block_hashes = [ZERO_HASH32] * config['cycle_length'] * 2

    return ActiveState(
        pending_attestations=[],
        recent_block_hashes=recent_block_hashes,
    )


def get_genesis_crystallized_state(
        validators: List['ValidatorRecord'],
        init_shuffling_seed: Hash32,
        config: Dict[str, Any]) -> CrystallizedState:

    current_dynasty = 1
    crosslinking_start_shard = 0

    shard_and_committee_for_slots = get_new_shuffling(
        init_shuffling_seed,
        validators,
        current_dynasty,
        crosslinking_start_shard,
        config=config,
    )
    # concatenate with itself to span 2*CYCLE_LENGTH
    shard_and_committee_for_slots = shard_and_committee_for_slots + shard_and_committee_for_slots

    return CrystallizedState(
        validators=validators,
        last_state_recalc=0,
        shard_and_committee_for_slots=shard_and_committee_for_slots,
        last_justified_slot=0,
        justified_streak=0,
        last_finalized_slot=0,
        current_dynasty=current_dynasty,
        crosslink_records=[
            CrosslinkRecord(hash=ZERO_HASH32, slot=0, dynasty=0)
            for i
            in range(config['shard_count'])
        ],
        dynasty_seed=init_shuffling_seed,
        dynasty_start=0,
    )


def get_genesis_block(active_state_root: Hash32,
                      crystallized_state_root: Hash32) -> Block:
    return Block(
        parent_hash=ZERO_HASH32,
        slot_number=0,
        randao_reveal=ZERO_HASH32,
        attestations=[],
        pow_chain_ref=ZERO_HASH32,
        active_state_root=active_state_root,
        crystallized_state_root=crystallized_state_root,
    )
