#!/usr/bin/env python3
"""Decode a Google Authenticator export QR screenshot into otpauth:// URIs."""
import argparse
import base64
import sys
from urllib.parse import urlparse, parse_qs, quote

import cv2

ALGORITHMS = {0: "SHA1", 1: "SHA1", 2: "SHA256", 3: "SHA512", 4: "MD5"}
DIGITS = {0: 6, 1: 6, 2: 8}
TYPES = {0: "totp", 1: "hotp", 2: "totp"}  # 0 = unspecified, default totp


def read_varint(buf, pos):
    result = shift = 0
    while True:
        b = buf[pos]
        pos += 1
        result |= (b & 0x7F) << shift
        if not b & 0x80:
            return result, pos
        shift += 7


def parse_message(buf):
    """Generic protobuf parser -> list of (field_number, wire_type, value)."""
    pos, fields = 0, []
    while pos < len(buf):
        key, pos = read_varint(buf, pos)
        field, wire = key >> 3, key & 7
        if wire == 0:
            val, pos = read_varint(buf, pos)
        elif wire == 2:
            length, pos = read_varint(buf, pos)
            val = buf[pos:pos + length]
            pos += length
        elif wire == 1:
            val, pos = buf[pos:pos + 8], pos + 8
        elif wire == 5:
            val, pos = buf[pos:pos + 4], pos + 4
        else:
            raise ValueError(f"Unsupported wire type {wire}")
        fields.append((field, wire, val))
    return fields


def parse_otp_parameters(buf):
    p = {"secret": b"", "name": "", "issuer": "", "algorithm": 1,
         "digits": 1, "type": 2, "counter": 0}
    for field, _, val in parse_message(buf):
        if field == 1: p["secret"] = val
        elif field == 2: p["name"] = val.decode("utf-8")
        elif field == 3: p["issuer"] = val.decode("utf-8")
        elif field == 4: p["algorithm"] = val
        elif field == 5: p["digits"] = val
        elif field == 6: p["type"] = val
        elif field == 7: p["counter"] = val
    return p


def to_otpauth_uri(p):
    secret = base64.b32encode(p["secret"]).decode().rstrip("=")
    otp_type = TYPES.get(p["type"], "totp")
    label = quote(f"{p['issuer']}:{p['name']}" if p["issuer"] else p["name"])
    uri = f"otpauth://{otp_type}/{label}?secret={secret}"
    if p["issuer"]:
        uri += f"&issuer={quote(p['issuer'])}"
    uri += f"&algorithm={ALGORITHMS.get(p['algorithm'], 'SHA1')}"
    uri += f"&digits={DIGITS.get(p['digits'], 6)}"
    if otp_type == "hotp":
        uri += f"&counter={p['counter']}"
    return uri


def read_qr(path):
    img = cv2.imread(path)
    if img is None:
        sys.exit(f"Could not read image: {path}")
    detector = cv2.QRCodeDetector()
    data, _, _ = detector.detectAndDecode(img)
    if not data:
        # Retry upscaled + grayscale; screenshots can be small/blurry
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        data, _, _ = detector.detectAndDecode(gray)
    if not data:
        sys.exit("No QR code found in the image.")
    return data


def decode_migration(uri):
    parsed = urlparse(uri)
    if parsed.scheme != "otpauth-migration":
        sys.exit(f"Not a Google Authenticator export QR (got scheme '{parsed.scheme}').")
    b64 = parse_qs(parsed.query)["data"][0]
    payload = base64.b64decode(b64 + "=" * (-len(b64) % 4))
    # MigrationPayload: field 1 = repeated OtpParameters
    return [parse_otp_parameters(val)
            for field, wire, val in parse_message(payload)
            if field == 1 and wire == 2]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("image", nargs="+", help="Screenshot(s) of the export QR code")
    ap.add_argument("--json", action="store_true", help="Output JSON instead of URIs")
    args = ap.parse_args()

    entries = []
    for path in args.image:
        entries.extend(decode_migration(read_qr(path)))

    if args.json:
        import json
        print(json.dumps([{
            "issuer": e["issuer"], "name": e["name"],
            "secret": base64.b32encode(e["secret"]).decode().rstrip("="),
            "type": TYPES.get(e["type"], "totp"),
            "algorithm": ALGORITHMS.get(e["algorithm"], "SHA1"),
            "digits": DIGITS.get(e["digits"], 6),
        } for e in entries], indent=2))
    else:
        for e in entries:
            print(to_otpauth_uri(e))


if __name__ == "__main__":
    main()