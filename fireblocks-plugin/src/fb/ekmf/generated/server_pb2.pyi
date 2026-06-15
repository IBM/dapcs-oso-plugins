from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class GenerateRandomRequest(_message.Message):
    __slots__ = ("Len",)
    LEN_FIELD_NUMBER: _ClassVar[int]
    Len: int
    def __init__(self, Len: _Optional[int] = ...) -> None: ...

class GenerateRandomResponse(_message.Message):
    __slots__ = ("Rnd",)
    RND_FIELD_NUMBER: _ClassVar[int]
    Rnd: bytes
    def __init__(self, Rnd: _Optional[bytes] = ...) -> None: ...

class DigestInitRequest(_message.Message):
    __slots__ = ("Mech",)
    MECH_FIELD_NUMBER: _ClassVar[int]
    Mech: Mechanism
    def __init__(self, Mech: _Optional[_Union[Mechanism, _Mapping]] = ...) -> None: ...

class DigestInitResponse(_message.Message):
    __slots__ = ("State",)
    STATE_FIELD_NUMBER: _ClassVar[int]
    State: bytes
    def __init__(self, State: _Optional[bytes] = ...) -> None: ...

class DigestRequest(_message.Message):
    __slots__ = ("State", "Data")
    STATE_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    State: bytes
    Data: bytes
    def __init__(self, State: _Optional[bytes] = ..., Data: _Optional[bytes] = ...) -> None: ...

class DigestResponse(_message.Message):
    __slots__ = ("Digest",)
    DIGEST_FIELD_NUMBER: _ClassVar[int]
    Digest: bytes
    def __init__(self, Digest: _Optional[bytes] = ...) -> None: ...

class DigestUpdateRequest(_message.Message):
    __slots__ = ("State", "Data")
    STATE_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    State: bytes
    Data: bytes
    def __init__(self, State: _Optional[bytes] = ..., Data: _Optional[bytes] = ...) -> None: ...

class DigestUpdateResponse(_message.Message):
    __slots__ = ("State",)
    STATE_FIELD_NUMBER: _ClassVar[int]
    State: bytes
    def __init__(self, State: _Optional[bytes] = ...) -> None: ...

class DigestKeyRequest(_message.Message):
    __slots__ = ("State", "Key")
    STATE_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    State: bytes
    Key: KeyBlob
    def __init__(self, State: _Optional[bytes] = ..., Key: _Optional[_Union[KeyBlob, _Mapping]] = ...) -> None: ...

class DigestKeyResponse(_message.Message):
    __slots__ = ("State",)
    STATE_FIELD_NUMBER: _ClassVar[int]
    State: bytes
    def __init__(self, State: _Optional[bytes] = ...) -> None: ...

class DigestFinalRequest(_message.Message):
    __slots__ = ("State",)
    STATE_FIELD_NUMBER: _ClassVar[int]
    State: bytes
    def __init__(self, State: _Optional[bytes] = ...) -> None: ...

class DigestFinalResponse(_message.Message):
    __slots__ = ("Digest",)
    DIGEST_FIELD_NUMBER: _ClassVar[int]
    Digest: bytes
    def __init__(self, Digest: _Optional[bytes] = ...) -> None: ...

class DigestSingleRequest(_message.Message):
    __slots__ = ("Mech", "Data")
    MECH_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    Mech: Mechanism
    Data: bytes
    def __init__(self, Mech: _Optional[_Union[Mechanism, _Mapping]] = ..., Data: _Optional[bytes] = ...) -> None: ...

class DigestSingleResponse(_message.Message):
    __slots__ = ("Digest",)
    DIGEST_FIELD_NUMBER: _ClassVar[int]
    Digest: bytes
    def __init__(self, Digest: _Optional[bytes] = ...) -> None: ...

class EncryptInitRequest(_message.Message):
    __slots__ = ("Mech", "Key")
    MECH_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    Mech: Mechanism
    Key: KeyBlob
    def __init__(self, Mech: _Optional[_Union[Mechanism, _Mapping]] = ..., Key: _Optional[_Union[KeyBlob, _Mapping]] = ...) -> None: ...

class EncryptInitResponse(_message.Message):
    __slots__ = ("State",)
    STATE_FIELD_NUMBER: _ClassVar[int]
    State: bytes
    def __init__(self, State: _Optional[bytes] = ...) -> None: ...

class DecryptInitRequest(_message.Message):
    __slots__ = ("Mech", "Key")
    MECH_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    Mech: Mechanism
    Key: KeyBlob
    def __init__(self, Mech: _Optional[_Union[Mechanism, _Mapping]] = ..., Key: _Optional[_Union[KeyBlob, _Mapping]] = ...) -> None: ...

class DecryptInitResponse(_message.Message):
    __slots__ = ("State",)
    STATE_FIELD_NUMBER: _ClassVar[int]
    State: bytes
    def __init__(self, State: _Optional[bytes] = ...) -> None: ...

class EncryptUpdateRequest(_message.Message):
    __slots__ = ("State", "Plain")
    STATE_FIELD_NUMBER: _ClassVar[int]
    PLAIN_FIELD_NUMBER: _ClassVar[int]
    State: bytes
    Plain: bytes
    def __init__(self, State: _Optional[bytes] = ..., Plain: _Optional[bytes] = ...) -> None: ...

class EncryptUpdateResponse(_message.Message):
    __slots__ = ("State", "Ciphered")
    STATE_FIELD_NUMBER: _ClassVar[int]
    CIPHERED_FIELD_NUMBER: _ClassVar[int]
    State: bytes
    Ciphered: bytes
    def __init__(self, State: _Optional[bytes] = ..., Ciphered: _Optional[bytes] = ...) -> None: ...

class DecryptUpdateRequest(_message.Message):
    __slots__ = ("State", "Ciphered")
    STATE_FIELD_NUMBER: _ClassVar[int]
    CIPHERED_FIELD_NUMBER: _ClassVar[int]
    State: bytes
    Ciphered: bytes
    def __init__(self, State: _Optional[bytes] = ..., Ciphered: _Optional[bytes] = ...) -> None: ...

class DecryptUpdateResponse(_message.Message):
    __slots__ = ("State", "Plain")
    STATE_FIELD_NUMBER: _ClassVar[int]
    PLAIN_FIELD_NUMBER: _ClassVar[int]
    State: bytes
    Plain: bytes
    def __init__(self, State: _Optional[bytes] = ..., Plain: _Optional[bytes] = ...) -> None: ...

