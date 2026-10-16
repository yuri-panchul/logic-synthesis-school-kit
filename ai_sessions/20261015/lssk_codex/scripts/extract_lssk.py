#!/usr/bin/env python3
"""Recreate the exact cell-value snapshot using Python's standard library."""
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET
import json
ROOT=Path(__file__).resolve().parents[1]
NS={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
with ZipFile(ROOT/'research/source.xlsx') as z:
 workbook=ET.fromstring(z.read('xl/workbook.xml'))
 relationships=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
 targets={r.attrib['Id']:r.attrib['Target'] for r in relationships}
 shared=[''.join(v.itertext()) for v in ET.fromstring(z.read('xl/sharedStrings.xml'))]
 sheet=next(s for s in workbook.findall('s:sheets/s:sheet',NS) if s.attrib['name']=='LSSK')
 target=targets[sheet.attrib['{'+NS['r']+'}id']]
 name=target.lstrip('/') if target.startswith('/') else 'xl/'+target
 result=[]
 for row in ET.fromstring(z.read(name)).findall('s:sheetData/s:row',NS):
  cells={}
  for cell in row:
   value=cell.find('s:v',NS)
   if value is not None:cells[cell.attrib['r']]=shared[int(value.text)] if cell.attrib.get('t')=='s' else value.text
  result.append(cells)
 (ROOT/'research/lssk_rows.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
 print('Extracted LSSK cells; price formulas use the workbook’s saved values.')
