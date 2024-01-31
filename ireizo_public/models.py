from collections import OrderedDict
from datetime import datetime
from http import HTTPStatus
import json
import logging
logger = logging.getLogger(__name__)
import os
import sys

logging.getLogger("elasticsearch").setLevel(logging.WARNING)

from django.conf import settings
import httpx
from rest_framework.exceptions import NotFound
from rest_framework.reverse import reverse

from elastictools import docstore
from elastictools.docstore import elasticsearch_dsl as dsl

from . import definitions

INDEX_PREFIX = 'names'

MAX_SIZE = 1000

MODELS = [
    'ireirecord',
]
SEARCH_MODELS = MODELS
DOCTYPES = [f'{INDEX_PREFIX}{model}' for model in MODELS]
MODELS_DOCTYPES = {model: f'{INDEX_PREFIX}{model}' for model in MODELS}

SEARCH_FORM_LABELS = {}


def _hitvalue(hit, field):
    """Extract list-wrapped values from their lists.
    
    For some reason, Search hit objects wrap values in lists.
    returns the value inside the list.
    
    @param hit: Elasticsearch search hit object
    @param field: str field name
    @return: value
    """
    if hit.get(field) \
       and isinstance(hit[field], list):
        value = hit[field][0]
    elif hit.get(field):
        value = hit[field]
    return None


class Record(dsl.Document):
    """Base record type
    """
    fulltext = dsl.Text()  # see Record.assemble_fulltext()
    
    #class Index:
    #    name = ???
    # We could define Index here but we don't because we want to be consistent
    # with ddr-local and ddr-public.
    
    @staticmethod
    def from_dict(class_, fieldnames, record_id, data):
        """
        @param class_: Person, FarRecord, IreiRecord
        @param fieldnames: list
        @param record_id: str
        @param data: dict
        @returns: Record
        """
        #print(f'  from_dict({class_}, {fieldnames}, {record_id}, data)')
        # Elasticsearch 7 chokes on empty ('') dates so remove from rowd
        empty_dates = [
            fieldname for fieldname,val in data.items()
            if ('date' in fieldname) and (val == '')
        ]
        for fieldname in empty_dates:
            data.pop(fieldname)
        # set values
        record = class_(meta={
            'id': record_id
        })
        record.errors = []
        for field in fieldnames:
            #print(f'    field {field}')
            if data.get(field):
                try:
                    #print(f'      data[field] {data[field]}')
                    setattr(record, field, data[field])
                    #print('       ok')
                except dsl.exceptions.ValidationException:
                    err = ':'.join([field, data[field]])
                    record.errors.append(err)
                    #print(f'       err {err}')
        return record
    
    @staticmethod
    def from_hit(class_, hit):
        """Build Record object from Elasticsearch hit
        @param class_: Person, FarRecord, IreiRecord
        @param hit
        @returns: Record
        """
        hit_d = hit.__dict__['_d_']
        if record_id:
            record = class_(meta={
                'id': record_id
            })
            for field in definitions.FIELDS_MASTER:
                setattr(record, field, _hitvalue(hit_d, field))
            record.assemble_fulltext()
            return record
        record.assemble_fulltext(fieldnames)
        return None
     
    @staticmethod
    def field_values(class_, field, es=None, index=None):
        """Returns unique values and counts for specified field.
        """
        if es and index:
            s = dsl.Search(using=es, index=index)
        else:
            s = dsl.Search()
        s = s.doc_type(class_)
        s.aggs.bucket('bucket', 'terms', field=field, size=1000)
        response = s.execute()
        return [
            (x['key'], x['doc_count'])
            for x in response.aggregations['bucket']['buckets']
        ]

    @staticmethod
    def fields_enriched(record, label=False, description=False, list_fields=[]):
        """Returns dict for each field with value and label etc for display
        
        # list fields and values in order
        >>> for field in record.details.values:
        >>>     print(field.label, field.value)
        
        # access individual values
        >>> record.details.m_dataset.label
        >>> record.details.m_dataset.value
        
        @param record: dict (not an elasticsearch_dsl..Hit)
        @param label: boolean Get pretty label for fields.
        @param description: boolean Get pretty description for fields. boolean
        @param list_fields: list If non-blank get pretty values for these fields.
        @returns: dict
        """
        details = []
        model = record.__class__.Index.model
        fieldnames = FIELDS_BY_MODEL[model]
        for n,fieldname in enumerate(fieldnames):
            try:
                value = getattr(record, fieldname)
            except AttributeError:
                continue
            field_def = definitions.FIELD_DEFINITIONS[model].get(fieldname, {})
            display = field_def.get('display', None)
            if value and display:
                # display datetimes as dates
                if isinstance(value, datetime):
                    value = value.date()
                data = {
                    'field': fieldname,
                    'label': fieldname,
                    'description': '',
                    'value_raw': value,
                    'value': value,
                }
                if (not list_fields) or (fieldname in list_fields):
                    # get pretty value from FIELD_DEFINITIONS
                    choices = field_def.get('choices', {})
                    if choices and choices.get(value, None):
                        data['value'] = choices[value]
                if label:
                    data['label'] = field_def.get('label', fieldname)
                if description:
                    data['description'] = field_def.get('description', '')
                item = (fieldname, data)
                details.append(item)
        return OrderedDict(details)


