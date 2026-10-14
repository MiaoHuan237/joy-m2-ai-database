"""Internal Oxford evidence adapter; never a public-exam source."""
import hashlib
import json
import shutil
import tempfile
from io import BytesIO
from pathlib import Path
from pypdf import PdfReader

from .automation import canonical, read_json, sha
from .v123_preflight import _formal_indexes

PROFILE = {'schema_version':'oxford-mock-transcription-v1',
           'source_type':'publisher_mock','source_id':'OXFORD-M2-2025-26-C-SET1',
           'publisher':'Oxford','session':'2025/26','paper':'C Set 1',
           'module':'M2','language':'zh-Hant'}
CHECKS = {'question','subparts','formula','marks','figures','solution'}
FIELDS = {'staging_id','question_number','question_pages','solution_pages','marks',
          'difficulty_proposal','question_text_original','publisher_ms_original',
          'ms_evidence_level','primary_type','tags','review','review_notes',
          'requires_figure','issues'}


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _text(value):
    return type(value) is str and bool(value.strip())


def _load(inputs):
    _require(set(inputs)=={'proposal','staging','pp','ms'},'exact source inputs required')
    for path in inputs.values():
        _require(Path(path).is_file() and not any(p.is_symlink() for p in (Path(path),*Path(path).parents)),
                 'regular source files required')
    data=read_json(inputs['proposal'])
    _require(type(data) is dict and set(data)==set(PROFILE)|{'batch_id','staging_sha256','sources','records','transcription_digest'},
             'proposal fields invalid')
    digest=data['transcription_digest']
    semantic={k:v for k,v in data.items() if k!='transcription_digest'}
    _require(hashlib.sha256(canonical(semantic).encode()).hexdigest()==digest,'proposal digest mismatch')
    _require(all(data[k]==v for k,v in PROFILE.items()),'publisher mock profile mismatch')
    draft=read_json(inputs['staging'])
    _require(sha(inputs['staging'])==data['staging_sha256'],'staging identity mismatch')
    _require(_text(data['batch_id']) and data['batch_id']==draft['batch_id'],'batch identity mismatch')
    _require(type(data['sources']) is dict and set(data['sources'])=={'pp','ms'},'source roles invalid')
    for role in ('pp','ms'):
        evidence=data['sources'][role]
        raw=Path(inputs[role]).read_bytes()
        _require(set(evidence)=={'sha256','page_count'} and hashlib.sha256(raw).hexdigest()==evidence['sha256'],
                 role+' identity mismatch')
        _require(raw.startswith(b'%PDF-'),'invalid PDF signature')
        _require(type(evidence['page_count']) is int and evidence['page_count']>0 and
                 len(PdfReader(BytesIO(raw)).pages)==evidence['page_count'],'PDF page count mismatch')
    rows=data['records']
    _require(type(rows) is list and len(rows)==len(draft['records'])==13,'Oxford requires 13 complete records')
    for i,(row,old) in enumerate(zip(rows,draft['records']),1):
        _require(type(row) is dict and set(row)==FIELDS,'record fields invalid')
        _require(row['staging_id']==old['staging_id']==f'MOCK-C1-2025-26-Q{i:02d}' and
                 row['question_number']==str(i),'original IDs/order mismatch')
        for key in ('marks','difficulty_proposal'):
            _require(type(row[key]) is int and row[key]==old[key] and row[key]>0,'original '+key+' mismatch')
        _require(row['difficulty_proposal']<=5,'difficulty out of range')
        for key,role in (('question_pages','pp'),('solution_pages','ms')):
            pages=row[key]
            _require(type(pages) is list and pages and pages==old[key] and
                     all(type(n) is int and 1<=n<=data['sources'][role]['page_count'] for n in pages) and
                     sorted(set(pages))==pages,'page mapping invalid')
        _require(_text(row['question_text_original']) and _text(row['review_notes']),'question/review text missing')
        _require(type(row['publisher_ms_original']) is str and row['ms_evidence_level'] in
                 ('full_publisher_ms','outline','missing'),'MS evidence level invalid')
        _require(_text(row['primary_type']) and type(row['tags']) is list and
                 all(_text(t) for t in row['tags']) and len(row['tags'])==len(set(row['tags'])),'taxonomy shape invalid')
        _require(type(row['review']) is dict and set(row['review'])==CHECKS and
                 all(type(v) is bool for v in row['review'].values()),'review checklist invalid')
        _require(type(row['requires_figure']) is bool and type(row['issues']) is list and
                 all(_text(issue) for issue in row['issues']),'review issues invalid')
    _require(sum(r['marks'] for r in rows)==100,'Oxford total marks mismatch')
    return data

def inspect_proposal(inputs, config):
    data=_load(inputs)
    _,primary_types,tags=_formal_indexes(config.releases_root/'V1.22/Joy_M2_Complete_Question_DB_V1_22.sqlite3')
    issues=[]
    for row in data['records']:
        reasons=list(row['issues'])
        if row['ms_evidence_level']!='full_publisher_ms' or not _text(row['publisher_ms_original']):
            reasons.append('complete publisher MS transcription required; outline/missing is not full MS')
        reasons.extend('unreviewed '+k for k,v in sorted(row['review'].items()) if not v)
        if row['requires_figure']:
            reasons.append('necessary figure requires explicit supported canonical image evidence')
        if row['primary_type'] not in primary_types or set(row['tags'])-tags:
            reasons.append('unknown controlled taxonomy')
        if reasons: issues.append({'id':row['staging_id'],'reasons':reasons})
    result={'status':'REVIEW_REQUIRED' if issues else 'AWAITING_TRANSCRIPTION_APPROVAL',
            'record_count':13,'marks':100,'source_type':'publisher_mock',
            'transcription_digest':data['transcription_digest'],
            'proposal_path':str(inputs['proposal']),'issues':issues}
    if not issues:
        result['required_approval']=f"USER APPROVED PDF TRANSCRIPTION BATCH {data['batch_id']} {data['transcription_digest']}"
    return result


