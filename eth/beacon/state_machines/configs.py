from typing import (
    NamedTuple,
)

from eth.typing import (
    Address,
)


BeaconConfig = NamedTuple(
    'BeaconConfig',
    (
        # Misc
        ('SHARD_COUNT', int),
        ('TARGET_COMMITTEE_SIZE', int),
        ('EJECTION_BALANCE', int),
        ('MAX_BALANCE_CHURN_QUOTIENT', int),
        ('BEACON_CHAIN_SHARD_NUMBER', int),
        ('MAX_CASPER_VOTES', int),
        ('LATEST_BLOCK_ROOTS_LENGTH', int),
        ('LATEST_RANDAO_MIXES_LENGTH', int),
        ('LATEST_PENALIZED_EXIT_LENGTH', int),
        # EMPTY_SIGNATURE is defined in constants.py
        # Deposit contract
        ('DEPOSIT_CONTRACT_ADDRESS', Address),
        ('DEPOSIT_CONTRACT_TREE_DEPTH', int),
        ('MIN_DEPOSIT', int),
        ('MAX_DEPOSIT', int),
        # ZERO_HASH (ZERO_HASH32) is defined in constants.py
        # Initial values
        ('GENESIS_FORK_VERSION', int),
        ('GENESIS_SLOT', int),
        ('FAR_FUTURE_SLOT', int),
        ('BLS_WITHDRAWAL_PREFIX_BYTE', bytes),
        # Time parameters
        ('SLOT_DURATION', int),
        ('MIN_ATTESTATION_INCLUSION_DELAY', int),
        ('EPOCH_LENGTH', int),
        ('MIN_VALIDATOR_REGISTRY_CHANGE_INTERVAL', int),
        ('SEED_LOOKAHEAD', int),
        ('ENTRY_EXIT_DELAY', int),
        ('POW_RECEIPT_ROOT_VOTING_PERIOD', int),
        ('MIN_VALIDATOR_WITHDRAWAL_TIME', int),
        # Reward and penalty quotients
        ('BASE_REWARD_QUOTIENT', int),
        ('WHISTLEBLOWER_REWARD_QUOTIENT', int),
        ('INCLUDER_REWARD_QUOTIENT', int),
        ('INACTIVITY_PENALTY_QUOTIENT', int),
        # Max operations per block
        ('MAX_PROPOSER_SLASHINGS', int),
        ('MAX_CASPER_SLASHINGS', int),
        ('MAX_ATTESTATIONS', int),
        ('MAX_DEPOSITS', int),
        ('MAX_EXITS', int),
    )
)
