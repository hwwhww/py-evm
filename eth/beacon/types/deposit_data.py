
import rlp
from eth.rlp.sedes import uint64
from .deposit_input import DepositInput


class DepositData(rlp.Serializable):
    """
    Not in spec, this is for fields in Deposit
    """
    fields = [
        ('deposit_input', DepositInput),
        # Amount in Gwei
        ('amount', uint64),
        # Timestamp from deposit contract
        ('timestamp', uint64),
    ]

    def __init__(self,
                 deposit_input: DepositInput,
                 amount: int,
                 timestamp: int) -> None:

        super().__init__(
            deposit_input,
            amount,
            timestamp,
        )