class EncryptRequest(_message.Message):
    __slots__ = ("State", "Plain")
    STATE_FIELD_NUMBER: _ClassVar[int]
    PLAIN_FIELD_NUMBER: _ClassVar[int]
    State: bytes
    Plain: bytes
    def __init__(self, State: _Optional[bytes] = ..., Plain: _Optional[bytes] = ...) -> None: ...

class EncryptResponse(_message.Message):
    __slots__ = ("Ciphered",)
    CIPHERED_FIELD_NUMBER: _ClassVar[int]
    Ciphered: bytes
    def __init__(self, Ciphered: _Optional[bytes] = ...) -> None: ...

class DecryptRequest(_message.Message):
    __slots__ = ("State", "Ciphered")
    STATE_FIELD_NUMBER: _ClassVar[int]
    CIPHERED_FIELD_NUMBER: _ClassVar[int]
    State: bytes
    Ciphered: bytes
    def __init__(self, State: _Optional[bytes] = ..., Ciphered: _Optional[bytes] = ...) -> None: ...

class DecryptResponse(_message.Message):
    __slots__ = ("Plain",)
    PLAIN_FIELD_NUMBER: _ClassVar[int]
    Plain: bytes
    def __init__(self, Plain: _Optional[bytes] = ...) -> None: ...

class EncryptFinalRequest(_message.Message):
    __slots__ = ("State",)
    STATE_FIELD_NUMBER: _ClassVar[int]
    State: bytes
    def __init__(self, State: _Optional[bytes] = ...) -> None: ...

class EncryptFinalResponse(_message.Message):
    __slots__ = ("Ciphered",)
    CIPHERED_FIELD_NUMBER: _ClassVar[int]
    Ciphered: bytes
    def __init__(self, Ciphered: _Optional[bytes] = ...) -> None: ...

class DecryptFinalRequest(_message.Message):
    __slots__ = ("State",)
    STATE_FIELD_NUMBER: _ClassVar[int]
    State: bytes
    def __init__(self, State: _Optional[bytes] = ...) -> None: ...

class DecryptFinalResponse(_message.Message):
    __slots__ = ("Plain",)
    PLAIN_FIELD_NUMBER: _ClassVar[int]
    Plain: bytes
    def __init__(self, Plain: _Optional[bytes] = ...) -> None: ...

class EncryptSingleRequest(_message.Message):
    __slots__ = ("Mech", "Plain", "Key")
    MECH_FIELD_NUMBER: _ClassVar[int]
    PLAIN_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    Mech: Mechanism
    Plain: bytes
    Key: KeyBlob
    def __init__(self, Mech: _Optional[_Union[Mechanism, _Mapping]] = ..., Plain: _Optional[bytes] = ..., Key: _Optional[_Union[KeyBlob, _Mapping]] = ...) -> None: ...

class EncryptSingleResponse(_message.Message):
    __slots__ = ("Ciphered",)
    CIPHERED_FIELD_NUMBER: _ClassVar[int]
    Ciphered: bytes
    def __init__(self, Ciphered: _Optional[bytes] = ...) -> None: ...

class DecryptSingleRequest(_message.Message):
    __slots__ = ("Mech", "Ciphered", "Key")
    MECH_FIELD_NUMBER: _ClassVar[int]
    CIPHERED_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    Mech: Mechanism
    Ciphered: bytes
    Key: KeyBlob
    def __init__(self, Mech: _Optional[_Union[Mechanism, _Mapping]] = ..., Ciphered: _Optional[bytes] = ..., Key: _Optional[_Union[KeyBlob, _Mapping]] = ...) -> None: ...

class DecryptSingleResponse(_message.Message):
    __slots__ = ("Plain",)
    PLAIN_FIELD_NUMBER: _ClassVar[int]
    Plain: bytes
    def __init__(self, Plain: _Optional[bytes] = ...) -> None: ...

class SignInitRequest(_message.Message):
    __slots__ = ("Mech", "PrivKey")
    MECH_FIELD_NUMBER: _ClassVar[int]
    PRIVKEY_FIELD_NUMBER: _ClassVar[int]
    Mech: Mechanism
    PrivKey: KeyBlob
    def __init__(self, Mech: _Optional[_Union[Mechanism, _Mapping]] = ..., PrivKey: _Optional[_Union[KeyBlob, _Mapping]] = ...) -> None: ...

class SignInitResponse(_message.Message):
    __slots__ = ("State",)
    STATE_FIELD_NUMBER: _ClassVar[int]
    State: bytes
    def __init__(self, State: _Optional[bytes] = ...) -> None: ...

class VerifyInitRequest(_message.Message):
    __slots__ = ("Mech", "PubKey")
    MECH_FIELD_NUMBER: _ClassVar[int]
    PUBKEY_FIELD_NUMBER: _ClassVar[int]
    Mech: Mechanism
    PubKey: KeyBlob
    def __init__(self, Mech: _Optional[_Union[Mechanism, _Mapping]] = ..., PubKey: _Optional[_Union[KeyBlob, _Mapping]] = ...) -> None: ...

class VerifyInitResponse(_message.Message):
    __slots__ = ("State",)
    STATE_FIELD_NUMBER: _ClassVar[int]
    State: bytes
    def __init__(self, State: _Optional[bytes] = ...) -> None: ...

class SignUpdateRequest(_message.Message):
    __slots__ = ("State", "Data")
    STATE_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    State: bytes
    Data: bytes
    def __init__(self, State: _Optional[bytes] = ..., Data: _Optional[bytes] = ...) -> None: ...

class SignUpdateResponse(_message.Message):
    __slots__ = ("State",)
    STATE_FIELD_NUMBER: _ClassVar[int]
    State: bytes
    def __init__(self, State: _Optional[bytes] = ...) -> None: ...

class VerifyUpdateRequest(_message.Message):
    __slots__ = ("State", "Data")
    STATE_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    State: bytes
    Data: bytes
    def __init__(self, State: _Optional[bytes] = ..., Data: _Optional[bytes] = ...) -> None: ...

class VerifyUpdateResponse(_message.Message):
    __slots__ = ("State",)
    STATE_FIELD_NUMBER: _ClassVar[int]
    State: bytes
    def __init__(self, State: _Optional[bytes] = ...) -> None: ...

class SignFinalRequest(_message.Message):
    __slots__ = ("State",)
    STATE_FIELD_NUMBER: _ClassVar[int]
    State: bytes
    def __init__(self, State: _Optional[bytes] = ...) -> None: ...

