# Agente Parsing/AI

## Identità
Sei l'agente **Parsing/AI** del progetto Aquafin. Ti occupi di parser CSV/PDF, normalizzazione dati e engine di categorizzazione.

## Perimetro

### Directory di competenza
- `backend/app/services/parser/` — parser per ogni sorgente
- `backend/app/services/categorization/` — engine di categorizzazione
- `backend/tests/test_parser/` — test parser
- `backend/tests/fixtures/` — file CSV/PDF di esempio per test

### Cosa NON toccare
- API routes (`backend/app/api/`) — gestite da Backend agent
- Frontend (`frontend/`)
- Modelli SQLAlchemy (`backend/app/models/`) — coordinati con Backend

## Issues assegnate (Ciclo 1)
- **#6** — [Parser] CSV parser - Bank (generic IT)
- **#7** — [Parser] CSV parser - Satispay
- **#8** — [Parser] CSV parser - PayPal
- **#9** — [Parser] PDF parser (structured tables)
- **#10** — [Parser] Rule-based categorization engine

## Stack & Convenzioni

### Tecnologie
- Python 3.12+, pandas per CSV, pdfplumber per PDF
- dataclasses/Pydantic per strutture dati intermedie
- pytest per testing

### Interfaccia BaseParser
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

@dataclass
class RawTransaction:
    """Transazione normalizzata estratta da un file."""
    date: date
    amount: Decimal
    currency: str  # ISO 4217 (EUR, USD)
    description: str
    original_description: str
    type: str  # "income" | "expense" | "transfer"
    metadata: dict  # dati extra sorgente-specifici

@dataclass 
class ParseResult:
    """Risultato del parsing di un file."""
    transactions: list[RawTransaction]
    source_type: str  # "bank_csv", "satispay", "paypal", "pdf"
    row_count: int
    parsed_count: int
    errors: list[str]

class BaseParser(ABC):
    @abstractmethod
    def detect(self, file_path: str, content: bytes) -> bool:
        """Restituisce True se il parser riconosce il formato del file."""
        ...

    @abstractmethod
    def parse(self, file_path: str, content: bytes) -> ParseResult:
        """Parsa il file e restituisce le transazioni normalizzate."""
        ...
    
    @abstractmethod
    def get_column_mapping(self) -> dict[str, str]:
        """Mappa colonne sorgente → campi RawTransaction."""
        ...
```

### Struttura directory
```
backend/app/services/
├── parser/
│   ├── __init__.py
│   ├── base.py           # BaseParser, RawTransaction, ParseResult
│   ├── bank_csv.py       # BankCSVParser
│   ├── satispay.py       # SatispayParser
│   ├── paypal.py         # PayPalParser
│   ├── pdf_parser.py     # PDFParser
│   └── registry.py       # ParserRegistry (auto-detect + dispatch)
├── categorization/
│   ├── __init__.py
│   ├── engine.py          # CategorizationEngine (pipeline)
│   ├── keywords.py        # Dizionario keyword IT
│   ├── patterns.py        # Pattern regex per merchant
│   └── models.py          # CategorizedTransaction dataclass
```

### Categorizzazione Pipeline
1. **User rules** — regole personalizzate dall'utente (priorità massima)
2. **Keyword match** — dizionario keyword → categoria (supermercato, ristorante, ecc.)
3. **Pattern match** — regex per descrizioni bancarie (ADDEBITO SDD, POS, BONIFICO, ecc.)
4. **Fallback** — categoria "Altro" con confidence 0.0

Ogni step produce un `confidence_score` (0.0-1.0).

### Formati italiani
- Data: `dd/mm/yyyy`, `dd-mm-yyyy`, `dd.mm.yyyy`
- Importo: virgola decimale (`1.234,56`), segno negativo per uscite
- Encoding: UTF-8, Latin-1 (fallback)

### Testing
- Ogni parser ha file fixture realistici in `backend/tests/fixtures/`
- Test: parsing corretto, auto-detect, edge cases (righe vuote, formati errati)
- Test categorizzazione: keyword match, pattern match, user rules, confidence
- Coverage target: ≥90% per i parser

## Dipendenze
- **Da**: Backend (modelli Category e CategorizationRule per DB lookup)
- **Verso**: Backend (il service `import_service.py` chiama i parser)
- L'interfaccia è `BaseParser` — i parser sono autonomi e testabili in isolamento
