import pytest

from eth_utils import (
    denoms,
    ValidationError,
)

from eth.beacon.deposit_helpers import (
    add_pending_validator,
    process_deposit,
    validate_proof_of_possession,
)
from eth.beacon.enums import (
    SignatureDomain,
)
from eth.beacon.helpers import (
    get_domain,
)
from eth.beacon.types.states import BeaconState
from eth.beacon.types.validator_records import ValidatorRecord

from tests.beacon.helpers import (
    make_deposit_input,
    sign_proof_of_possession,
)


def test_add_pending_validator(sample_beacon_state_params,
                               sample_validator_record_params):

    validator_registry_len = 2
    state = BeaconState(**sample_beacon_state_params).copy(
        validator_registry=[
            ValidatorRecord(**sample_validator_record_params)
            for _ in range(validator_registry_len)
        ],
        validator_balances=[
            100
            for _ in range(validator_registry_len)
        ],
    )
    validator = ValidatorRecord(**sample_validator_record_params)
    amount = 5566
    state, index = add_pending_validator(
        state,
        validator,
        amount,
    )
    assert index == validator_registry_len
    assert state.validator_registry[index] == validator


@pytest.mark.parametrize(
    "expected",
    (
        (True),
        (ValidationError),
    ),
)
def test_validate_proof_of_possession(sample_beacon_state_params, pubkeys, privkeys, expected):
    state = BeaconState(**sample_beacon_state_params)

    privkey = privkeys[0]
    pubkey = pubkeys[0]
    withdrawal_credentials = b'\x34' * 32
    custody_commitment = b'\x12' * 32
    randao_commitment = b'\x56' * 32
    domain = get_domain(
        state.fork_data,
        state.slot,
        SignatureDomain.DOMAIN_DEPOSIT,
    )

    deposit_input = make_deposit_input(
        pubkey=pubkey,
        withdrawal_credentials=withdrawal_credentials,
        randao_commitment=randao_commitment,
        custody_commitment=custody_commitment,
    )
    if expected is True:
        proof_of_possession = sign_proof_of_possession(deposit_input, privkey, domain)

        validate_proof_of_possession(
            state=state,
            pubkey=pubkey,
            proof_of_possession=proof_of_possession,
            withdrawal_credentials=withdrawal_credentials,
            randao_commitment=randao_commitment,
            custody_commitment=custody_commitment,
        )
    else:
        proof_of_possession = b'\x11' * 32
        with pytest.raises(ValidationError):
            validate_proof_of_possession(
                state=state,
                pubkey=pubkey,
                proof_of_possession=proof_of_possession,
                withdrawal_credentials=withdrawal_credentials,
                randao_commitment=randao_commitment,
                custody_commitment=custody_commitment,
            )


def test_process_deposit(sample_beacon_state_params,
                         privkeys,
                         pubkeys,
                         far_future_slot):
    state = BeaconState(**sample_beacon_state_params).copy(
        slot=1,
        validator_registry=(),
    )

    privkey_1 = privkeys[0]
    pubkey_1 = pubkeys[0]
    amount = 32 * denoms.gwei
    withdrawal_credentials = b'\x34' * 32
    custody_commitment = b'\x11' * 32
    randao_commitment = b'\x56' * 32
    domain = get_domain(
        state.fork_data,
        state.slot,
        SignatureDomain.DOMAIN_DEPOSIT,
    )

    deposit_input = make_deposit_input(
        pubkey=pubkey_1,
        withdrawal_credentials=withdrawal_credentials,
        randao_commitment=randao_commitment,
        custody_commitment=custody_commitment,
    )
    proof_of_possession = sign_proof_of_possession(deposit_input, privkey_1, domain)
    # Add the first validator
    result_state = process_deposit(
        state=state,
        pubkey=pubkey_1,
        amount=amount,
        proof_of_possession=proof_of_possession,
        withdrawal_credentials=withdrawal_credentials,
        randao_commitment=randao_commitment,
        custody_commitment=custody_commitment,
        far_future_slot=far_future_slot,
    )

    assert len(result_state.validator_registry) == 1
    index = 0
    assert result_state.validator_registry[0].pubkey == pubkey_1
    assert result_state.validator_registry[index].withdrawal_credentials == withdrawal_credentials
    assert result_state.validator_registry[index].randao_commitment == randao_commitment
    assert result_state.validator_balances[index] == amount
    # test immutable
    assert len(state.validator_registry) == 0

    # Add the second validator
    privkey_2 = privkeys[1]
    pubkey_2 = pubkeys[1]
    deposit_input = make_deposit_input(
        pubkey=pubkey_2,
        withdrawal_credentials=withdrawal_credentials,
        randao_commitment=randao_commitment,
        custody_commitment=custody_commitment,
    )
    proof_of_possession = sign_proof_of_possession(deposit_input, privkey_2, domain)
    result_state = process_deposit(
        state=result_state,
        pubkey=pubkey_2,
        amount=amount,
        proof_of_possession=proof_of_possession,
        withdrawal_credentials=withdrawal_credentials,
        randao_commitment=randao_commitment,
        far_future_slot=far_future_slot,
    )
    assert len(result_state.validator_registry) == 2
    assert result_state.validator_registry[1].pubkey == pubkey_2
