"""Offline source/asset validation. Run from any directory with Python 3.10+.

Checks manifests, DOI duplication, file SHA256, PDF magic, BibTeX keys and local
Markdown links. With PyMuPDF installed it additionally checks PDF page counts.
It validates integrity, not the scientific validity of a claim or fulltext access.
"""
from pathlib import Path
from urllib.parse import unquote
import hashlib
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SUPPLEMENT = ROOT / 'Reference/05_英文补充与来源核验'


def main():
    errors = []
    old = json.loads((ROOT / 'Reference/资料索引.json').read_text(encoding='utf-8'))
    new = json.loads((SUPPLEMENT / 'sources.json').read_text(encoding='utf-8'))
    try:
        import fitz
    except ImportError:
        fitz = None
    doi_owners, hash_owners = {}, {}
    pdf_count = 0
    for group, records in [('original', old), ('supplement', new)]:
        for entry in records:
            ident = group + ':' + entry['id']
            # Original ERA5-Land web entry has no publication-year field.
            for key in ('title', 'url') + (('year',) if group == 'supplement' else ()):
                if not entry.get(key):
                    errors.append(f'{ident}: missing {key}')
            doi = (entry.get('doi') or '').lower().strip()
            # Legacy index uses this field for arXiv/report identifiers too.
            if group == 'original' and not doi.startswith('10.'):
                doi = ''
            if doi:
                if not re.fullmatch(r'10\.\d{4,9}/\S+', doi):
                    errors.append(f'{ident}: malformed DOI')
                if doi in doi_owners:
                    errors.append(f'{ident}: duplicate DOI with {doi_owners[doi]}')
                doi_owners[doi] = ident
            rel = entry.get('local_file') if group == 'supplement' else entry.get('file')
            if not rel:
                if group == 'supplement' and not entry.get('fulltext_status', '').endswith('local_fulltext') and entry.get('fulltext_status') != 'online_pdf_reviewed_no_local_copy':
                    errors.append(f'{ident}: missing explicit access limitation')
                continue
            path = ROOT / rel if group == 'supplement' else ROOT / 'Reference' / rel
            if not path.is_file():
                errors.append(f'{ident}: missing {path}')
                continue
            content = path.read_bytes()
            digest = hashlib.sha256(content).hexdigest()
            if digest != entry.get('sha256'):
                errors.append(f'{ident}: SHA256 mismatch')
            if digest in hash_owners:
                errors.append(f'{ident}: byte-identical duplicate with {hash_owners[digest]}')
            hash_owners[digest] = ident
            if path.suffix.lower() == '.pdf':
                pdf_count += 1
                if not content.startswith(b'%PDF-'):
                    errors.append(f'{ident}: PDF signature missing')
                elif fitz:
                    try:
                        with fitz.open(path) as document:
                            if len(document) != entry.get('pages'):
                                errors.append(f'{ident}: PDF page count mismatch')
                    except Exception as exc:
                        errors.append(f'{ident}: unreadable PDF: {exc}')

    bibliography = (SUPPLEMENT / 'references.bib').read_text(encoding='utf-8')
    bib_keys = re.findall(r'@\w+\{([^,]+),', bibliography)
    expected = {entry['id'] for entry in new}
    if len(bib_keys) != len(set(bib_keys)) or set(bib_keys) != expected:
        errors.append('BibTeX keys do not match supplemental source IDs')

    link_count = 0
    for doc in ROOT.rglob('*.md'):
        if '.git' in doc.parts:
            continue
        text = re.sub(r'```.*?```', '', doc.read_text(encoding='utf-8'), flags=re.S)
        for target in re.findall(r'\]\(([^)]+)\)', text):
            target = target.strip('<>')
            if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', target) or target.startswith('#'):
                continue
            path = unquote(target.split('#')[0])
            if not path:
                continue
            link_count += 1
            if not (doc.parent / path).exists():
                errors.append(f'{doc.relative_to(ROOT)}: broken local link {target}')

    if errors:
        for error in errors:
            print('ERROR:', error)
        return 1
    print(f'PASS: {len(old)} original indexed records; {len(new)} supplemental records; '
          f'{pdf_count} PDFs; {link_count} local links; {len(bib_keys)} BibTeX keys.')
    print('SHA256 and DOI duplication checks passed. '
          + ('PDF page counts checked with PyMuPDF.' if fitz else 'Install PyMuPDF to also check page counts.'))
    print('The 16 CAJ titles are outside the original 16-record manifest; their content is not validated here.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
