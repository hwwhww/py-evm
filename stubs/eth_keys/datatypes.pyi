import collections
from typing import (
    Any,
    Optional,
    Tuple,
    Type,
    Union
)

from backends.base import BaseECCBackend

class LazyBackend:
    def __init__(
            self,
            backend: 'Union[BaseECCBackend, Type[BaseECCBackend], str]'=None
            ) -> None: ...

    @property
    def backend(self) -> BaseECCBackend: ...
    @classmethod
    def get_backend(cls) -> BaseECCBackend: ...

class BaseKey(collections.abc.ByteString, collections.Hashable):
    def to_hex(self) -> str: ...
    def to_bytes(self) -> bytes: ...
    def __hash__(self) -> int: ...
    def __int__(self) -> int: ...
    def __len__(self) -> int: ...
    def __getitem__(self, index: int) -> int: ...  # type: ignore
    def __eq__(self, other: Any) -> bool: ...
    def __index__(self) -> int: ...
    def __hex__(self) -> str: ...

class PublicKey(BaseKey, LazyBackend):
    def __init__(self, public_key_bytes: bytes) -> None: ...
    @classmethod
    def from_private(cls, private_key: PrivateKey) -> PublicKey: ...
    @classmethod
    def recover_from_msg(cls, message: bytes, signature: Signature) -> PublicKey: ...
    @classmethod
    def recover_from_msg_hash(cls, message_hash: bytes, signature: Signature) -> PublicKey: ...
    def verify_msg(self, message: bytes, signature: Signature) -> bool: ...
    def verify_msg_hash(self, message_hash: bytes, signature: Signature) -> bool: ...
    def to_checksum_address(self) -> bytes: ...
    def to_address(self) -> bytes: ...
    def to_canonical_address(self) -> bytes: ...

class PrivateKey(BaseKey, LazyBackend):
    public_key: PublicKey = ...
    def __init__(self, private_key_bytes: bytes) -> None: ...
    def sign_msg(self, message: bytes) -> Signature: ...
    def sign_msg_hash(self, message_hash: bytes) -> Signature: ...

class Signature(collections.abc.ByteString, LazyBackend):
    r: int = ...
    s: int = ...
    v: int = ...
    def __init__(self, signature_bytes: Optional[bytes]=..., vrs: Optional[Tuple[int, int, int]]=...) -> None: ...
    @property
    def v(self) -> int: ...
    @v.setter
    def v(self, value: int) -> None: ...
    @property
    def r(self) -> int: ...
    @r.setter
    def r(self, value: int) -> None: ...
    @property
    def s(self) -> int: ...
    @s.setter
    def s(self, value: int) -> None: ...
    @property
    def vrs(self) -> Tuple[int, int, int]: ...
    def to_hex(self) -> str: ...
    def to_bytes(self) -> bytes: ...
    def __hash__(self) -> int: ...
    def __bytes__(self) -> bytes: ...
    def __len__(self) -> int: ...
    def __eq__(self, other: Any) -> bool: ...
    def __getitem__(self, index: int) -> int: ...  # type: ignore
    def verify_msg(self, message: bytes, public_key: PublicKey) -> bool: ...
    def verify_msg_hash(self, message_hash: bytes, public_key: PublicKey) -> bool: ...
    def recover_public_key_from_msg(self, message: bytes) -> PublicKey: ...
    def recover_public_key_from_msg_hash(self, message_hash: bytes) -> PublicKey: ...
    def __index__(self) -> int: ...
    def __hex__(self) -> str: ...
    def __int__(self) -> int: ...
