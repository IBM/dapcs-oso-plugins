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
"""EKMF key import support for the Fireblocks plugin.

Imports externally-created signing keys into the EP11 HSM through the EKMF
addon sidecar and signs with the imported key blobs over plain (localhost)
GREP11 gRPC.
"""

from .addon_client import EkmfAddonClient, EkmfAddonError, parse_ekmf_document_type
from .grep11_client import CKM, Grep11Client
from .keystore import SigningKeyStore
from .state import EkmfImportState, EkmfStateError

__all__ = [
    "CKM",
    "EkmfAddonClient",
    "EkmfAddonError",
    "EkmfImportState",
    "EkmfStateError",
    "Grep11Client",
    "SigningKeyStore",
    "parse_ekmf_document_type",
]
