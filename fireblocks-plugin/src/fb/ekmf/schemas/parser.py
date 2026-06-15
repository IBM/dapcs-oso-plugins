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

import xml.etree.ElementTree as ET
from pathlib import Path

from .simple_exchange import (
    KekData,
    Key,
    KeyCheck,
    KeyData,
    MetaData,
    SimpleExchangeModel,
)

KEY_ELEMENT_TAGS = {"AesKey", "DesKey", "HmacKey", "EccKey"}


def _text(element: ET.Element, tag: str) -> str | None:
    child = element.find(f".//{tag}")
    if child is not None and child.text:
        return child.text.strip()
    return None


def _parse_key_check(element: ET.Element | None) -> KeyCheck | None:
    if element is None:
        return None
    value = _text(element, "KeyCheckValue")
    if value is None:
        return None
    return KeyCheck(
        key_check_value=value,
        key_check_method=_text(element, "KeyCheckMethod"),
    )


def _parse_kek_data(key_el: ET.Element) -> KekData | None:
    kek_el = key_el.find("KekData")
    if kek_el is None:
        return None
    return KekData(
        kek_key_check=_parse_key_check(kek_el.find("KekKeyCheck")),
        kek_label=_text(kek_el, "KekLabel"),
    )


def _parse_key_data(key_el: ET.Element) -> KeyData:
    data_el = key_el.find("KeyData")
    if data_el is None:
        raise ValueError("KeyData element missing")
    return KeyData(
        format=_text(data_el, "Format"),
        key_value=_text(data_el, "KeyValue"),
        key_check=_parse_key_check(data_el.find("KeyCheck")),
        key_label=_text(data_el, "KeyLabel"),
        curve=_text(data_el, "Curve"),
        key_token_hash_algorithm=_text(data_el, "KeyTokenHashAlgorithm"),
    )


def _parse_meta_data(key_el: ET.Element) -> MetaData | None:
    meta_el = key_el.find("MetaData")
    if meta_el is None:
        return None
    return MetaData(
        activation_date=_text(meta_el, "ActivationDate"),
        expiration_date=_text(meta_el, "ExpirationDate"),
        original_key_template=_text(meta_el, "OriginalKeyTemplate"),
        suggested_key_template=_text(meta_el, "SuggestedKeyTemplate"),
        source_institution=_text(meta_el, "SourceInstitution"),
    )


def _parse_key(element: ET.Element, key_type: str) -> Key:
    return Key(
        key_type=key_type,
        kek_data=_parse_kek_data(element),
        key_data=_parse_key_data(element),
        meta_data=_parse_meta_data(element),
    )


def parse_xml(source: str | Path | bytes) -> SimpleExchangeModel:
    if isinstance(source, bytes):
        raw = source
        root = ET.fromstring(source)
    elif isinstance(source, Path):
        raw = Path(source).read_bytes()
        root = ET.fromstring(raw)
    elif Path(source).exists():
        raw = Path(source).read_bytes()
        root = ET.fromstring(raw)
    else:
        raw = source.encode()
        root = ET.fromstring(source)

    uuid = root.get("uuid")

    keys: list[Key] = []
    key_list = root.find("KeyList")
    if key_list is not None:
        for child in key_list:
            tag = child.tag
            if tag in KEY_ELEMENT_TAGS:
                keys.append(_parse_key(child, tag))

    return SimpleExchangeModel(uuid=uuid, keys=keys, raw_xml=raw)
