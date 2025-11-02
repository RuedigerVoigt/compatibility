#!/usr/bin/env python
"""Compile .po files to .mo files for translations.

This script converts human-readable .po translation files to binary .mo files
that are used by Python's gettext module at runtime.

Usage:
    python compile_translations.py

The script will compile:
    locales/de/LC_MESSAGES/compatibility.po -> locales/de/LC_MESSAGES/compatibility.mo

Copyright (c) 2021-2025 Rüdiger Voigt and contributors
Released under the Apache License 2.0
"""

import os
import struct


def compile_po_to_mo(po_file, mo_file):
    """Compile .po to .mo using Python stdlib only (no external dependencies).

    Args:
        po_file: Path to source .po file
        mo_file: Path to output .mo file
    """
    # Read and parse .po file
    with open(po_file, 'r', encoding='utf-8') as f:
        content = f.read()

    messages = {}
    lines = content.split('\n')

    current_msgid = []
    current_msgstr = []
    in_msgid = False
    in_msgstr = False

    for line in lines:
        line = line.strip()

        if line.startswith('msgid '):
            # Save previous entry if exists
            if current_msgid and current_msgstr:
                msgid_text = ''.join(current_msgid)
                msgstr_text = ''.join(current_msgstr)
                if msgid_text:  # Skip empty (header) entry for now
                    messages[msgid_text] = msgstr_text

            # Start new msgid
            current_msgid = [line[7:-1]]  # Remove 'msgid "' and trailing '"'
            current_msgstr = []
            in_msgid = True
            in_msgstr = False

        elif line.startswith('msgstr '):
            current_msgstr = [line[8:-1]]  # Remove 'msgstr "' and trailing '"'
            in_msgid = False
            in_msgstr = True

        elif line.startswith('"') and line.endswith('"'):
            # Continuation line
            text = line[1:-1]  # Remove quotes
            if in_msgid:
                current_msgid.append(text)
            elif in_msgstr:
                current_msgstr.append(text)

    # Don't forget the last entry
    if current_msgid and current_msgstr:
        msgid_text = ''.join(current_msgid)
        msgstr_text = ''.join(current_msgstr)
        if msgid_text:
            messages[msgid_text] = msgstr_text

    # Build .mo file with proper UTF-8 metadata header
    # This header is critical for Python's gettext to use UTF-8 encoding
    metadata = (
        "Project-Id-Version: compatibility 2.0.0\n"
        "Content-Type: text/plain; charset=UTF-8\n"
        "Content-Transfer-Encoding: 8bit\n"
    )

    # Create catalog with header
    catalog = {'': metadata}
    catalog.update(messages)

    # Sort keys
    keys = sorted(catalog.keys())

    # Prepare data
    offsets = []
    ids = b''
    strs = b''

    for key in keys:
        # Encode as UTF-8
        key_bytes = key.encode('utf-8')
        val_bytes = catalog[key].encode('utf-8')

        offsets.append((len(ids), len(key_bytes), len(strs), len(val_bytes)))
        ids += key_bytes + b'\x00'
        strs += val_bytes + b'\x00'

    # Calculate offsets
    keystart = 7 * 4 + 16 * len(keys)
    valuestart = keystart + len(ids)

    # Prepare index arrays
    koffsets = []
    voffsets = []

    for o1, l1, o2, l2 in offsets:
        koffsets.append((l1, keystart + o1))
        voffsets.append((l2, valuestart + o2))

    # Write .mo file in GNU gettext format
    with open(mo_file, 'wb') as f:
        # Magic number (little-endian)
        f.write(struct.pack('<I', 0x950412de))
        # Version
        f.write(struct.pack('<I', 0))
        # Number of entries
        f.write(struct.pack('<I', len(keys)))
        # Offset of table with original strings
        f.write(struct.pack('<I', 7 * 4))
        # Offset of table with translation strings
        f.write(struct.pack('<I', 7 * 4 + len(keys) * 8))
        # Size of hashing table (we don't use it)
        f.write(struct.pack('<I', 0))
        # Offset of hashing table
        f.write(struct.pack('<I', 0))

        # Write original strings index
        for length, offset in koffsets:
            f.write(struct.pack('<II', length, offset))

        # Write translation strings index
        for length, offset in voffsets:
            f.write(struct.pack('<II', length, offset))

        # Write original strings
        f.write(ids)

        # Write translation strings
        f.write(strs)


if __name__ == '__main__':
    po_file = 'compatibility/locales/de/LC_MESSAGES/compatibility.po'
    mo_file = 'compatibility/locales/de/LC_MESSAGES/compatibility.mo'

    print(f"Compiling {po_file} to {mo_file}...")
    compile_po_to_mo(po_file, mo_file)
    print(f"Done! Created {mo_file}")
    print(f"File size: {os.path.getsize(mo_file)} bytes")