def assemble_fulltext(record, fieldnames):
    """Assembles single fulltext search field from all string fields
    """
    values = []
    for fieldname in fieldnames:
        value = getattr(record, fieldname, '')
        if value:
            if isinstance(value, str):
                value = value.lower()
            else:
                continue
            values.append(value)
    return ' '.join(values)


FIELDS_IREIRECORD = [
    'irei_id',
    'person',
    'year',
    'birthday',
    'birthdate',
    'name',
    'lastname',
    'firstname',
    'middlename',
    'camps',
    'fetch_ts',
    'timestamp',
]

SEARCH_EXCLUDE_FIELDS_IREIRECORD = []

INCLUDE_FIELDS_IREIRECORD = [
    'irei_id',
    'person',
    'year',
    'birthday',
    'birthdate',
    'name',
    'lastname',
    'firstname',
    'middlename',
    'camps',
    'fetch_ts',
    'timestamp',
]

EXCLUDE_FIELDS_IREIRECORD = []

AGG_FIELDS_IREIRECORD = {}

HIGHLIGHT_FIELDS_IREIRECORD = []

class NestedPerson(dsl.InnerDoc):
    nr_id = dsl.Keyword()
    preferred_name = dsl.Text()

class IreiRecord(Record):
    """IreiRecord model
    """
    irei_id     = dsl.Keyword()
    person      = dsl.Nested(NestedPerson)
    year        = dsl.Integer()
    birthday    = dsl.Text()
    birthdate   = dsl.Date()
    name        = dsl.Text()
    lastname    = dsl.Text()
    firstname   = dsl.Text()
    middlename  = dsl.Text()
    camps       = dsl.Text()
    fetch_ts    = dsl.Date()
    timestamp   = dsl.Date()
    
    class Index:
        model = 'ireirecord'
        name = f'{INDEX_PREFIX}ireirecord'
    
    def __repr__(self):
        return f'<IreiRecord {self.irei_id}>'
    
    @staticmethod
    def get(oid, request):
        """Get record for web app"""
        return docstore_object(request, 'ireirecord', oid)

    @staticmethod
    def from_dict(irei_id, data):
        """
        @param irei_id: str
        @param data: dict
        @returns: IreiRecord
        """
        # exclude private fields
        fieldnames = [
            f for f in FIELDS_IREIRECORD if f not in EXCLUDE_FIELDS_IREIRECORD
        ]
        record = Record.from_dict(IreiRecord, fieldnames, irei_id, data)
        assemble_fulltext(record, fieldnames)
        return record
    
    @staticmethod
    def from_hit(hit):
        """Build IreiRecord object from Elasticsearch hit
        @param hit
        @returns: IreiRecord
        """
        return Record.from_hit(IreiRecord, hit)
     
    @staticmethod
    def field_values(field, es=None, index=None):
        """Returns unique values and counts for specified field.
        """
        return Record.field_values(IreiRecord, field, es, index)


DOCTYPES_BY_MODEL = {
    'ireirecord': f'{INDEX_PREFIX}ireirecord',
}

ELASTICSEARCH_CLASSES_BY_MODEL = {
    'ireirecord': IreiRecord,
}

FIELDS_BY_MODEL = {
    'ireirecord': FIELDS_IREIRECORD,
}

SEARCH_INCLUDE_FIELDS_IREIRECORD = [x for x in FIELDS_IREIRECORD if (x not in SEARCH_EXCLUDE_FIELDS_IREIRECORD)]

SEARCH_INCLUDE_FIELDS = list(set(
    SEARCH_INCLUDE_FIELDS_IREIRECORD
))

SEARCH_AGG_FIELDS = {}
for fieldset in [AGG_FIELDS_IREIRECORD]:
    for key,val in fieldset.items():
        SEARCH_AGG_FIELDS[key] = val

SEARCH_FORM_LABELS = {}

def docstore_object(request, model, oid):
    data = docstore.Docstore(
        INDEX_PREFIX, settings.DOCSTORE_HOST, settings
    ).es.get(
        index=MODELS_DOCTYPES[model],
        id=oid
    )
    return format_object_detail(data, request)

