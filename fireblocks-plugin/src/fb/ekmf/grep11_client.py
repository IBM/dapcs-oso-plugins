#
# (c) Copyright IBM Corp. 2026
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from dataclasses import dataclass
from enum import IntEnum

import grpc

from .generated import server_pb2, server_pb2_grpc


class CKM(IntEnum):
    RSA_PKCS_KEY_PAIR_GEN = 0x0000
    RSA_PKCS_OAEP = 0x0009
    SHA256 = 0x0250
    ECDSA = 0x1041
    EC_KEY_PAIR_GEN = 0x1040
    AES_KEY_GEN = 0x1080
    AES_CBC_PAD = 0x1085
    # EP11 does not implement the standard CKM_EDDSA / CKM_AES_CMAC
    # mechanisms; m_SignSingle rejects them with CKR_MECHANISM_INVALID.
    # The IBM vendor mechanisms (CKM_VENDOR_DEFINED = 0x80000000) produce
    # standard RFC 8032 Ed25519 and NIST SP 800-38B CMAC signatures.
    IBM_CMAC = 0x80010007
    IBM_ED25519_SHA512 = 0x8001001C


class CKA(IntEnum):
    TOKEN = 0x0001
    KEY_TYPE = 0x0100
    ENCRYPT = 0x0104
    DECRYPT = 0x0105
    WRAP = 0x0106
    UNWRAP = 0x0107
    SIGN = 0x0108
    VERIFY = 0x010A
    DERIVE = 0x010C
    MODULUS_BITS = 0x0121
    PUBLIC_EXPONENT = 0x0122
    VALUE_LEN = 0x0161
    EXTRACTABLE = 0x0162
    EC_PARAMS = 0x0180
    IBM_USE_AS_DATA = 0x8000000D


CKK_AES = 0x1F
CKK_EC = 0x03

OID_ED25519 = bytes.fromhex("06032b6570")
OID_SECP256K1 = bytes.fromhex("06052b8104000a")


@dataclass
class GenerateKeyPairResult:
    priv_key_blob: bytes
    pub_key_bytes: bytes


@dataclass
class UnwrapKeyResult:
    key_blob: bytes
    check_sum: bytes


def _rsa_oaep_sha256_mech() -> server_pb2.Mechanism:
    return server_pb2.Mechanism(
        Mechanism=CKM.RSA_PKCS_OAEP,
        RSAOAEPParameter=server_pb2.RSAOAEPParm(
            HashMech=CKM.SHA256,
            Mgf=server_pb2.RSAOAEPParm.CkgMgf1Sha256,
            EncodingParmType=server_pb2.RSAOAEPParm.CkzNoDataSpecified,
        ),
    )


def _aes_cbc_pad_mech(iv: bytes) -> server_pb2.Mechanism:
    return server_pb2.Mechanism(Mechanism=CKM.AES_CBC_PAD, ParameterB=iv)


def _aes_kek_template() -> dict[int, server_pb2.AttributeValue]:
    return {
        CKA.KEY_TYPE: server_pb2.AttributeValue(AttributeI=CKK_AES),
        CKA.VALUE_LEN: server_pb2.AttributeValue(AttributeI=32),
        CKA.ENCRYPT: server_pb2.AttributeValue(AttributeTF=True),
        CKA.DECRYPT: server_pb2.AttributeValue(AttributeTF=True),
        CKA.WRAP: server_pb2.AttributeValue(AttributeTF=True),
        CKA.UNWRAP: server_pb2.AttributeValue(AttributeTF=True),
        CKA.TOKEN: server_pb2.AttributeValue(AttributeTF=True),
        CKA.EXTRACTABLE: server_pb2.AttributeValue(AttributeTF=False),
    }


def _aes_data_key_template() -> dict[int, server_pb2.AttributeValue]:
    return {
        CKA.KEY_TYPE: server_pb2.AttributeValue(AttributeI=CKK_AES),
        CKA.VALUE_LEN: server_pb2.AttributeValue(AttributeI=32),
        CKA.ENCRYPT: server_pb2.AttributeValue(AttributeTF=True),
        CKA.DECRYPT: server_pb2.AttributeValue(AttributeTF=True),
        CKA.SIGN: server_pb2.AttributeValue(AttributeTF=True),
        CKA.VERIFY: server_pb2.AttributeValue(AttributeTF=True),
        CKA.DERIVE: server_pb2.AttributeValue(AttributeTF=True),
        CKA.WRAP: server_pb2.AttributeValue(AttributeTF=False),
        CKA.UNWRAP: server_pb2.AttributeValue(AttributeTF=False),
        CKA.EXTRACTABLE: server_pb2.AttributeValue(AttributeTF=False),
        CKA.TOKEN: server_pb2.AttributeValue(AttributeTF=True),
        CKA.IBM_USE_AS_DATA: server_pb2.AttributeValue(AttributeTF=True),
    }


def _ec_priv_template(oid: bytes) -> dict[int, server_pb2.AttributeValue]:
    return {
        CKA.KEY_TYPE: server_pb2.AttributeValue(AttributeI=CKK_EC),
        CKA.EC_PARAMS: server_pb2.AttributeValue(AttributeB=oid),
        CKA.SIGN: server_pb2.AttributeValue(AttributeTF=True),
        CKA.EXTRACTABLE: server_pb2.AttributeValue(AttributeTF=False),
        CKA.TOKEN: server_pb2.AttributeValue(AttributeTF=True),
    }