class SignFinalResponse(_message.Message):
    __slots__ = ("Signature",)
    SIGNATURE_FIELD_NUMBER: _ClassVar[int]
    Signature: bytes
    def __init__(self, Signature: _Optional[bytes] = ...) -> None: ...

class VerifyFinalRequest(_message.Message):
    __slots__ = ("State", "Signature")
    STATE_FIELD_NUMBER: _ClassVar[int]
    SIGNATURE_FIELD_NUMBER: _ClassVar[int]
    State: bytes
    Signature: bytes
    def __init__(self, State: _Optional[bytes] = ..., Signature: _Optional[bytes] = ...) -> None: ...

class VerifyFinalResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class SignRequest(_message.Message):
    __slots__ = ("State", "Data")
    STATE_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    State: bytes
    Data: bytes
    def __init__(self, State: _Optional[bytes] = ..., Data: _Optional[bytes] = ...) -> None: ...

class SignResponse(_message.Message):
    __slots__ = ("Signature",)
    SIGNATURE_FIELD_NUMBER: _ClassVar[int]
    Signature: bytes
    def __init__(self, Signature: _Optional[bytes] = ...) -> None: ...

class VerifyRequest(_message.Message):
    __slots__ = ("State", "Data", "Signature")
    STATE_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    SIGNATURE_FIELD_NUMBER: _ClassVar[int]
    State: bytes
    Data: bytes
    Signature: bytes
    def __init__(self, State: _Optional[bytes] = ..., Data: _Optional[bytes] = ..., Signature: _Optional[bytes] = ...) -> None: ...

class VerifyResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class SignSingleRequest(_message.Message):
    __slots__ = ("Mech", "Data", "PrivKey")
    MECH_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    PRIVKEY_FIELD_NUMBER: _ClassVar[int]
    Mech: Mechanism
    Data: bytes
    PrivKey: KeyBlob
    def __init__(self, Mech: _Optional[_Union[Mechanism, _Mapping]] = ..., Data: _Optional[bytes] = ..., PrivKey: _Optional[_Union[KeyBlob, _Mapping]] = ...) -> None: ...

class SignSingleResponse(_message.Message):
    __slots__ = ("Signature",)
    SIGNATURE_FIELD_NUMBER: _ClassVar[int]
    Signature: bytes
    def __init__(self, Signature: _Optional[bytes] = ...) -> None: ...

class VerifySingleRequest(_message.Message):
    __slots__ = ("Mech", "Data", "Signature", "PubKey")
    MECH_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    SIGNATURE_FIELD_NUMBER: _ClassVar[int]
    PUBKEY_FIELD_NUMBER: _ClassVar[int]
    Mech: Mechanism
    Data: bytes
    Signature: bytes
    PubKey: KeyBlob
    def __init__(self, Mech: _Optional[_Union[Mechanism, _Mapping]] = ..., Data: _Optional[bytes] = ..., Signature: _Optional[bytes] = ..., PubKey: _Optional[_Union[KeyBlob, _Mapping]] = ...) -> None: ...

class VerifySingleResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ReencryptSingleRequest(_message.Message):
    __slots__ = ("DecMech", "EncMech", "Ciphered", "DecKey", "EncKey")
    DECMECH_FIELD_NUMBER: _ClassVar[int]
    ENCMECH_FIELD_NUMBER: _ClassVar[int]
    CIPHERED_FIELD_NUMBER: _ClassVar[int]
    DECKEY_FIELD_NUMBER: _ClassVar[int]
    ENCKEY_FIELD_NUMBER: _ClassVar[int]
    DecMech: Mechanism
    EncMech: Mechanism
    Ciphered: bytes
    DecKey: KeyBlob
    EncKey: KeyBlob
    def __init__(self, DecMech: _Optional[_Union[Mechanism, _Mapping]] = ..., EncMech: _Optional[_Union[Mechanism, _Mapping]] = ..., Ciphered: _Optional[bytes] = ..., DecKey: _Optional[_Union[KeyBlob, _Mapping]] = ..., EncKey: _Optional[_Union[KeyBlob, _Mapping]] = ...) -> None: ...

class ReencryptSingleResponse(_message.Message):
    __slots__ = ("Reciphered",)
    RECIPHERED_FIELD_NUMBER: _ClassVar[int]
    Reciphered: bytes
    def __init__(self, Reciphered: _Optional[bytes] = ...) -> None: ...

class GenerateKeyRequest(_message.Message):
    __slots__ = ("Mech", "Template")
    class TemplateEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: int
        value: AttributeValue
        def __init__(self, key: _Optional[int] = ..., value: _Optional[_Union[AttributeValue, _Mapping]] = ...) -> None: ...
    MECH_FIELD_NUMBER: _ClassVar[int]
    TEMPLATE_FIELD_NUMBER: _ClassVar[int]
    Mech: Mechanism
    Template: _containers.MessageMap[int, AttributeValue]
    def __init__(self, Mech: _Optional[_Union[Mechanism, _Mapping]] = ..., Template: _Optional[_Mapping[int, AttributeValue]] = ...) -> None: ...

class GenerateKeyResponse(_message.Message):
    __slots__ = ("KeyBytes", "CheckSum", "Key")
    KEYBYTES_FIELD_NUMBER: _ClassVar[int]
    CHECKSUM_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    KeyBytes: bytes
    CheckSum: bytes
    Key: KeyBlob
    def __init__(self, KeyBytes: _Optional[bytes] = ..., CheckSum: _Optional[bytes] = ..., Key: _Optional[_Union[KeyBlob, _Mapping]] = ...) -> None: ...

class GenerateKeyPairRequest(_message.Message):
    __slots__ = ("Mech", "PrivKeyTemplate", "PubKeyTemplate")
    class PrivKeyTemplateEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: int
        value: AttributeValue
        def __init__(self, key: _Optional[int] = ..., value: _Optional[_Union[AttributeValue, _Mapping]] = ...) -> None: ...
    class PubKeyTemplateEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: int
        value: AttributeValue
        def __init__(self, key: _Optional[int] = ..., value: _Optional[_Union[AttributeValue, _Mapping]] = ...) -> None: ...
    MECH_FIELD_NUMBER: _ClassVar[int]
    PRIVKEYTEMPLATE_FIELD_NUMBER: _ClassVar[int]
    PUBKEYTEMPLATE_FIELD_NUMBER: _ClassVar[int]
    Mech: Mechanism
    PrivKeyTemplate: _containers.MessageMap[int, AttributeValue]
    PubKeyTemplate: _containers.MessageMap[int, AttributeValue]
    def __init__(self, Mech: _Optional[_Union[Mechanism, _Mapping]] = ..., PrivKeyTemplate: _Optional[_Mapping[int, AttributeValue]] = ..., PubKeyTemplate: _Optional[_Mapping[int, AttributeValue]] = ...) -> None: ...