def format_object_detail(document, request, listitem=False):
    """Formats repository objects, adds list URLs,
    """
    if document.get('_source'):
        oid = document['_id']
        model = document['_index']
        document = document['_source']
    else:
        if document.get('irei_id'):
            oid = document['irei_id']
            model = 'ireirecord'
    if model:
        model = model.replace(INDEX_PREFIX, '')
    
    d = OrderedDict()
    d['irei_id'] = oid
    d['model'] = model
    if document.get('index'):
        d['index'] = document.pop('index')
    d['links'] = OrderedDict()
    # accomodate ark/noids
    if model == 'ireirecord':
        #d['links']['html'] = reverse('ireizo-ireirecord', args=[oid], request=request)
        d['links']['json'] = reverse('ireizo-api-ireirecord', args=[oid], request=request)
    #d['title'] = ''
    #d['description'] = ''
    for field in FIELDS_BY_MODEL[model]:
        if document.get(field):
            data = document[field]
            # for some reason person ID is 'id' and not 'nr_id'
            if field == 'person':
                person = {
                    'nr_id': data.pop('id'),
                    'name': data.pop('name'),
                }
                data = person
            d[field] = data
    d['ddr_objects'] = []
    return d

def format_ireirecord(document, request, highlights=None, listitem=False):
    oid = document['irei_id']
    model = 'ireirecord'
    d = OrderedDict()
    d['id'] = oid
    d['model'] = model
    if document.get('index'):
        d['index'] = document.pop('index')
    d['links'] = OrderedDict()
    #d['links']['html'] = reverse('ireizo-ireirecord', args=[oid], request=request)
    d['links']['json'] = reverse('ireizo-api-ireirecord', args=[oid], request=request)
    d['title'] = ''
    d['description'] = ''
    for field in FIELDS_BY_MODEL[model]:
        if document.get(field):
            d[field] = document.pop(field)
    d['highlights'] = join_highlight_text(model, highlights)
    return d

def join_highlight_text(model, highlights):
    """Concatenate highlight text for various fields into one str
    """
    snippets = []
    for field in FIELDS_BY_MODEL[model]:
        if hasattr(highlights, field):
            vals = ' / '.join(getattr(highlights,field))
            text = f'{field}: "{vals}"'
            snippets.append(text)
    return ', '.join(snippets)

FORMATTERS = {
    'namesireirecord': format_ireirecord,
}

class PersonNotFoundError(Exception):
    pass

def irei_person_objects(request, irei_id):
    """Get DDR objects for the Person matching an irei_id"""
    irei_record = IreiRecord.get(irei_id, request)
    try:
        nr_id = irei_record['person']['nr_id']
    except KeyError:
        raise PersonNotFoundError()
    # get data from DDR API
    ddr_response = ddr_objects(nr_id, request)
    ddr_ui_url,ddr_api_url,ddr_status,ddrobjects = ddr_response
    # assemble output
    api_out = {
        'irei_id': irei_id,
        'nr_id': nr_id,
        'name': irei_record['name'],
        'objects': [],
    }
    ALLOW_FIELDS_OBJECTS = ['id','links','title','format', 'credit']
    ALLOW_FIELDS_LINKS = ['html','json','img',]
    for rowd in ddrobjects[:5]:
        for fieldname in [f for f in rowd.keys()]:
            if fieldname not in ALLOW_FIELDS_OBJECTS:
                rowd.pop(fieldname)
        for fieldname in [f for f in rowd['links'].keys()]:
            if fieldname not in ALLOW_FIELDS_LINKS:
                rowd['links'].pop(fieldname)
        api_out['objects'].append(rowd)
    return ddr_status,api_out

def ddr_objects(nr_id, request):
    """Get DDR objects for Person"""
    naan,noid = nr_id.split('/')
    # TODO cache this
    ui_url = f"{settings.DDR_UI_URL}/nrid/{naan}/{noid}/"
    api_url = f"{settings.DDR_API_URL}/api/0.2/nrid/{naan}/{noid}/"
    if settings.DDR_API_USERNAME and settings.DDR_API_PASSWORD:
        r = httpx.get(
            api_url, timeout=settings.DDR_API_TIMEOUT,
            auth=(settings.DDR_API_USERNAME, settings.DDR_API_PASSWORD),
            follow_redirects=True
        )
    else:
        r = httpx.get(
            api_url, timeout=settings.DDR_API_TIMEOUT,
            follow_redirects=True
        )
    if r.status_code == HTTPStatus.OK:
        data = r.json()
        if data.get('objects') and len(data['objects']):
            return ui_url,api_url,r.status_code,data['objects']
    return ui_url,api_url,r.status_code,[]
