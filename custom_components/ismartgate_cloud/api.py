"""Cloud API client for iSmartGate."""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import random
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode
import xml.etree.ElementTree as ET

from aiohttp import ClientError, ClientSession
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

_LOGGER = logging.getLogger(__name__)


class ISmartGateApiError(Exception):
    """Generic API error."""


class ISmartGateAuthError(ISmartGateApiError):
    """Authentication error."""


class ISmartGateConnectionError(ISmartGateApiError):
    """Connection error."""


class ISmartGateInvalidApiCodeError(ISmartGateApiError):
    """Invalid API code (stale/expired)."""


@dataclass
class ISmartGateDoor:
    """Parsed door data."""

    door_id: int
    enabled: bool
    name: str | None
    gate: bool
    status: str
    apicode: str | None
    temperature: float | None
    voltage: int | None


@dataclass
class ISmartGateInfo:
    """Parsed device info."""

    name: str
    model: str
    firmware_version: str
    remote_access_enabled: bool
    remote_access: str | None
    doors: list[ISmartGateDoor]


class ISmartGateCloudApi:
    """Client for iSmartGate cloud endpoint."""

    def __init__(
        self,
        session: ClientSession,
        udi: str,
        username: str,
        password: str,
        timeout: int = 20,
    ) -> None:
        """Initialize cloud client."""
        self._session = session
        self._udi = udi.strip()
        self._username = username.strip()
        self._password = password
        self._timeout = timeout

        user_l = self._username.lower()
        raw_token = f"{user_l}@ismartgate"
        self._token = hashlib.sha1(raw_token.encode("utf-8")).hexdigest()

        sha1_hex = hashlib.sha1((user_l + self._password).encode("utf-8")).hexdigest()
        self._key = (
            f"{sha1_hex[32:36]}a"
            f"{sha1_hex[7:10]}!"
            f"{sha1_hex[18:21]}*#"
            f"{sha1_hex[24:26]}"
        ).encode("utf-8")

    @property
    def base_url(self) -> str:
        """Return cloud API URL."""
        return f"https://{self._udi}.isgaccess.com/api.php"

    async def async_get_info(self) -> ISmartGateInfo:
        """Fetch device info."""
        root = await self._async_request("info", "", "")
        return self._parse_info(root)

    async def async_activate(self, door_id: int, api_code: str) -> None:
        """Activate a door with the current API code."""
        root = await self._async_request("activate", str(door_id), api_code)
        result = self._find_text(root, "result")
        if str(result).upper() != "OK":
            raise ISmartGateApiError(f"Activation failed for door {door_id}")

    async def _async_request(self, option: str, arg1: str, arg2: str) -> ET.Element:
        """Send encrypted command to cloud API and return parsed XML root."""
        command = json.dumps(
            [self._username, self._password, option, arg1, arg2],
            separators=(",", ":"),
        )
        encrypted_command = self._encrypt(command)
        params = {
            "data": encrypted_command,
            "t": str(random.randint(1, 100000000)),
            "token": self._token,
        }
        url = f"{self.base_url}?{urlencode(params)}"

        try:
            async with self._session.get(url, timeout=self._timeout) as resp:
                text = await resp.text()
        except (TimeoutError, ClientError) as err:
            raise ISmartGateConnectionError("Unable to reach iSmartGate cloud API") from err

        if "invalid login or password" in text.lower():
            raise ISmartGateAuthError("Invalid username/password")

        try:
            xml_text = self._decrypt(text)
        except Exception:
            # API sometimes returns plain xml/errors when decrypt fails.
            xml_text = text

        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as err:
            raise ISmartGateApiError("Invalid XML returned from API") from err

        err_node = root.find("error")
        if err_node is not None:
            err_code = self._find_text(err_node, "errorcode")
            err_msg = self._find_text(err_node, "errormsg") or "Unknown error"
            msg_lower = str(err_msg).lower()
            if "invalid login" in msg_lower or "wrong login" in msg_lower:
                raise ISmartGateAuthError(str(err_msg))
            if "invalid api code" in msg_lower:
                raise ISmartGateInvalidApiCodeError(str(err_msg))
            raise ISmartGateApiError(f"API error {err_code}: {err_msg}")

        return root

    def _encrypt(self, plaintext: str) -> str:
        """Encrypt payload in AES-128-CBC + PKCS#7 and prefix IV text."""
        iv_text = os.urandom(8).hex()[:16]
        iv = iv_text.encode("utf-8")
        padded = self._pad(plaintext.encode("utf-8"))
        cipher = Cipher(
            algorithms.AES(self._key),
            modes.CBC(iv),
            backend=default_backend(),
        )
        encryptor = cipher.encryptor()
        encrypted = encryptor.update(padded) + encryptor.finalize()
        return iv_text + base64.b64encode(encrypted).decode("utf-8")

    def _decrypt(self, payload: str) -> str:
        """Decrypt iSmartGate payload where first 16 chars are IV."""
        iv_text = payload[:16]
        encrypted_b64 = payload[16:]
        iv = iv_text.encode("utf-8")
        encrypted = base64.b64decode(encrypted_b64)
        cipher = Cipher(
            algorithms.AES(self._key),
            modes.CBC(iv),
            backend=default_backend(),
        )
        decryptor = cipher.decryptor()
        decrypted = decryptor.update(encrypted) + decryptor.finalize()
        return self._unpad(decrypted).decode("utf-8")

    @staticmethod
    def _pad(data: bytes) -> bytes:
        pad_len = 16 - (len(data) % 16)
        return data + bytes([pad_len] * pad_len)

    @staticmethod
    def _unpad(data: bytes) -> bytes:
        pad_len = data[-1]
        if pad_len < 1 or pad_len > 16:
            raise ValueError("Invalid padding")
        return data[:-pad_len]

    def _parse_info(self, root: ET.Element) -> ISmartGateInfo:
        response = root.find("response") or root

        name = (
            self._find_text(response, "ismartgatename")
            or self._find_text(response, "gogogatename")
            or "iSmartGate"
        )
        model = self._find_text(response, "model") or "unknown"
        firmware = self._find_text(response, "firmwareversion") or "unknown"
        remote_enabled = self._to_bool(self._find_text(response, "remoteaccessenabled"))
        remote_access = self._find_text(response, "remoteaccess")

        doors: list[ISmartGateDoor] = []
        for door_id in (1, 2, 3):
            door_node = response.find(f"door{door_id}")
            if door_node is None:
                continue

            temp_raw = self._find_first_text(
                door_node,
                ["temperature", "temp", "tempc", "temperaturec", "tmp"],
            ) or self._find_first_text(
                response,
                [
                    f"door{door_id}temperature",
                    f"door{door_id}_temperature",
                    f"temperature{door_id}",
                    f"temp{door_id}",
                    f"door{door_id}temp",
                ],
            )

            voltage_raw = self._find_first_text(
                door_node,
                ["voltage", "battery", "batterypercent", "battery_level"],
            ) or self._find_first_text(
                response,
                [
                    f"door{door_id}voltage",
                    f"voltage{door_id}",
                    f"door{door_id}battery",
                    f"battery{door_id}",
                ],
            )

            doors.append(
                ISmartGateDoor(
                    door_id=door_id,
                    enabled=self._to_bool(self._find_text(door_node, "enabled")),
                    name=self._find_text(door_node, "name"),
                    gate=self._to_bool(self._find_text(door_node, "gate")),
                    status=(self._find_text(door_node, "status") or "undefined").lower(),
                    apicode=self._find_text(door_node, "apicode"),
                    temperature=self._to_float(temp_raw),
                    voltage=self._to_int(voltage_raw),
                )
            )

        return ISmartGateInfo(
            name=name,
            model=model,
            firmware_version=firmware,
            remote_access_enabled=remote_enabled,
            remote_access=remote_access,
            doors=doors,
        )

    @staticmethod
    def _find_text(node: ET.Element, tag: str) -> str | None:
        child = node.find(tag)
        if child is None or child.text is None:
            return None
        text = child.text.strip()
        return text if text != "" else None

    def _find_first_text(self, node: ET.Element, tags: list[str]) -> str | None:
        """Return the first non-empty value from a list of XML tags."""
        for tag in tags:
            value = self._find_text(node, tag)
            if value is not None:
                return value
        return None

    @staticmethod
    def _to_bool(value: str | None) -> bool:
        if value is None:
            return False
        return value.strip().lower() in {"yes", "1", "true", "on", "opened"}

    @staticmethod
    def _to_int(value: str | None) -> int | None:
        if value in (None, ""):
            return None
        try:
            return int(float(value))
        except ValueError:
            return None

    @staticmethod
    def _to_float(value: str | None) -> float | None:
        if value in (None, ""):
            return None
        try:
            return float(value.replace(",", "."))
        except ValueError:
            return None