class GenerateKeyPairResponse(_message.Message):
    __slots__ = ("PrivKeyBytes", "PubKeyBytes", "PrivKey", "PubKey")
    PRIVKEYBYTES_FIELD_NUMBER: _ClassVar[int]
    PUBKEYBYTES_FIELD_NUMBER: _ClassVar[int]
    PRIVKEY_FIELD_NUMBER: _ClassVar[int]
    PUBKEY_FIELD_NUMBER: _ClassVar[int]
    PrivKeyBytes: bytes
    PubKeyBytes: bytes
    PrivKey: KeyBlob
    PubKey: KeyBlob
    def __init__(self, PrivKeyBytes: _Optional[bytes] = ..., PubKeyBytes: _Optional[bytes] = ..., PrivKey: _Optional[_Union[KeyBlob, _Mapping]] = ..., PubKey: _Optional[_Union[KeyBlob, _Mapping]] = ...) -> None: ...

class WrapKeyRequest(_message.Message):
    __slots__ = ("Mech", "Key", "KeK", "MacKey")
    MECH_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    KEK_FIELD_NUMBER: _ClassVar[int]
    MACKEY_FIELD_NUMBER: _ClassVar[int]
    Mech: Mechanism
    Key: KeyBlob
    KeK: KeyBlob
    MacKey: KeyBlob
    def __init__(self, Mech: _Optional[_Union[Mechanism, _Mapping]] = ..., Key: _Optional[_Union[KeyBlob, _Mapping]] = ..., KeK: _Optional[_Union[KeyBlob, _Mapping]] = ..., MacKey: _Optional[_Union[KeyBlob, _Mapping]] = ...) -> None: ...

class WrapKeyResponse(_message.Message):
    __slots__ = ("Wrapped",)
    WRAPPED_FIELD_NUMBER: _ClassVar[int]
    Wrapped: bytes
    def __init__(self, Wrapped: _Optional[bytes] = ...) -> None: ...

class UnwrapKeyRequest(_message.Message):
    __slots__ = ("Wrapped", "Mech", "Template", "KeK", "MacKey")
    class TemplateEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: int
        value: AttributeValue
        def __init__(self, key: _Optional[int] = ..., value: _Optional[_Union[AttributeValue, _Mapping]] = ...) -> None: ...
    WRAPPED_FIELD_NUMBER: _ClassVar[int]
    MECH_FIELD_NUMBER: _ClassVar[int]
    TEMPLATE_FIELD_NUMBER: _ClassVar[int]
    KEK_FIELD_NUMBER: _ClassVar[int]
    MACKEY_FIELD_NUMBER: _ClassVar[int]
    Wrapped: bytes
    Mech: Mechanism
    Template: _containers.MessageMap[int, AttributeValue]
    KeK: KeyBlob
    MacKey: KeyBlob
    def __init__(self, Wrapped: _Optional[bytes] = ..., Mech: _Optional[_Union[Mechanism, _Mapping]] = ..., Template: _Optional[_Mapping[int, AttributeValue]] = ..., KeK: _Optional[_Union[KeyBlob, _Mapping]] = ..., MacKey: _Optional[_Union[KeyBlob, _Mapping]] = ...) -> None: ...

class UnwrapKeyResponse(_message.Message):
    __slots__ = ("UnwrappedBytes", "CheckSum", "Unwrapped")
    UNWRAPPEDBYTES_FIELD_NUMBER: _ClassVar[int]
    CHECKSUM_FIELD_NUMBER: _ClassVar[int]
    UNWRAPPED_FIELD_NUMBER: _ClassVar[int]
    UnwrappedBytes: bytes
    CheckSum: bytes
    Unwrapped: KeyBlob
    def __init__(self, UnwrappedBytes: _Optional[bytes] = ..., CheckSum: _Optional[bytes] = ..., Unwrapped: _Optional[_Union[KeyBlob, _Mapping]] = ...) -> None: ...

class DeriveKeyRequest(_message.Message):
    __slots__ = ("Mech", "Data", "Template", "BaseKey")
    class TemplateEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: int
        value: AttributeValue
        def __init__(self, key: _Optional[int] = ..., value: _Optional[_Union[AttributeValue, _Mapping]] = ...) -> None: ...
    MECH_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    TEMPLATE_FIELD_NUMBER: _ClassVar[int]
    BASEKEY_FIELD_NUMBER: _ClassVar[int]
    Mech: Mechanism
    Data: bytes
    Template: _containers.MessageMap[int, AttributeValue]
    BaseKey: KeyBlob
    def __init__(self, Mech: _Optional[_Union[Mechanism, _Mapping]] = ..., Data: _Optional[bytes] = ..., Template: _Optional[_Mapping[int, AttributeValue]] = ..., BaseKey: _Optional[_Union[KeyBlob, _Mapping]] = ...) -> None: ...

class DeriveKeyResponse(_message.Message):
    __slots__ = ("NewKeyBytes", "CheckSum", "NewKey")
    NEWKEYBYTES_FIELD_NUMBER: _ClassVar[int]
    CHECKSUM_FIELD_NUMBER: _ClassVar[int]
    NEWKEY_FIELD_NUMBER: _ClassVar[int]
    NewKeyBytes: bytes
    CheckSum: bytes
    NewKey: KeyBlob
    def __init__(self, NewKeyBytes: _Optional[bytes] = ..., CheckSum: _Optional[bytes] = ..., NewKey: _Optional[_Union[KeyBlob, _Mapping]] = ...) -> None: ...

class GetMechanismListRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class GetMechanismListResponse(_message.Message):
    __slots__ = ("Mechs",)
    MECHS_FIELD_NUMBER: _ClassVar[int]
    Mechs: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, Mechs: _Optional[_Iterable[int]] = ...) -> None: ...

class GetMechanismInfoRequest(_message.Message):
    __slots__ = ("Mech",)
    MECH_FIELD_NUMBER: _ClassVar[int]
    Mech: int
    def __init__(self, Mech: _Optional[int] = ...) -> None: ...

