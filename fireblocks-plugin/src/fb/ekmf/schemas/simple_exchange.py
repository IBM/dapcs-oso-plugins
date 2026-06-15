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

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class KeyCheckMethod(str, Enum):
    CMAC_ZERO = "5: CMAC-ZERO"
    ENC_ZERO = "8: ENC-ZERO"
    SHA_256 = "S: SHA-256"
    SHA2VP1 = "U: SHA2VP1"
    HMACS256 = "H: HMACS256"
    SKI = "K: SKI"


class KeyFormat(str, Enum):
    CCA_DES_KEK = "CCA_DES_KEK"
    CCA_AES_KEK = "CCA_AES_KEK"
    CKM_AES_CBC = "CKM_AES_CBC"
    CKM_DES_CBC = "CKM_DES_CBC"
    CKM_AES_ECB = "CKM_AES_ECB"
    CKM_DES_ECB = "CKM_DES_ECB"
    CKM_AES_CBC_PAD = "CKM_AES_CBC_PAD"
    CKM_RSA_PKCS_OAEP = "CKM_RSA_PKCS_OAEP"
    TR31_AES_KEK = "TR31_AES_KEK"
    TR31_DES_KEK = "TR31_DES_KEK"


class KeyTokenHashAlgorithm(str, Enum):
    SHA_1 = "SHA-1"
    SHA_256 = "SHA-256"
    SHA_256_UNDERSCORE = "SHA_256"
    SHA_512 = "SHA-512"


class KeyCheck(BaseModel):
    key_check_value: str
    key_check_method: Optional[KeyCheckMethod] = None


class KekData(BaseModel):
    kek_key_check: Optional[KeyCheck] = None
    kek_label: Optional[str] = None


class KeyData(BaseModel):
    format: KeyFormat
    key_value: str
    key_check: KeyCheck
    key_label: str
    curve: Optional[str] = None
    key_token_hash_algorithm: Optional[KeyTokenHashAlgorithm] = None


class MetaData(BaseModel):
    activation_date: Optional[str] = None
    expiration_date: Optional[str] = None
    original_key_template: Optional[str] = None
    suggested_key_template: Optional[str] = None
    source_institution: Optional[str] = None


class Key(BaseModel):
    key_type: str
    kek_data: Optional[KekData] = None
    key_data: KeyData
    meta_data: Optional[MetaData] = None


class SimpleExchangeModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    raw_xml: bytes = Field(exclude=True)
    uuid: Optional[str] = None
    keys: list[Key] = Field(default_factory=list)
