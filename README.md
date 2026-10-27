# vector_candela_ccd_parser

A Python library for reading Vector CANdela `.cdd` diagnostic description files. It turns the CDD XML into
an immutable, queryable object model of the ECU's UDS services, and can encode requests and decode
responses at bit level, all without CANdela Studio.

## Use cases

- **Inspect a CDD without CANdela Studio**: list the ECU's services, DIDs, routines, sessions and NRCs from
  a script or CI job.
- **Build diagnostic requests**: generate the default byte sequence for any service (e.g. `22 10 04` for
  ReadDataByIdentifier 0x1004) and use it in test benches, flashing tools or OTA campaigns.
- **Decode ECU responses**: turn raw bytes from a CAN/DoIP trace into named values
  (`62 10 04 7B` → `{"Battery_voltage_30": 123}`).
- **Convert to other formats**: the object model is the input for CDD → ODX/PDX conversion with
  [odxtools](https://github.com/mercedes-benz/odxtools), so CANdela data can be used by ODX-based testers.
- **Diff and review**: compare two CDD revisions at the service and parameter level instead of diffing XML.

## Installation

```sh
git clone https://github.com/OpenAutoDiagLabs/vector_candela_ccd_parser
cd vector_candela_ccd_parser
pip install -r requirements.txt
```

Requires Python 3.10+ and [xsdata](https://pypi.org/project/xsdata/).

## Quick start

```python
from cdd import load_cdd

db = load_cdd("path/to/ECU.cdd", strict=False)
print(db)                      # <CddDatabase ecu='...' services=586 frozen=True>

# Look up a service by qualifier
svc = db.services.Battery_Voltage_Read            # attribute access
svc = db.find_service("Battery_Voltage_Read")     # exact lookup
hits = db.search_services("Voltage")              # fuzzy search

# Encode the default request
print(svc.request.encode_default().hex(" "))      # 22 10 04

# Decode a positive response
print(svc.positive_responses.decode_values(bytes.fromhex("6210047B")))
# {'SID_PR': 98, 'RecordDataIdentifier_1': 4100, 'DataRecord': {'Battery_voltage_30': 123}}
```

Only services instantiated by the ECU (`svc.is_used`) are real diagnostic services; the rest are protocol
templates.

## Examples

| Script | What it does |
|---|---|
| `python example.py ECU.cdd` | Load a file and print the default request of the first services |
| `python example_services.py ECU.cdd` | Print every service with its request/response element layout |
| `python example_decode.py ECU.cdd SERVICE positive "62 10 04 7B"` | Decode a hex payload for one service (`request`, `positive` or `negative`) |

## Public API

| Symbol | Description |
|---|---|
| `load_cdd(path, *, strict=True)` | Load a CDD file and return a `CddDatabase` |
| `load_cdd_from_candela(candela, *, strict=True)` | Build a database from an already parsed `Candela` object |
| `CddDatabase` | Top-level read-only container: `ecu`, `services`, `warnings`, `find_service()`, `search_services()`, `refresh()` |
| `NamedItemList` | List supporting `list[i]`, `list.qualifier`, `list.by_name()`, `list.search()` |
| `CddRef[T]` | Typed lazy reference, resolved after transformation |
| `ObjectRegistry` | Global id → object registry |
| `DuplicateIdError`, `IdNotFoundError` | Registry errors |

**`strict` mode**: `strict=True` raises on the first resolution error; `strict=False` keeps going and
collects messages in `db.warnings`. Documentation-only CDD metadata (author e-mails, attachment proxies,
images) is always skipped.

## How it works

```
.cdd XML ──xsdata──▶ Candela dataclasses (cdd/models/candela.py)
          Phase 1    register every id/oid in an ObjectRegistry
          Phase 2    transformers turn raw objects into model elements (cdd/transformers/)
          Phase 3    resolve CddRef references
          Phase 4    freeze → CddDatabase
```

Model elements (`cdd/models/`):

| Element | CDD source | Meaning |
|---|---|---|
| `ConstElement` | CONSTCOMP | Fixed value (SID, sub-function) |
| `TextTableElement` | TEXTTBL | Raw value ↔ text mapping |
| `LinCompElement` | LINCOMP | Linear conversion `phys = raw * f / div + o` |
| `CodedElement` | IDENT | Raw value, ASCII, BCD or byte field |
| `PlaceholderElement` | GAPDATAOBJ | Reserved / padding bits |
| `StructElement`, `DidElement` | STRUCTDT, STRUCTURE, DID | Ordered group of elements |
| `MultiplexedElement` | MUXCOMP | Selector-dependent branches |
| `NumIterElement` | NUMITERCOMP | Count-driven repetition |

`cdd/codec/` holds the bit-level encoder/decoder: fields are packed in order, MSB-first within a byte;
multi-byte values honour the CDD byte order.

## Fixes in this fork

Compared with the upstream project, this repository:

- reads every member of a `STRUCTDT` (members after the first were silently dropped),
- reads every `SIMPLEPROXYCOMP` of a `NUMITERCOMP` and every `EXTSTORAGEITEM` attachment,
- encodes multi-byte constants stored as byte tuples, e.g. `v='(0,0,96,79,25)'`,
- skips unmodelled documentation metadata instead of failing to load,
- has examples that run from the repository root.

## Known limitations

- Multiplexers that reference `envData` (DTC snapshot / extended data) are not resolved and produce warnings.
- Sub-byte bit order follows the MSB-first convention; verify against a CANdela/CANoe trace for bit-field DIDs.
- Code comments and log messages are still partly in Chinese.

## Credits

Based on [fshoocn/cdd_utils](https://github.com/fshoocn/cdd_utils). The upstream project ships without a
license file.
