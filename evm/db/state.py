import logging

import rlp

from trie import (
    HexaryTrie
)

from evm.constants import (
    BLANK_ROOT_HASH,
    EMPTY_SHA3,
    BALANCE_TRIE_PREFIX,
    CODE_TRIE_PREFIX,
    NONCE_TRIE_PREFIX,
)
from evm.exceptions import (
    UnannouncedStateAccess,
)
from evm.db.immutable import (
    ImmutableDB,
)
from evm.db.tracked import (
    TrackedDB,
)
from evm.rlp.accounts import (
    Account,
)
from evm.validation import (
    validate_is_bytes,
    validate_uint256,
    validate_canonical_address,
)

from evm.utils.state_access_restriction import (
    is_accessible,
)
from evm.utils.keccak import (
    keccak,
)
from evm.utils.numeric import (
    int_to_big_endian,
)
from evm.utils.padding import (
    pad32,
)

from .hash_trie import HashTrie

class TwoLayerBackend:
    def __init__(self, db, root_hash=BLANK_ROOT_HASH, access_list=None):
        self.db = db
        self._trie = HashTrie(HexaryTrie(self.db, root_hash))
        if access_list is not None:
            raise NotImplementedError(
                "State access restriction not implemented for two layer trie"
            )

    def decommission(self):
        self.db = None
        self._trie = None

    @property
    def root_hash(self):
        return self._trie.root_hash

    @root_hash.setter
    def root_hash(self, value):
        self._trie.root_hash = value

    def set_storage(self, address, slot, value):
        account = self._get_account(address)
        storage = HashTrie(HexaryTrie(self.db, account.storage_root))

        slot_as_key = pad32(int_to_big_endian(slot))

        if value:
            encoded_value = rlp.encode(value)
            storage[slot_as_key] = encoded_value
        else:
            del storage[slot_as_key]

        account.storage_root = storage.root_hash
        self._set_account(address, account)

    def get_storage(self, address, slot):
        account = self._get_account(address)
        storage = HashTrie(HexaryTrie(self.db, account.storage_root))

        slot_as_key = pad32(int_to_big_endian(slot))

        if slot_as_key in storage:
            encoded_value = storage[slot_as_key]
            return rlp.decode(encoded_value, sedes=rlp.sedes.big_endian_int)
        else:
            return 0

    def delete_storage(self, address):
        account = self._get_account(address)
        account.storage_root = BLANK_ROOT_HASH
        self._set_account(address, account)

    def set_balance(self, address, balance):
        account = self._get_account(address)
        account.balance = balance

        self._set_account(address, account)

    def get_balance(self, address):
        account = self._get_account(address)
        return account.balance

    def set_nonce(self, address, nonce):
        account = self._get_account(address)
        account.nonce = nonce

        self._set_account(address, account)

    def get_nonce(self, address):
        account = self._get_account(address)
        return account.nonce

    def set_code(self, address, code):
        account = self._get_account(address)

        account.code_hash = keccak(code)
        self.db[account.code_hash] = code
        self._set_account(address, account)

    def get_code(self, address):
        try:
            return self.db[self.get_code_hash(address)]
        except KeyError:
            return b''

    def get_code_hash(self, address):
        account = self._get_account(address)
        return account.code_hash

    def delete_code(self, address):
        account = self._get_account(address)
        account.code_hash = EMPTY_SHA3
        self._set_account(address, account)

    #
    # Account Methods
    #
    def delete_account(self, address):
        del self._trie[address]

    def account_exists(self, address):
        return bool(self._trie[address])

    def touch_account(self, address):
        account = self._get_account(address)
        self._set_account(address, account)

    #
    # Internal
    #
    def _get_account(self, address):
        rlp_account = self._trie[address]
        if rlp_account:
            account = rlp.decode(rlp_account, sedes=Account)
            account._mutable = True
        else:
            account = Account()
        return account

    def _set_account(self, address, account):
        self._trie[address] = rlp.encode(account, sedes=Account)


class AccountStateDB:
    """
    High level API around account storage.
    """
    db = None
    _trie = None

    logger = logging.getLogger('evm.state.State')

    def __init__(
        self,
        db,
        root_hash=BLANK_ROOT_HASH,
        read_only=False,
        access_list=None,
        backend_class=TwoLayerBackend
    ):
        if read_only:
            self.db = ImmutableDB(db)
        else:
            self.db = TrackedDB(db)
        self.backend = backend_class(self.db, root_hash, access_list)

    def decommission(self):
        self.backend.decommission()
        self.db = None

    #
    # Base API
    #
    @property
    def root_hash(self):
        return self.backend.root_hash

    @root_hash.setter
    def root_hash(self, value):
        self.backend.root_hash = value

    def set_storage(self, address, slot, value):
        validate_uint256(value, title="Storage Value")
        validate_uint256(slot, title="Storage Slot")
        validate_canonical_address(address, title="Storage Address")
        self.backend.set_storage(address, slot, value)

    def get_storage(self, address, slot):
        validate_canonical_address(address, title="Storage Address")
        validate_uint256(slot, title="Storage Slot")
        return self.backend.get_storage(address, slot)

    def delete_storage(self, address):
        validate_canonical_address(address, title="Storage Address")
        self.backend.delete_storage(address)

    def set_balance(self, address, balance):
        validate_canonical_address(address, title="Storage Address")
        validate_uint256(balance, title="Account Balance")
        self.backend.set_balance(address, balance)

    def delta_balance(self, address, delta):
        self.set_balance(address, self.get_balance(address) + delta)

    def get_balance(self, address):
        validate_canonical_address(address, title="Storage Address")
        return self.backend.get_balance(address)

    def set_nonce(self, address, nonce):
        validate_canonical_address(address, title="Storage Address")
        validate_uint256(nonce, title="Nonce")
        self.backend.set_nonce(address, nonce)

    def get_nonce(self, address):
        validate_canonical_address(address, title="Storage Address")
        return self.backend.get_nonce(address)

    def set_code(self, address, code):
        validate_canonical_address(address, title="Storage Address")
        validate_is_bytes(code, title="Code")
        self.backend.set_code(address, code)

    def get_code(self, address):
        validate_canonical_address(address, title="Storage Address")
        return self.backend.get_code(address)

    def delete_code(self, address):
        validate_canonical_address(address, title="Storage Address")
        self.backend.delete_code(address)

    #
    # Account Methods
    #
    def delete_account(self, address):
        validate_canonical_address(address, title="Storage Address")
        self.backend.delete_account(address)

    def account_exists(self, address):
        validate_canonical_address(address, title="Storage Address")
        return self.backend.account_exists(address)

    def account_has_code_or_nonce(self, address):
        validate_canonical_address(address, title="Storage Address")
        return self.backend.account_has_code_or_nonce(address)

    def account_is_empty(self, address):
        return not self.account_has_code_or_nonce(address) and self.get_balance(address) == 0

    def touch_account(self, address):
        validate_canonical_address(address, title="Storage Address")
        self.backend.touch_account(address)

    def increment_nonce(self, address):
        current_nonce = self.get_nonce(address)
        self.set_nonce(address, current_nonce + 1)