class GetMechanismInfoResponse(_message.Message):
    __slots__ = ("MechInfo",)
    MECHINFO_FIELD_NUMBER: _ClassVar[int]
    MechInfo: MechanismInfo
    def __init__(self, MechInfo: _Optional[_Union[MechanismInfo, _Mapping]] = ...) -> None: ...

class GetAttributeValueRequest(_message.Message):
    __slots__ = ("Object", "AttributesBytes", "Attributes")
    class AttributesBytesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: int
        value: bytes
        def __init__(self, key: _Optional[int] = ..., value: _Optional[bytes] = ...) -> None: ...
    class AttributesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: int
        value: AttributeValue
        def __init__(self, key: _Optional[int] = ..., value: _Optional[_Union[AttributeValue, _Mapping]] = ...) -> None: ...
    OBJECT_FIELD_NUMBER: _ClassVar[int]
    ATTRIBUTESBYTES_FIELD_NUMBER: _ClassVar[int]
    ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    Object: bytes
    AttributesBytes: _containers.ScalarMap[int, bytes]
    Attributes: _containers.MessageMap[int, AttributeValue]
    def __init__(self, Object: _Optional[bytes] = ..., AttributesBytes: _Optional[_Mapping[int, bytes]] = ..., Attributes: _Optional[_Mapping[int, AttributeValue]] = ...) -> None: ...

class GetAttributeValueResponse(_message.Message):
    __slots__ = ("AttributesBytes", "Attributes")
    class AttributesBytesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: int
        value: bytes
        def __init__(self, key: _Optional[int] = ..., value: _Optional[bytes] = ...) -> None: ...
    class AttributesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: int
        value: AttributeValue
        def __init__(self, key: _Optional[int] = ..., value: _Optional[_Union[AttributeValue, _Mapping]] = ...) -> None: ...
    ATTRIBUTESBYTES_FIELD_NUMBER: _ClassVar[int]
    ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    AttributesBytes: _containers.ScalarMap[int, bytes]
    Attributes: _containers.MessageMap[int, AttributeValue]
    def __init__(self, AttributesBytes: _Optional[_Mapping[int, bytes]] = ..., Attributes: _Optional[_Mapping[int, AttributeValue]] = ...) -> None: ...

class SetAttributeValueRequest(_message.Message):
    __slots__ = ("Object", "Attributes")
    class AttributesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: int
        value: AttributeValue
        def __init__(self, key: _Optional[int] = ..., value: _Optional[_Union[AttributeValue, _Mapping]] = ...) -> None: ...
    OBJECT_FIELD_NUMBER: _ClassVar[int]
    ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    Object: bytes
    Attributes: _containers.MessageMap[int, AttributeValue]
    def __init__(self, Object: _Optional[bytes] = ..., Attributes: _Optional[_Mapping[int, AttributeValue]] = ...) -> None: ...

class SetAttributeValueResponse(_message.Message):
    __slots__ = ("Object",)
    OBJECT_FIELD_NUMBER: _ClassVar[int]
    Object: bytes
    def __init__(self, Object: _Optional[bytes] = ...) -> None: ...

class LoginRequest(_message.Message):
    __slots__ = ("Storeid", "Pin")
    STOREID_FIELD_NUMBER: _ClassVar[int]
    PIN_FIELD_NUMBER: _ClassVar[int]
    Storeid: bytes
    Pin: bytes
    def __init__(self, Storeid: _Optional[bytes] = ..., Pin: _Optional[bytes] = ...) -> None: ...

class LoginResponse(_message.Message):
    __slots__ = ("Pinblob",)
    PINBLOB_FIELD_NUMBER: _ClassVar[int]
    Pinblob: bytes
    def __init__(self, Pinblob: _Optional[bytes] = ...) -> None: ...

class LogoutRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class LogoutResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Mechanism(_message.Message):
    __slots__ = ("Mechanism", "ParameterB", "RSAOAEPParameter", "RSAPSSParameter", "ECDH1DeriveParameter", "BTCDeriveParameter", "ECSGParameter", "KyberKEMParameter", "ECAGGParameter")
    MECHANISM_FIELD_NUMBER: _ClassVar[int]
    PARAMETERB_FIELD_NUMBER: _ClassVar[int]
    RSAOAEPPARAMETER_FIELD_NUMBER: _ClassVar[int]
    RSAPSSPARAMETER_FIELD_NUMBER: _ClassVar[int]
    ECDH1DERIVEPARAMETER_FIELD_NUMBER: _ClassVar[int]
    BTCDERIVEPARAMETER_FIELD_NUMBER: _ClassVar[int]
    ECSGPARAMETER_FIELD_NUMBER: _ClassVar[int]
    KYBERKEMPARAMETER_FIELD_NUMBER: _ClassVar[int]
    ECAGGPARAMETER_FIELD_NUMBER: _ClassVar[int]
    Mechanism: int
    ParameterB: bytes
    RSAOAEPParameter: RSAOAEPParm
    RSAPSSParameter: RSAPSSParm
    ECDH1DeriveParameter: ECDH1DeriveParm
    BTCDeriveParameter: BTCDeriveParm
    ECSGParameter: ECSGParm
    KyberKEMParameter: KyberKEMParm
    ECAGGParameter: ECAGGParm
    def __init__(self, Mechanism: _Optional[int] = ..., ParameterB: _Optional[bytes] = ..., RSAOAEPParameter: _Optional[_Union[RSAOAEPParm, _Mapping]] = ..., RSAPSSParameter: _Optional[_Union[RSAPSSParm, _Mapping]] = ..., ECDH1DeriveParameter: _Optional[_Union[ECDH1DeriveParm, _Mapping]] = ..., BTCDeriveParameter: _Optional[_Union[BTCDeriveParm, _Mapping]] = ..., ECSGParameter: _Optional[_Union[ECSGParm, _Mapping]] = ..., KyberKEMParameter: _Optional[_Union[KyberKEMParm, _Mapping]] = ..., ECAGGParameter: _Optional[_Union[ECAGGParm, _Mapping]] = ...) -> None: ...

class MechanismInfo(_message.Message):
    __slots__ = ("MinKeySize", "MaxKeySize", "Flags")
    MINKEYSIZE_FIELD_NUMBER: _ClassVar[int]
    MAXKEYSIZE_FIELD_NUMBER: _ClassVar[int]
    FLAGS_FIELD_NUMBER: _ClassVar[int]
    MinKeySize: int
    MaxKeySize: int
    Flags: int
    def __init__(self, MinKeySize: _Optional[int] = ..., MaxKeySize: _Optional[int] = ..., Flags: _Optional[int] = ...) -> None: ...

