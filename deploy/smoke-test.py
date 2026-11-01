#!/usr/bin/env python3
"""Exercise the deployed login captcha through the public HTTP entry point."""

import base64
import binascii
import json
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.request
import zlib


def post(base_url, path, body):
    request = urllib.request.Request(
        base_url + path,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "tenant-id": "1"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.load(response)


def check_png(encoded, name):
    try:
        data = base64.b64decode(encoded, validate=True)
        if not data.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError("missing PNG signature")
        position = 8
        image_data = bytearray()
        has_header = False
        has_end = False
        while position + 12 <= len(data):
            length = struct.unpack_from(">I", data, position)[0]
            chunk_type = data[position + 4 : position + 8]
            end = position + 12 + length
            if end > len(data):
                raise ValueError("truncated chunk")
            chunk = data[position + 8 : position + 8 + length]
            expected_crc = struct.unpack_from(">I", data, position + 8 + length)[0]
            if zlib.crc32(chunk_type + chunk) != expected_crc:
                raise ValueError("invalid chunk checksum")
            if chunk_type == b"IHDR":
                width, height = struct.unpack_from(">II", chunk)
                has_header = width > 0 and height > 0
            elif chunk_type == b"IDAT":
                image_data.extend(chunk)
            elif chunk_type == b"IEND":
                has_end = True
                break
            position = end
        if not has_header or not has_end or not image_data or not zlib.decompress(image_data):
            raise ValueError("incomplete image")
    except (TypeError, ValueError, binascii.Error, struct.error, zlib.error) as error:
        raise AssertionError(f"Invalid {name} PNG: {error}") from error


def encrypt(value, key):
    if len(key.encode("utf-8")) != 16:
        raise AssertionError("Unexpected captcha AES key length")
    result = subprocess.run(
        ["openssl", "enc", "-aes-128-ecb", "-e", "-K", key.encode("utf-8").hex(), "-nosalt", "-a", "-A"],
        input=value.encode("utf-8"),
        capture_output=True,
        check=True,
    )
    return result.stdout.decode("ascii")


def backend_restarting():
    """Fail promptly on repeated crashes while allowing time for first startup."""
    try:
        result = subprocess.run(
            ["docker", "compose", "-f", "deploy/compose.yml", "ps", "--all", "--quiet", "backend"],
            capture_output=True, text=True, check=True,
        )
        container = result.stdout.strip()
        if not container:
            return False
        result = subprocess.run(
            ["docker", "inspect", "--format", "{{.RestartCount}}", container],
            capture_output=True, text=True, check=True,
        )
        return int(result.stdout.strip()) >= 2
    except (OSError, subprocess.CalledProcessError, ValueError):
        return False


def main():
    base_url = sys.argv[1].rstrip("/")
    deadline = time.monotonic() + 360
    check_backend_at = time.monotonic() + 30
    last_error = "no response"
    while time.monotonic() < deadline:
        try:
            captcha = post(base_url, "/admin-api/system/captcha/get", {"captchaType": "blockPuzzle"})
            if captcha.get("repCode") == "0000":
                break
            last_error = f"captcha returned {captcha.get('repCode')}: {captcha.get('repMsg')}"
        except (OSError, ValueError, urllib.error.URLError) as error:
            last_error = str(error)
        if time.monotonic() >= check_backend_at:
            if backend_restarting():
                raise AssertionError("Backend restarted repeatedly; inspect container logs")
            check_backend_at = time.monotonic() + 15
        time.sleep(3)
    else:
        raise AssertionError(f"Captcha did not become ready: {last_error}")

    data = captcha.get("repData") or {}
    if not data.get("token"):
        raise AssertionError("Captcha response has no token")
    check_png(data.get("originalImageBase64"), "background")
    check_png(data.get("jigsawImageBase64"), "puzzle")

    login = post(base_url, "/admin-api/system/auth/login", {"username": "admin", "password": "111111"})
    if login.get("code") == 0 or "验证码" not in str(login.get("msg", "")):
        raise AssertionError(f"Login without a captcha was not rejected for captcha validation: {login}")

    invalid = post(base_url, "/admin-api/system/captcha/check", {
        "captchaType": "blockPuzzle", "token": "invalid", "pointJson": "invalid"
    })
    if invalid.get("repCode") == "0000":
        raise AssertionError("Captcha check accepted an invalid token")

    # Read the generated challenge from this isolated CI Redis instance to test
    # the successful path without automating a human captcha or logging secrets.
    cached = subprocess.run(
        ["docker", "compose", "-f", "deploy/compose.yml", "exec", "-T", "redis",
         "redis-cli", "-n", "1", "GET", "RUNNING:CAPTCHA:" + data["token"]],
        capture_output=True, text=True, check=True,
    )
    point = json.loads(cached.stdout)
    point_json = json.dumps({"x": point["x"], "y": point["y"]}, separators=(",", ":"))
    checked = post(base_url, "/admin-api/system/captcha/check", {
        "captchaType": "blockPuzzle", "token": data["token"],
        "pointJson": encrypt(point_json, data["secretKey"]),
    })
    if checked.get("repCode") != "0000":
        raise AssertionError(f"Correct captcha was rejected: {checked.get('repMsg')}")

    login = post(base_url, "/admin-api/system/auth/login", {
        "username": "admin", "password": "111111",
        "captchaVerification": encrypt(data["token"] + "---" + point_json, data["secretKey"]),
    })
    if login.get("code") != 0 or not (login.get("data") or {}).get("accessToken"):
        raise AssertionError(f"Login after captcha verification failed: {login.get('msg')}")
    print("Captcha PNGs, Redis storage, invalid/correct answers, and protected login passed.")


if __name__ == "__main__":
    main()
