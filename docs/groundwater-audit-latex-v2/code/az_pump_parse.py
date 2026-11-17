"""Parse ADWR 'Pump Data Export' files (SpreadsheetML .xls) into one CSV.

Usage: python az_pump_parse.py OUT.csv FILE.xls [FILE.xls ...]
Keeps every row of every worksheet with its header (column names vary by export).
"""
import sys, csv
import xml.etree.ElementTree as ET

NS = {"ss": "urn:schemas-microsoft-com:office:spreadsheet"}
rows_out, header_all = [], []
for path in sys.argv[2:]:
    root = ET.parse(path).getroot()
    for ws in root.findall("ss:Worksheet", NS):
        rows = []
        for r in ws.findall(".//ss:Row", NS):
            rows.append([(c.find("ss:Data", NS).text if c.find("ss:Data", NS) is not None else "") or ""
                         for c in r.findall("ss:Cell", NS)])
        hi = next((i for i, r in enumerate(rows) if "REGISTRY_ID" in r), None)   # wide: one column per year
        if hi is None:
            continue
        head = [h.strip() for h in rows[hi]]
        for h in head:
            if h not in header_all:
                header_all.append(h)
        for r in rows[hi + 1:]:
            if any(x.strip() for x in r):
                rows_out.append(dict(zip(head, [x.strip() for x in r]), sheet=ws.get(f"{{{NS['ss']}}}Name"), file=path))
with open(sys.argv[1], "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=header_all + ["sheet", "file"])
    w.writeheader()
    w.writerows(rows_out)
print(len(rows_out), "rows; columns:", header_all)
