from cytoolz import (
    curry,
    merge,
)

from eth_utils import (
    keccak,
    to_tuple,
)
import rlp
from trie import (
    BinaryTrie,
    HexaryTrie,
)

from evm.db.backends.memory import MemoryDB
from evm.db.chain import ChainDB


@to_tuple
def diff_state_db(expected_state, state_db):
    for account, account_data in sorted(expected_state.items()):
        expected_nonce = account_data['nonce']
        expected_code = account_data['code']
        expected_balance = account_data['balance']

        actual_nonce = state_db.get_nonce(account)
        actual_code = state_db.get_code(account)
        actual_balance = state_db.get_balance(account)

        if actual_nonce != expected_nonce:
            yield (account, 'nonce', actual_nonce, expected_nonce)
        if actual_code != expected_code:
            yield (account, 'code', actual_code, expected_code)
        if actual_balance != expected_balance:
            yield (account, 'balance', actual_balance, expected_balance)

        for slot, expected_storage_value in sorted(account_data['storage'].items()):
            actual_storage_value = state_db.get_storage(account, slot)
            if actual_storage_value != expected_storage_value:
                yield (
                    account,
                    'storage[{0}]'.format(slot),
                    actual_storage_value,
                    expected_storage_value,
                )


# Make the root of a receipt tree
def make_trie_root_and_nodes(transactions, trie_class=HexaryTrie, chain_db_class=ChainDB):
    chaindb = chain_db_class(MemoryDB(), trie_class=trie_class)
    db = chaindb.db
    transaction_db = trie_class(db, chaindb.empty_root_hash)

    for index, transaction in enumerate(transactions):
        index_key = rlp.encode(index, sedes=rlp.sedes.big_endian_int)
        transaction_db[index_key] = rlp.encode(transaction)

    return transaction_db.root_hash, transaction_db.db.wrapped_db.kv_store


def update_witness_db(witness, recent_trie_nodes_db, account_state_class, trie_class=BinaryTrie):
    witness_kv = dict([(keccak(value), value) for value in witness])
    witness_union = merge(witness_kv, recent_trie_nodes_db)
    witness_db = ChainDB(
        MemoryDB(witness_union),
        account_state_class=account_state_class,
        trie_class=trie_class,
    )
    return witness_db


def apply_state_transition_with_witness(
        witness_db,
        transaction,
        block,
        receipts,
        state_class,
        execution_context):

    vm_state = state_class(
        chaindb=witness_db,
        execution_context=execution_context,
        state_root=block.header.state_root,
        receipts=receipts,
    )
    computation, block, trie_data_dict = vm_state.apply_transaction(
        transaction=transaction,
        block=block,
    )
    return computation, block, trie_data_dict


@curry
def apply_single_transaction(
        transaction,
        state_class,
        account_state_class,
        execution_context,
        params):
    current_block, receipts, recent_trie_nodes_db, recent_trie_data_dict = params
    witness_db = ChainDB(
        MemoryDB(recent_trie_nodes_db),
        account_state_class=account_state_class,
        trie_class=BinaryTrie,
    )

    computation, current_block, trie_data_dict = apply_state_transition_with_witness(
        witness_db,
        transaction,
        current_block,
        receipts,
        state_class,
        execution_context)

    if computation.is_success:
        return (
            current_block,
            computation.vm_state.receipts,
            merge(recent_trie_nodes_db, computation.vm_state.access_logs.writes),
            merge(trie_data_dict, recent_trie_data_dict)
        )
    else:
        return current_block, receipts, recent_trie_nodes_db, recent_trie_data_dict


@curry
def apply_single_transaction_with_transaction_package(
        transaction_package,
        state_class,
        account_state_class,
        execution_context,
        params):

    current_block, receipts, recent_trie_nodes_db, recent_trie_data_dict, block_witness = params
    transaction, transaction_witness = transaction_package
    witness_db = update_witness_db(
        witness=transaction_witness,
        recent_trie_nodes_db=recent_trie_nodes_db,
        account_state_class=account_state_class,
    )

    computation, current_block, trie_data_dict = apply_state_transition_with_witness(
        witness_db,
        transaction,
        current_block,
        receipts,
        state_class,
        execution_context)

    if computation.is_success:
        block_witness.update(transaction_witness)
        return (
            current_block,
            computation.vm_state.receipts,
            merge(recent_trie_nodes_db, computation.vm_state.access_logs.writes),
            merge(trie_data_dict, recent_trie_data_dict),
            block_witness
        )
    else:
        pass
