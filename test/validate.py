#!/usr/bin/env python3

from lxml import etree
from io import BytesIO
import sys

filename_xml = sys.argv[1]
filename_xsd = sys.argv[2]

# open and read schema file
with open(filename_xsd, 'rb') as schema_file:
    schema_to_check = schema_file.read()

# open and read xml file
with open(filename_xml, 'rb') as xml_file:
    xml_to_check = xml_file.read()

xmlschema_doc = etree.parse(BytesIO(schema_to_check))
xmlschema = etree.XMLSchema(xmlschema_doc)

# parse xml
try:
    doc = etree.parse(BytesIO(xml_to_check))
    print('XML well formed, syntax ok.')

# check for file IO error
except IOError:
    print('Invalid File')

# check for XML syntax errors
except etree.XMLSyntaxError as err:
    print('XML Syntax Error, see error_syntax.log')
    with open('error_syntax.log', 'w') as error_log_file:
        error_log_file.write(str(err.error_log))
    quit()

except Exception as e:
    print('Unknown error, exiting. %s' % str(e))
    quit()

try:
    xmlschema.assertValid(doc)
    print('XML valid, schema validation ok.')

except etree.DocumentInvalid as err:
    print('Schema validation error, see error_schema.log')
    with open('error_schema.log', 'w') as error_log_file:
        error_log_file.write(str(err.error_log))
    quit()

except:
    print('Unknown error, exiting. 2')
    quit()

