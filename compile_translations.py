#!/usr/bin/env python
"""Compile .po files to .mo files for translations.

This script converts human-readable .po translation files to binary .mo files
that are used by Python's gettext module at runtime.

Usage:
    python compile_translations.py

The script will compile:
    locales/de/LC_MESSAGES/compatibility.po -> locales/de/LC_MESSAGES/compatibility.mo

Copyright (c) 2021-2026 Rüdiger Voigt and contributors
Released under the Apache License 2.0
"""

import glob
import os
import struct


_PO_ESCAPES = {'n': '\n', 't': '\t', 'r': '\r', '"': '"', '\\': '\\'}


def _unescape_po(text):
    """Decode the backslash escape sequences used inside .po quoted strings.

    Handles the standard set (\\n, \\t, \\r, \\", \\\\). An unknown escape is
    left untouched (backslash preserved). This is needed so the header entry,
    which encodes its fields with \\n, becomes real newlines that gettext can
    parse.

    Args:
        text: A raw string taken from between the quotes of a .po line.

    Returns:
        The unescaped string.
    """
    result = []
    i = 0
    while i < len(text):
        if text[i] == '\\' and i + 1 < len(text):
            nxt = text[i + 1]
            result.append(_PO_ESCAPES.get(nxt, '\\' + nxt))
            i += 2
        else:
            result.append(text[i])
            i += 1
    return ''.join(result)


def _parse_po(po_file):
    """Parse a .po file into a {msgid: msgstr} mapping.

    The empty-msgid header entry is preserved so its metadata (Content-Type,
    Language, Plural-Forms, ...) is carried into the compiled catalog.

    Args:
        po_file: Path to the source .po file.

    Returns:
        Dict mapping each msgid to its msgstr (including the '' header entry).
    """
    with open(po_file, encoding='utf-8') as f:
        lines = f.read().split('\n')

    messages = {}
    current_msgid = []
    current_msgstr = []
    state = None  # tracks whether we're reading a msgid or a msgstr

    def flush():
        # Save the entry just parsed (including the '' header entry).
        if current_msgid and current_msgstr:
            messages[''.join(current_msgid)] = ''.join(current_msgstr)

    for line in lines:
        line = line.strip()
        if line.startswith('msgid '):
            flush()
            current_msgid[:] = [_unescape_po(line[7:-1])]   # strip 'msgid "' / '"'
            current_msgstr[:] = []
            state = 'msgid'
        elif line.startswith('msgstr '):
            current_msgstr[:] = [_unescape_po(line[8:-1])]  # strip 'msgstr "' / '"'
            state = 'msgstr'
        elif line.startswith('"') and line.endswith('"'):
            text = _unescape_po(line[1:-1])                 # continuation line
            if state == 'msgid':
                current_msgid.append(text)
            elif state == 'msgstr':
                current_msgstr.append(text)
    flush()
    return messages


def _serialize_mo(catalog):
    """Serialize a message catalog into GNU gettext .mo binary format.

    Args:
        catalog: Dict mapping msgid to msgstr (including the '' metadata header).

    Returns:
        The .mo file contents as bytes.
    """
    keys = sorted(catalog.keys())

    offsets = []
    ids = b''
    strs = b''
    for key in keys:
        key_bytes = key.encode('utf-8')
        val_bytes = catalog[key].encode('utf-8')
        offsets.append((len(ids), len(key_bytes), len(strs), len(val_bytes)))
        ids += key_bytes + b'\x00'
        strs += val_bytes + b'\x00'

    keystart = 7 * 4 + 16 * len(keys)
    valuestart = keystart + len(ids)
    koffsets = [(l1, keystart + o1) for o1, l1, _, _ in offsets]
    voffsets = [(l2, valuestart + o2) for _, _, o2, l2 in offsets]

    output = bytearray()
    output += struct.pack('<I', 0x950412de)             # magic number (LE)
    output += struct.pack('<I', 0)                       # version
    output += struct.pack('<I', len(keys))              # number of entries
    output += struct.pack('<I', 7 * 4)                  # offset of originals table
    output += struct.pack('<I', 7 * 4 + len(keys) * 8)  # offset of translations table
    output += struct.pack('<I', 0)                       # hash table size (unused)
    output += struct.pack('<I', 0)                       # hash table offset (unused)
    for length, offset in koffsets:
        output += struct.pack('<II', length, offset)
    for length, offset in voffsets:
        output += struct.pack('<II', length, offset)
    output += ids
    output += strs
    return bytes(output)


def compile_po_to_mo(po_file, mo_file):
    """Compile .po to .mo using Python stdlib only (no external dependencies).

    Args:
        po_file: Path to source .po file
        mo_file: Path to output .mo file
    """
    # The parsed catalog already includes the '' header entry from the .po
    # (Content-Type, Language, Plural-Forms, ...), so no metadata is injected
    # here -- the .po file is the single source of truth.
    catalog = _parse_po(po_file)
    with open(mo_file, 'wb') as f:
        f.write(_serialize_mo(catalog))


if __name__ == '__main__':
    # Compile every .po catalog under the locales tree (one per language).
    po_files = sorted(
        glob.glob('compatibility/locales/**/*.po', recursive=True))
    if not po_files:
        print('No .po files found under compatibility/locales/.')
    for po_file in po_files:
        mo_file = os.path.splitext(po_file)[0] + '.mo'
        print(f"Compiling {po_file} to {mo_file}...")
        compile_po_to_mo(po_file, mo_file)
        print(f"Done! Created {mo_file} ({os.path.getsize(mo_file)} bytes)")
