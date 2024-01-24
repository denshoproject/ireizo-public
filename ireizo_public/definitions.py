from collections import OrderedDict


FIELDS_MASTER = []

FIELDS_IREI = []

DATASETS = {}

FIELD_DEFINITIONS = {}


FIELD_DEFINITIONS['ireirecord'] = {}
FIELD_DEFINITIONS['ireirecord']['irei_id'] = {
    'label': "Irei ID",
    'description': 'Unique identifier from Ireizo database',
    'type': 'string',
    'required': True,
    'display': True,
    'sample': 'SAMPLE GOES HERE',
    'notes': 'NOTES GO HERE',
}
FIELD_DEFINITIONS['ireirecord']['name']  = {'label': 'Name', 'description': 'Name'}
FIELD_DEFINITIONS['ireirecord']['lastname']  = {'label': 'Last name', 'description': 'Last name'}
FIELD_DEFINITIONS['ireirecord']['firstname'] = {'label': 'First name', 'description': 'First name'}
FIELD_DEFINITIONS['ireirecord']['middlename'] = {'label': 'Middle name', 'description': 'Middle name'}
FIELD_DEFINITIONS['ireirecord']['birthyear'] = {'label': 'Year of birth', 'description': 'Year of birth'}
FIELD_DEFINITIONS['ireirecord']['birthday'] = {'label': 'Date of birth', 'description': 'Date of birth'}
FIELD_DEFINITIONS['ireirecord']['birthdate'] = {'label': 'Date of birth', 'description': 'Date of birth'}
FIELD_DEFINITIONS['ireirecord']['camps'] = {'label': 'Camps', 'description': 'Camps'}

# set default values until we need to do something else
for model in FIELD_DEFINITIONS.keys():
    for key in FIELD_DEFINITIONS[model].keys():
        item = FIELD_DEFINITIONS[model][key]
        item['type'] = 'string'
        item['required'] = True
        item['display'] = True
        item['sample'] = 'SAMPLE GOES HERE'
        item['notes'] = 'NOTES GO HERE'
