from eth_typing import (
    Hash32,
)
import rlp

from eth.beacon.enums import (
    ValidatorStatusFlags,
)
from eth.rlp.sedes import (
    uint64,
    uint384,
    hash32,
)


class ValidatorRecord(rlp.Serializable):
    """
    Note: using RLP until we have standardized serialization format.
    """
    fields = [
        # BLS public key
        ('pubkey', uint384),
        # Withdrawal credentials
        ('withdrawal_credentials', hash32),
        # RANDAO commitment
        ('randao_commitment', hash32),
        # Slot the proposer has skipped (ie. layers of RANDAO expected)
        ('randao_layers', uint64),
        # Slot when validator activated
        ('activation_slot', uint64),
        # Slot when validator exited
        ('exit_slot', uint64),
        # Slot when validator withdrew
        ('withdrawal_slot', uint64),
        # Slot when validator was penalized
        ('penalized_slot', uint64),
        # Exit counter when validator exited
        ('exit_count', uint64),
        # Status flags
        ('status_flags', uint64),
    ]

    def __init__(self,
                 pubkey: int,
                 withdrawal_credentials: Hash32,
                 randao_commitment: Hash32,
                 randao_layers: int,
                 activation_slot: int,
                 exit_slot: int,
                 withdrawal_slot: int,
                 penalized_slot: int,
                 exit_count: int,
                 status_flags: int) -> None:
        super().__init__(
            pubkey=pubkey,
            withdrawal_credentials=withdrawal_credentials,
            randao_commitment=randao_commitment,
            randao_layers=randao_layers,
            activation_slot=activation_slot,
            exit_slot=exit_slot,
            withdrawal_slot=withdrawal_slot,
            penalized_slot=penalized_slot,
            exit_count=exit_count,
            status_flags=status_flags,
        )

    def is_active(self, slot: int) -> bool:
        """
        Return ``True`` if the validator is active.
        """
        return self.activation_slot <= slot < self.exit_slot

    @classmethod
    def get_pending_validator(cls,
                              pubkey: int,
                              withdrawal_credentials: Hash32,
                              randao_commitment: Hash32,
                              far_future_slot: int) -> 'ValidatorRecord':
        """
        Return a new pending ``ValidatorRecord`` with the given fields.
        """
        return cls(
            pubkey=pubkey,
            withdrawal_credentials=withdrawal_credentials,
            randao_commitment=randao_commitment,
            randao_layers=0,
            activation_slot=far_future_slot,
            exit_slot=far_future_slot,
            withdrawal_slot=far_future_slot,
            penalized_slot=far_future_slot,
            exit_count=0,
            status_flags=0,
        )
