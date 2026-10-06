"""Observed preview coverage, never a document completeness certificate."""


def unknown_coverage(reason='LEGACY_UNKNOWN'):
    return dict(scope='TEXT_PREVIEW_ONLY',status='UNKNOWN',method='UNKNOWN',
                total_pages=None,attempted_pages=None,pages_with_text=None,
                pages_without_text=[],unattempted_pages=None,page_records=[],
                source_chars=None,stored_chars=None,stop_reasons=[reason],
                completeness='NOT_CHECKED',ocr='NOT_RUN')


def summary(coverage):
    c=coverage or unknown_coverage()
    keys=('scope','status','method','total_pages','attempted_pages','pages_with_text',
          'pages_without_text','unattempted_pages','source_chars','stored_chars',
          'stop_reasons','completeness','ocr')
    return {key:c.get(key) for key in keys}


def incomplete(coverage):
    c=coverage or unknown_coverage()
    return c['status']=='UNKNOWN' or bool(c['stop_reasons'] or c['pages_without_text'])


def automatic_summary(source):
    result=dict(scope='UNVERIFIED_EXTRACTION',status='RECORDED',
                method=source['backend'].upper(),completeness='NOT_CHECKED',
                pages_without_text=source['pages_without_text'],
                **{key:source[key] for key in ('total_pages','processed_pages','blocked_pages','failed_pages','ocr')})
    if 'total_units' in source:
        result.update(total_pages=None,processed_pages=None,total_units=source['total_units'],processed_units=source['processed_units'],
                      unit_label=source['unit_label'],limitations=source.get('limitations',[]),physical_pages=None)
    return result
