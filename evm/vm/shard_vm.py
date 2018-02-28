from cytoolz import (
    pipe,
)

from eth_utils import (
    keccak,
)
import rlp
from trie import (
    BinaryTrie,
)

from evm.db.backends.memory import MemoryDB
from evm.db.chain import ChainDB
from evm.utils.state import (
    apply_single_transaction,
    apply_single_transaction_with_transaction_package,
    update_witness_db,
)

from .base import (
    BaseVM,
)
from .execution_context import (
    ExecutionContext,
)


class ShardVM(BaseVM):
    #
    # Apply block
    #
    def apply_block_with_witness(self, block, witness):
        self.configure_header(
            coinbase=block.header.coinbase,
            gas_limit=block.header.gas_limit,
            timestamp=block.header.timestamp,
            extra_data=block.header.extra_data,
            mix_hash=block.header.mix_hash,
            nonce=block.header.nonce,
            uncles_hash=keccak(rlp.encode(block.uncles)),
        )

        receipts = []
        recent_trie_nodes_db = dict([(keccak(value), value) for value in witness])
        recent_trie_data_dict = {}
        prev_hashes = self.previous_hashes
        state_class = self.get_state_class()
        account_state_class = self.chaindb.account_state_class
        execution_context = ExecutionContext.from_block_header(block.header, prev_hashes)

        txn_applicators = [
            apply_single_transaction(
                transaction,
                state_class,
                account_state_class,
                execution_context,
            ) for transaction in block.transactions
        ]
        result_block, receipts, trie_nodes, trie_dict = pipe(
            [self.block, receipts, recent_trie_nodes_db, recent_trie_data_dict],
            *txn_applicators
        )
        self.chaindb.persist_trie_data_dict_to_db(trie_dict)

        # transfer the list of uncles.
        self.block = result_block
        self.block.uncles = result_block.uncles

        witness_db = ChainDB(
            MemoryDB(trie_nodes),
            account_state_class=account_state_class,
            trie_class=BinaryTrie,
        )

        return self.mine_block_stateless(witness_db, receipts)

    def mine_block_stateless(self, witness_db, receipts, *args, **kwargs):
        """
        Mine the current block. Proxies to self.pack_block method.
        """
        block = self.block
        self.pack_block(block, *args, **kwargs)

        if block.number == 0:
            return block

        execution_context = ExecutionContext.from_block_header(
            block.header,
            self.previous_hashes
        )

        vm_state = self.get_state_class()(
            chaindb=witness_db,
            execution_context=execution_context,
            state_root=block.header.state_root,
            receipts=receipts,
        )
        block = vm_state.finalize_block(block)

        return block

    @classmethod
    def build_block(
            cls,
            witness_package,
            prev_hashes,
            parent_header,
            account_state_class):
        """
        Build a block with transaction witness
        """
        block = cls.generate_block_from_parent_header_and_coinbase(
            parent_header,
            witness_package.coinbase,
        )
        receipts = []
        recent_trie_nodes_db = {}
        recent_trie_data_dict = {}
        block_witness = set()
        transaction_packages = witness_package.transaction_packages
        state_class = cls.get_state_class()
        execution_context = ExecutionContext.from_block_header(block.header, prev_hashes)

        txn_applicators = [
            apply_single_transaction_with_transaction_package(
                transaction_package,
                state_class,
                account_state_class,
                execution_context,
            ) for transaction_package in transaction_packages
        ]
        result_block, receipts, trie_nodes, _, block_witness = pipe(
            [block, receipts, recent_trie_nodes_db, recent_trie_data_dict, block_witness],
            *txn_applicators
        )

        # Finalize
        # For sharding, ignore uncles and nephews.
        witness_db = update_witness_db(
            witness=witness_package.coinbase_witness,
            recent_trie_nodes_db=trie_nodes,
            account_state_class=account_state_class,
        )

        # execution_context = ExecutionContext.from_block_header(block.header, prev_hashes)
        vm_state = cls.get_state_class()(
            chaindb=witness_db,
            execution_context=execution_context,
            state_root=result_block.header.state_root,
            receipts=receipts,
        )
        block = vm_state.finalize_block(result_block)
        block_witness.update(witness_package.coinbase_witness)
        return block, block_witness