def build_package(inputs, approval_text, output_dir, config):
    result=inspect_proposal(inputs,config)
    _require(result['status']=='AWAITING_TRANSCRIPTION_APPROVAL' and
             approval_text==result.get('required_approval'),'exact eligible transcription approval required')
    data=_load(inputs)
    _require(data['transcription_digest']==result['transcription_digest'],'proposal changed during approval check')
    from .hkdse_pdf_adapter import (_validate_output, _file_evidence, _v120_manifest_payload,
                                   _write_private_file, atomic_rename_no_replace)
    from .v123_models import V123BatchImportManifest
    from .v123_manifest import load_v123_import_manifest
    output=_validate_output(Path(output_dir),config)
    for path in inputs.values():
        resolved=Path(path).resolve()
        _require(not resolved.is_relative_to(output),'output overlaps source')
    for ancestor in output.parents:
        if ancestor==config.staging_root: break
        _require(not any((ancestor/n).exists() for n in ('candidate_manifest.json','import_manifest.json')),
                 'output nested in existing artifact')
    candidates=[]
    for i,row in enumerate(data['records']):
        candidates.append({
            'proposed_question_id':row['staging_id'], 'source_id':data['source_id'],
            'source_question_number':row['question_number'], 'source_section':'Oxford 2025/26 C Set 1',
            'source_fragment_hash':hashlib.sha256(row['question_text_original'].encode()).hexdigest(),
            'question_text_original':row['question_text_original'],'question_text_zh':row['question_text_original'],
            'translation_status':'source_present',
            'translation_evidence':f'source:source/transcription.json#records[{i}].question_text_original',
            'solution_original':row['publisher_ms_original'],'solution_verified':'','answer_status':'source_provided',
            'explanation_text':'','explanation_status':'missing','explanation_evidence':None,
            'image_paths':[],'image_roles':[], 'primary_type':row['primary_type'],'tags':row['tags'],
            'tag_status':'proposed','difficulty_level':row['difficulty_proposal'],'difficulty_status':'proposed',
            'enrichment_status':'incomplete'})
    mapping={**PROFILE,'schema_version':'oxford-mock-source-map-v1','batch_id':data['batch_id'],
             'staging_sha256':data['staging_sha256'],'sources':data['sources'],
             'transcription_digest':data['transcription_digest'],'approval_text':approval_text,
             'records':[{k:r[k] for k in ('staging_id','question_number','question_pages','solution_pages',
                                         'marks','review','review_notes','requires_figure','ms_evidence_level','issues')}
                        for r in data['records']]}
    def encode(value): return (canonical(value)+'\n').encode()
    files={'records/candidates.json':encode(candidates), 'source/transcription.json':encode(data),
           'source/source-map.json':encode(mapping),
           'answers/publisher-ms.json':encode({'source_type':'publisher_mock','publisher':'Oxford',
               'records':[{'staging_id':r['staging_id'],'publisher_ms_original':r['publisher_ms_original'],
                           'pages':r['solution_pages']} for r in data['records']]})}
    manifest=V123BatchImportManifest(schema_version='task13-v123-import-manifest-v1',
        batch_id=data['batch_id'],project='Joy M2 AI Database',module='M2',chapter='Oxford Mock M2 C Set 1',
        target_release_version='V1.23',
        candidate_records=(_file_evidence('records/candidates.json',files['records/candidates.json'],'candidate_json'),),
        source_files=tuple(_file_evidence(n,files[n],'source') for n in ('source/transcription.json','source/source-map.json')),
        answer_files=(_file_evidence('answers/publisher-ms.json',files['answers/publisher-ms.json'],'answer'),),
        image_files=(),teacher_notes_files=(),common_errors_files=(),
        language_policy='preserve_source_and_store_reviewed_chinese_separately',
        split_policy='one_complete_question_per_record',difficulty_policy='joy_level_1_5',
        tag_policy='controlled_primary_type_and_tags',answer_policy='preserve_source_answer_identity',
        explanation_policy='source_or_independently_verified_with_identity')
    files['import_manifest.json']=(json.dumps(_v120_manifest_payload(manifest),ensure_ascii=False,
                                             separators=(',',':'),allow_nan=False)+'\n').encode()
    output.parent.mkdir(parents=True,exist_ok=True)
    temporary=Path(tempfile.mkdtemp(prefix='.'+output.name+'-',dir=output.parent))
    try:
        for name,content in files.items():
            path=temporary/name
            path.parent.mkdir(parents=True,exist_ok=True)
            _write_private_file(path,content)
        _require(load_v123_import_manifest(temporary/'import_manifest.json')==manifest,'manifest roundtrip mismatch')
        atomic_rename_no_replace(temporary,output)
    finally:
        if temporary.exists(): shutil.rmtree(temporary)
    return output
