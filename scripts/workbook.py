"""Read a maintainer's mit-sheet workbook straight from Google Sheets.

The published spreadsheet is the source of truth for a sheet's mits, so the
importers fetch it by id rather than reading a local copy someone downloaded --
there is no local file to go stale. Google exports the whole spreadsheet as
xlsx at a plain URL, which needs the doc shared as "anyone with the link".

Tabs are resolved by name. Workbook XML numbers its worksheet parts in an order
that has nothing to do with the tab order a person sees, so an index like
`sheet9.xml` is a guess that silently reads the wrong tab when the author adds
or reorders one.
"""

import io
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

EXPORT = 'https://docs.google.com/spreadsheets/d/{}/export?format=xlsx'
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}


def fetch(sheet_id):
    """Download a spreadsheet and open it as a zip archive, in memory."""
    try:
        with urllib.request.urlopen(EXPORT.format(sheet_id)) as response:
            data = response.read()
    except urllib.error.HTTPError as error:
        raise SystemExit(
            f'Google Sheets returned HTTP {error.code} for {sheet_id}.\n'
            'The spreadsheet must be shared as "anyone with the link".')
    if not data.startswith(b'PK'):
        raise SystemExit(f'{sheet_id} did not return an xlsx - check the sharing setting.')
    return zipfile.ZipFile(io.BytesIO(data))


def tabs(archive):
    """Visible tab name -> worksheet part name, in the order a person sees them."""
    workbook = ET.fromstring(archive.read('xl/workbook.xml'))
    rels = {rel.get('Id'): rel.get('Target')
            for rel in ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))}
    found = {}
    for sheet in workbook.findall('.//s:sheets/s:sheet', NS):
        target = rels[sheet.get('{%s}id' % NS['r'])].lstrip('/')
        found[sheet.get('name')] = target if target.startswith('xl/') else f'xl/{target}'
    return found


def worksheet(archive, name):
    """The worksheet part for a tab, by its visible name."""
    found = tabs(archive)
    if name not in found:
        raise SystemExit(f'No tab named {name!r}. Tabs are:\n  ' + '\n  '.join(found))
    return found[name]


def shared_strings(archive):
    return [''.join(node.itertext()) for node in ET.fromstring(archive.read('xl/sharedStrings.xml'))]