def _ed25519_priv_template() -> dict[int, server_pb2.AttributeValue]:
    return _ec_priv_template(OID_ED25519)


def _secp256k1_priv_template() -> dict[int, server_pb2.AttributeValue]:
    return _ec_priv_template(OID_SECP256K1)


class Grep11Client:
    def __init__(self, endpoint: str) -> None:
        channel = grpc.insecure_channel(target=endpoint)
        self.stub = server_pb2_grpc.CryptoStub(channel)

    def generate_rsa_key_pair(self) -> GenerateKeyPairResult:
        pub_key_template: dict[int, server_pb2.AttributeValue] = {
            CKA.MODULUS_BITS: server_pb2.AttributeValue(AttributeI=4096),
            CKA.PUBLIC_EXPONENT: server_pb2.AttributeValue(
                AttributeB=bytes([0x01, 0x00, 0x01])
            ),
            CKA.ENCRYPT: server_pb2.AttributeValue(AttributeTF=True),
            CKA.WRAP: server_pb2.AttributeValue(AttributeTF=True),
            CKA.TOKEN: server_pb2.AttributeValue(AttributeTF=True),
        }

        priv_key_template: dict[int, server_pb2.AttributeValue] = {
            CKA.SIGN: server_pb2.AttributeValue(AttributeTF=True),
            CKA.DECRYPT: server_pb2.AttributeValue(AttributeTF=True),
            CKA.UNWRAP: server_pb2.AttributeValue(AttributeTF=True),
            CKA.EXTRACTABLE: server_pb2.AttributeValue(AttributeTF=False),
            CKA.TOKEN: server_pb2.AttributeValue(AttributeTF=True),
        }

        request = server_pb2.GenerateKeyPairRequest(
            Mech=server_pb2.Mechanism(Mechanism=CKM.RSA_PKCS_KEY_PAIR_GEN),
            PubKeyTemplate=pub_key_template,
            PrivKeyTemplate=priv_key_template,
        )

        response: server_pb2.GenerateKeyPairResponse = self.stub.GenerateKeyPair(
            request
        )

        return GenerateKeyPairResult(
            priv_key_blob=response.PrivKeyBytes,
            pub_key_bytes=response.PubKeyBytes,
        )

    def _unwrap(
        self,
        *,
        mechanism: server_pb2.Mechanism,
        kek_blob: bytes,
        wrapped: bytes,
        template: dict[int, server_pb2.AttributeValue],
    ) -> UnwrapKeyResult:
        request = server_pb2.UnwrapKeyRequest(
            Wrapped=wrapped,
            Mech=mechanism,
            Template=template,
            KeK=server_pb2.KeyBlob(KeyBlobs=[kek_blob]),
        )
        response: server_pb2.UnwrapKeyResponse = self.stub.UnwrapKey(request)
        return UnwrapKeyResult(
            key_blob=response.UnwrappedBytes,
            check_sum=response.CheckSum,
        )

    def unwrap_aes_kek_with_rsa(
        self, wrapped: bytes, rsa_priv_blob: bytes
    ) -> UnwrapKeyResult:
        return self._unwrap(
            mechanism=_rsa_oaep_sha256_mech(),
            kek_blob=rsa_priv_blob,
            wrapped=wrapped,
            template=_aes_kek_template(),
        )

    def unwrap_ed25519_with_aes(
        self, wrapped: bytes, iv: bytes, aes_kek_blob: bytes
    ) -> UnwrapKeyResult:
        return self._unwrap(
            mechanism=_aes_cbc_pad_mech(iv),
            kek_blob=aes_kek_blob,
            wrapped=wrapped,
            template=_ed25519_priv_template(),
        )

    def unwrap_secp256k1_with_aes(
        self, wrapped: bytes, iv: bytes, aes_kek_blob: bytes
    ) -> UnwrapKeyResult:
        return self._unwrap(
            mechanism=_aes_cbc_pad_mech(iv),
            kek_blob=aes_kek_blob,
            wrapped=wrapped,
            template=_secp256k1_priv_template(),
        )

    def unwrap_aes_with_aes(
        self, wrapped: bytes, iv: bytes, aes_kek_blob: bytes
    ) -> UnwrapKeyResult:
        return self._unwrap(
            mechanism=_aes_cbc_pad_mech(iv),
            kek_blob=aes_kek_blob,
            wrapped=wrapped,
            template=_aes_data_key_template(),
        )

    def get_mechanism_list(self) -> list[int]:
        request = server_pb2.GetMechanismListRequest()
        response: server_pb2.GetMechanismListResponse = self.stub.GetMechanismList(
            request
        )
        return list(response.Mechs)

    def sign_single(self, data: bytes, key_blob: bytes, mechanism: int) -> bytes:
        request = server_pb2.SignSingleRequest(
            Mech=server_pb2.Mechanism(Mechanism=mechanism),
            Data=data,
            PrivKey=server_pb2.KeyBlob(KeyBlobs=[key_blob]),
        )
        response: server_pb2.SignSingleResponse = self.stub.SignSingle(request)
        return response.Signature