class RSAOAEPParm(_message.Message):
    __slots__ = ("HashMech", "Mgf", "EncodingParmType", "EncodingParm")
    class Mask(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        CkgMgf1None: _ClassVar[RSAOAEPParm.Mask]
        CkgMgf1Sha1: _ClassVar[RSAOAEPParm.Mask]
        CkgMgf1Sha256: _ClassVar[RSAOAEPParm.Mask]
        CkgMgf1Sha384: _ClassVar[RSAOAEPParm.Mask]
        CkgMgf1Sha512: _ClassVar[RSAOAEPParm.Mask]
        CkgMgf1Sha224: _ClassVar[RSAOAEPParm.Mask]
        CkgIbmMgf1Sha3_224: _ClassVar[RSAOAEPParm.Mask]
        CkgIbmMgf1Sha3_256: _ClassVar[RSAOAEPParm.Mask]
        CkgIbmMgf1Sha3_384: _ClassVar[RSAOAEPParm.Mask]
        CkgIbmMgf1Sha3_512: _ClassVar[RSAOAEPParm.Mask]
    CkgMgf1None: RSAOAEPParm.Mask
    CkgMgf1Sha1: RSAOAEPParm.Mask
    CkgMgf1Sha256: RSAOAEPParm.Mask
    CkgMgf1Sha384: RSAOAEPParm.Mask
    CkgMgf1Sha512: RSAOAEPParm.Mask
    CkgMgf1Sha224: RSAOAEPParm.Mask
    CkgIbmMgf1Sha3_224: RSAOAEPParm.Mask
    CkgIbmMgf1Sha3_256: RSAOAEPParm.Mask
    CkgIbmMgf1Sha3_384: RSAOAEPParm.Mask
    CkgIbmMgf1Sha3_512: RSAOAEPParm.Mask
    class ParmType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        CkzNoDataSpecified: _ClassVar[RSAOAEPParm.ParmType]
        CkzDataSpecifiied: _ClassVar[RSAOAEPParm.ParmType]
    CkzNoDataSpecified: RSAOAEPParm.ParmType
    CkzDataSpecifiied: RSAOAEPParm.ParmType
    HASHMECH_FIELD_NUMBER: _ClassVar[int]
    MGF_FIELD_NUMBER: _ClassVar[int]
    ENCODINGPARMTYPE_FIELD_NUMBER: _ClassVar[int]
    ENCODINGPARM_FIELD_NUMBER: _ClassVar[int]
    HashMech: int
    Mgf: RSAOAEPParm.Mask
    EncodingParmType: RSAOAEPParm.ParmType
    EncodingParm: bytes
    def __init__(self, HashMech: _Optional[int] = ..., Mgf: _Optional[_Union[RSAOAEPParm.Mask, str]] = ..., EncodingParmType: _Optional[_Union[RSAOAEPParm.ParmType, str]] = ..., EncodingParm: _Optional[bytes] = ...) -> None: ...

class RSAPSSParm(_message.Message):
    __slots__ = ("HashMech", "Mgf", "SaltByteCount")
    class Mask(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        CkgMgf1None: _ClassVar[RSAPSSParm.Mask]
        CkgMgf1Sha1: _ClassVar[RSAPSSParm.Mask]
        CkgMgf1Sha256: _ClassVar[RSAPSSParm.Mask]
        CkgMgf1Sha384: _ClassVar[RSAPSSParm.Mask]
        CkgMgf1Sha512: _ClassVar[RSAPSSParm.Mask]
        CkgMgf1Sha224: _ClassVar[RSAPSSParm.Mask]
        CkgIbmMgf1Sha3_224: _ClassVar[RSAPSSParm.Mask]
        CkgIbmMgf1Sha3_256: _ClassVar[RSAPSSParm.Mask]
        CkgIbmMgf1Sha3_384: _ClassVar[RSAPSSParm.Mask]
        CkgIbmMgf1Sha3_512: _ClassVar[RSAPSSParm.Mask]
    CkgMgf1None: RSAPSSParm.Mask
    CkgMgf1Sha1: RSAPSSParm.Mask
    CkgMgf1Sha256: RSAPSSParm.Mask
    CkgMgf1Sha384: RSAPSSParm.Mask
    CkgMgf1Sha512: RSAPSSParm.Mask
    CkgMgf1Sha224: RSAPSSParm.Mask
    CkgIbmMgf1Sha3_224: RSAPSSParm.Mask
    CkgIbmMgf1Sha3_256: RSAPSSParm.Mask
    CkgIbmMgf1Sha3_384: RSAPSSParm.Mask
    CkgIbmMgf1Sha3_512: RSAPSSParm.Mask
    HASHMECH_FIELD_NUMBER: _ClassVar[int]
    MGF_FIELD_NUMBER: _ClassVar[int]
    SALTBYTECOUNT_FIELD_NUMBER: _ClassVar[int]
    HashMech: int
    Mgf: RSAPSSParm.Mask
    SaltByteCount: int
    def __init__(self, HashMech: _Optional[int] = ..., Mgf: _Optional[_Union[RSAPSSParm.Mask, str]] = ..., SaltByteCount: _Optional[int] = ...) -> None: ...

class ECDH1DeriveParm(_message.Message):
    __slots__ = ("Kdf", "SharedData", "PublicData")
    class KeyDerivationFunction(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        CkdNotUsed0: _ClassVar[ECDH1DeriveParm.KeyDerivationFunction]
        CkdNull: _ClassVar[ECDH1DeriveParm.KeyDerivationFunction]
        CkdSha1Kdf: _ClassVar[ECDH1DeriveParm.KeyDerivationFunction]
        CkdNotUsed3: _ClassVar[ECDH1DeriveParm.KeyDerivationFunction]
        CkdNotUsed4: _ClassVar[ECDH1DeriveParm.KeyDerivationFunction]
        CkdSha224Kdf: _ClassVar[ECDH1DeriveParm.KeyDerivationFunction]
        CkdSha256Kdf: _ClassVar[ECDH1DeriveParm.KeyDerivationFunction]
        CkdSha384Kdf: _ClassVar[ECDH1DeriveParm.KeyDerivationFunction]
        CkdSha512Kdf: _ClassVar[ECDH1DeriveParm.KeyDerivationFunction]
        CkdIbmHybridNull: _ClassVar[ECDH1DeriveParm.KeyDerivationFunction]
    CkdNotUsed0: ECDH1DeriveParm.KeyDerivationFunction
    CkdNull: ECDH1DeriveParm.KeyDerivationFunction
    CkdSha1Kdf: ECDH1DeriveParm.KeyDerivationFunction
    CkdNotUsed3: ECDH1DeriveParm.KeyDerivationFunction
    CkdNotUsed4: ECDH1DeriveParm.KeyDerivationFunction
    CkdSha224Kdf: ECDH1DeriveParm.KeyDerivationFunction
    CkdSha256Kdf: ECDH1DeriveParm.KeyDerivationFunction
    CkdSha384Kdf: ECDH1DeriveParm.KeyDerivationFunction
    CkdSha512Kdf: ECDH1DeriveParm.KeyDerivationFunction
    CkdIbmHybridNull: ECDH1DeriveParm.KeyDerivationFunction
    KDF_FIELD_NUMBER: _ClassVar[int]
    SHAREDDATA_FIELD_NUMBER: _ClassVar[int]
    PUBLICDATA_FIELD_NUMBER: _ClassVar[int]
    Kdf: ECDH1DeriveParm.KeyDerivationFunction
    SharedData: bytes
    PublicData: bytes
    def __init__(self, Kdf: _Optional[_Union[ECDH1DeriveParm.KeyDerivationFunction, str]] = ..., SharedData: _Optional[bytes] = ..., PublicData: _Optional[bytes] = ...) -> None: ...

class BTCDeriveParm(_message.Message):
    __slots__ = ("Type", "ChildKeyIndex", "ChainCode", "Version")
    class BTCDeriveType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        CkBIP0032NotUsed: _ClassVar[BTCDeriveParm.BTCDeriveType]
        CkBIP0032PRV2PRV: _ClassVar[BTCDeriveParm.BTCDeriveType]
        CkBIP0032PRV2PUB: _ClassVar[BTCDeriveParm.BTCDeriveType]
        CkBIP0032PUB2PUB: _ClassVar[BTCDeriveParm.BTCDeriveType]
        CkBIP0032MASTERK: _ClassVar[BTCDeriveParm.BTCDeriveType]
        CkSLIP0010PRV2PRV: _ClassVar[BTCDeriveParm.BTCDeriveType]
        CkSLIP0010PRV2PUB: _ClassVar[BTCDeriveParm.BTCDeriveType]
        CkSLIP0010PUB2PUB: _ClassVar[BTCDeriveParm.BTCDeriveType]
        CkSLIP0010MASTERK: _ClassVar[BTCDeriveParm.BTCDeriveType]
    CkBIP0032NotUsed: BTCDeriveParm.BTCDeriveType
    CkBIP0032PRV2PRV: BTCDeriveParm.BTCDeriveType
    CkBIP0032PRV2PUB: BTCDeriveParm.BTCDeriveType
    CkBIP0032PUB2PUB: BTCDeriveParm.BTCDeriveType
    CkBIP0032MASTERK: BTCDeriveParm.BTCDeriveType
    CkSLIP0010PRV2PRV: BTCDeriveParm.BTCDeriveType
    CkSLIP0010PRV2PUB: BTCDeriveParm.BTCDeriveType
    CkSLIP0010PUB2PUB: BTCDeriveParm.BTCDeriveType
    CkSLIP0010MASTERK: BTCDeriveParm.BTCDeriveType
    TYPE_FIELD_NUMBER: _ClassVar[int]
    CHILDKEYINDEX_FIELD_NUMBER: _ClassVar[int]
    CHAINCODE_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    Type: BTCDeriveParm.BTCDeriveType
    ChildKeyIndex: int
    ChainCode: bytes
    Version: int
    def __init__(self, Type: _Optional[_Union[BTCDeriveParm.BTCDeriveType, str]] = ..., ChildKeyIndex: _Optional[int] = ..., ChainCode: _Optional[bytes] = ..., Version: _Optional[int] = ...) -> None: ...

class ECSGParm(_message.Message):
    __slots__ = ("Type",)
    class ECSGType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        CkEcsgIbmNotUsed: _ClassVar[ECSGParm.ECSGType]
        CkEcsgIbmEcsdsaS256: _ClassVar[ECSGParm.ECSGType]
        CkEcsgIbmEcsdsaComprMulti: _ClassVar[ECSGParm.ECSGType]
        CkEcsgIbmBls: _ClassVar[ECSGParm.ECSGType]
    CkEcsgIbmNotUsed: ECSGParm.ECSGType
    CkEcsgIbmEcsdsaS256: ECSGParm.ECSGType
    CkEcsgIbmEcsdsaComprMulti: ECSGParm.ECSGType
    CkEcsgIbmBls: ECSGParm.ECSGType
    TYPE_FIELD_NUMBER: _ClassVar[int]
    Type: ECSGParm.ECSGType
    def __init__(self, Type: _Optional[_Union[ECSGParm.ECSGType, str]] = ...) -> None: ...

class ECAGGParm(_message.Message):
    __slots__ = ("Version", "Mode", "PerElementSize", "Elements")
    class ECAGGMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        CkIbmEcAggInvalid: _ClassVar[ECAGGParm.ECAGGMode]
        CkIbmEcAggBLS12_381Sign: _ClassVar[ECAGGParm.ECAGGMode]
        CkIbmEcAggBLS12_381Pkey: _ClassVar[ECAGGParm.ECAGGMode]
    CkIbmEcAggInvalid: ECAGGParm.ECAGGMode
    CkIbmEcAggBLS12_381Sign: ECAGGParm.ECAGGMode
    CkIbmEcAggBLS12_381Pkey: ECAGGParm.ECAGGMode
    VERSION_FIELD_NUMBER: _ClassVar[int]
    MODE_FIELD_NUMBER: _ClassVar[int]
    PERELEMENTSIZE_FIELD_NUMBER: _ClassVar[int]
    ELEMENTS_FIELD_NUMBER: _ClassVar[int]
    Version: int
    Mode: ECAGGParm.ECAGGMode
    PerElementSize: int
    Elements: bytes
    def __init__(self, Version: _Optional[int] = ..., Mode: _Optional[_Union[ECAGGParm.ECAGGMode, str]] = ..., PerElementSize: _Optional[int] = ..., Elements: _Optional[bytes] = ...) -> None: ...

class KyberKEMParm(_message.Message):
    __slots__ = ("Version", "Mode", "Kdf", "Prepend", "CipherText", "SharedData", "Blob")
    class KyberMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        CkNotUsed: _ClassVar[KyberKEMParm.KyberMode]
        CkIbmKEMEncapsulate: _ClassVar[KyberKEMParm.KyberMode]
        CkIbmKEMDecapsulate: _ClassVar[KyberKEMParm.KyberMode]
    CkNotUsed: KyberKEMParm.KyberMode
    CkIbmKEMEncapsulate: KyberKEMParm.KyberMode
    CkIbmKEMDecapsulate: KyberKEMParm.KyberMode
    class KyberDeriveType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        CkdNotUsed: _ClassVar[KyberKEMParm.KyberDeriveType]
        CkdNull: _ClassVar[KyberKEMParm.KyberDeriveType]
        CkdIbmHybridNull: _ClassVar[KyberKEMParm.KyberDeriveType]
        CkdIbmHybridSha1Kdf: _ClassVar[KyberKEMParm.KyberDeriveType]
        CkdIbmHybridSha224Kdf: _ClassVar[KyberKEMParm.KyberDeriveType]
        CkdIbmHybridSha256Kdf: _ClassVar[KyberKEMParm.KyberDeriveType]
        CkdIbmHybridSha384Kdf: _ClassVar[KyberKEMParm.KyberDeriveType]
        CkdIbmHybridSha512Kdf: _ClassVar[KyberKEMParm.KyberDeriveType]
    CkdNotUsed: KyberKEMParm.KyberDeriveType
    CkdNull: KyberKEMParm.KyberDeriveType
    CkdIbmHybridNull: KyberKEMParm.KyberDeriveType
    CkdIbmHybridSha1Kdf: KyberKEMParm.KyberDeriveType
    CkdIbmHybridSha224Kdf: KyberKEMParm.KyberDeriveType
    CkdIbmHybridSha256Kdf: KyberKEMParm.KyberDeriveType
    CkdIbmHybridSha384Kdf: KyberKEMParm.KyberDeriveType
    CkdIbmHybridSha512Kdf: KyberKEMParm.KyberDeriveType
    VERSION_FIELD_NUMBER: _ClassVar[int]
    MODE_FIELD_NUMBER: _ClassVar[int]
    KDF_FIELD_NUMBER: _ClassVar[int]
    PREPEND_FIELD_NUMBER: _ClassVar[int]
    CIPHERTEXT_FIELD_NUMBER: _ClassVar[int]
    SHAREDDATA_FIELD_NUMBER: _ClassVar[int]
    BLOB_FIELD_NUMBER: _ClassVar[int]
    Version: int
    Mode: KyberKEMParm.KyberMode
    Kdf: KyberKEMParm.KyberDeriveType
    Prepend: bool
    CipherText: bytes
    SharedData: bytes
    Blob: bytes
    def __init__(self, Version: _Optional[int] = ..., Mode: _Optional[_Union[KyberKEMParm.KyberMode, str]] = ..., Kdf: _Optional[_Union[KyberKEMParm.KyberDeriveType, str]] = ..., Prepend: bool = ..., CipherText: _Optional[bytes] = ..., SharedData: _Optional[bytes] = ..., Blob: _Optional[bytes] = ...) -> None: ...

class HMACGeneralParm(_message.Message):
    __slots__ = ("ReturnByteCount",)
    RETURNBYTECOUNT_FIELD_NUMBER: _ClassVar[int]
    ReturnByteCount: int
    def __init__(self, ReturnByteCount: _Optional[int] = ...) -> None: ...

class RewrapKeyBlobRequest(_message.Message):
    __slots__ = ("WrappedKeyBytes", "WrappedKey")
    WRAPPEDKEYBYTES_FIELD_NUMBER: _ClassVar[int]
    WRAPPEDKEY_FIELD_NUMBER: _ClassVar[int]
    WrappedKeyBytes: bytes
    WrappedKey: KeyBlob
    def __init__(self, WrappedKeyBytes: _Optional[bytes] = ..., WrappedKey: _Optional[_Union[KeyBlob, _Mapping]] = ...) -> None: ...

class RewrapKeyBlobResponse(_message.Message):
    __slots__ = ("RewrappedKeyBytes", "RewrappedKey")
    REWRAPPEDKEYBYTES_FIELD_NUMBER: _ClassVar[int]
    REWRAPPEDKEY_FIELD_NUMBER: _ClassVar[int]
    RewrappedKeyBytes: bytes
    RewrappedKey: KeyBlob
    def __init__(self, RewrappedKeyBytes: _Optional[bytes] = ..., RewrappedKey: _Optional[_Union[KeyBlob, _Mapping]] = ...) -> None: ...

class AttributeValue(_message.Message):
    __slots__ = ("AttributeB", "AttributeTF", "AttributeI")
    ATTRIBUTEB_FIELD_NUMBER: _ClassVar[int]
    ATTRIBUTETF_FIELD_NUMBER: _ClassVar[int]
    ATTRIBUTEI_FIELD_NUMBER: _ClassVar[int]
    AttributeB: bytes
    AttributeTF: bool
    AttributeI: int
    def __init__(self, AttributeB: _Optional[bytes] = ..., AttributeTF: bool = ..., AttributeI: _Optional[int] = ...) -> None: ...

class KeyBlob(_message.Message):
    __slots__ = ("KeyBlobID", "Version", "TxID", "Attributes", "KeyBlobs")
    class AttributesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: int
        value: AttributeValue
        def __init__(self, key: _Optional[int] = ..., value: _Optional[_Union[AttributeValue, _Mapping]] = ...) -> None: ...
    KEYBLOBID_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    TXID_FIELD_NUMBER: _ClassVar[int]
    ATTRIBUTES_FIELD_NUMBER: _ClassVar[int]
    KEYBLOBS_FIELD_NUMBER: _ClassVar[int]
    KeyBlobID: bytes
    Version: int
    TxID: bytes
    Attributes: _containers.MessageMap[int, AttributeValue]
    KeyBlobs: _containers.RepeatedScalarFieldContainer[bytes]
    def __init__(self, KeyBlobID: _Optional[bytes] = ..., Version: _Optional[int] = ..., TxID: _Optional[bytes] = ..., Attributes: _Optional[_Mapping[int, AttributeValue]] = ..., KeyBlobs: _Optional[_Iterable[bytes]] = ...) -> None: ...
