# Aethersy Research

Deep research brandizzato Aethersy.AI per **Lara/Jarvis**: ricerca multi-fonte,
citazioni verificate e un vault persistente che può essere riutilizzato tra le
sessioni.

Aethersy Research è il porting brandizzato di
[hyperresearch](https://github.com/jordan-gibbs/hyperresearch) di **Jordan
Gibbs**, rilasciato con licenza MIT. Il codice, la pipeline a 16 passaggi, il
server MCP e il meccanismo del vault sono mantenuti; il porting cambia nome,
identità, documentazione e packaging per Aethersy.AI. I crediti originali sono
conservati in [`NOTICE.md`](NOTICE.md) e [`LICENSE`](LICENSE).

Repository: https://github.com/mattiadeblasio94-jpg/aethersy-research

## Installazione nel container Jarvis (Lara)

Per il Dockerfile del container Jarvis usa esattamente:

```bash
pip install "aethersy-research[mcp,parallel] @ git+https://github.com/mattiadeblasio94-jpg/aethersy-research.git"
```

La CLI espone due comandi equivalenti:

```bash
aethersy-research --version
ares --version
```

Requisiti: Python 3.11–3.14 e accesso di rete per recuperare le fonti. Gli extra
`mcp` e `parallel` installano il client MCP richiesto dal server e dal provider
Parallel.

## Uso da Lara/Jarvis

La skill `skills/aethersy-deep-research` è il bootstrap per Lara. Lara chiede
una ricerca approfondita, la skill verifica la CLI e il vault, quindi l'agente
che esegue la pipeline segue i passaggi della pipeline e consegna il report solo
dopo il gate di verifica.

Esempi di comandi operativi:

```bash
aethersy-research init . --json
aethersy-research install . --json
aethersy-research research "domanda di ricerca"
aethersy-research search "argomento" --include-body -j
aethersy-research fetch "https://example.org/studio" --tag argomento -j
aethersy-research run status -j
aethersy-research run finish <vault_tag> --json
```

L'alias `ares` può sostituire `aethersy-research` in ogni comando.

## Vault persistente

Il vault è la parte centrale del porting e conserva il comportamento
dell'originale:

- `.aethersy-research/` contiene configurazione e database SQLite;
- `research/notes/` contiene le note Markdown, che restano la fonte di verità;
- `research/runs/<vault_tag>/` contiene il workspace e il manifest di ogni run;
- `aethersy-research sync` ricostruisce l'indice SQLite dal Markdown;
- ricerche full-text, filtri, backlink, grafo, deduplicazione, lint e
  ranking delle fonti sono disponibili dalla CLI.

In questo modo una sessione successiva di Lara può cercare e riusare le fonti
precedenti prima di recuperare nuovi contenuti.

## Pipeline di ricerca

La pipeline è adattiva e suddivide il lavoro in 16 passaggi: decomposizione
della domanda, ampia ricerca, grafo delle contraddizioni, analisi dei loci,
indagini di profondità, riconciliazione, tensioni tra fonti, critica del
corpus, sintesi delle prove, stesura, critiche avversariali, recupero dei
gap, patch mirate, controllo delle citazioni, lucidatura e revisione della
leggibilità.

Il gate finale verifica struttura, citazioni, citazioni ritrattate e coerenza
numerica. Un report non viene considerato completato se `run finish` non
riporta `"passed": true`.

## Server MCP

Il server MCP espone il vault su stdio:

```bash
aethersy-research mcp
```

Con l'extra `mcp` installato, Lara o un altro client MCP può cercare e leggere
note, elencare fonti, controllare il vault, recuperare URL e creare o
aggiornare note. La configurazione MCP può avviare il comando:

```json
{
  "mcpServers": {
    "aethersy-research": {
      "command": "aethersy-research",
      "args": ["mcp"]
    }
  }
}
```

## Provider web supportati

Il provider si seleziona in `.aethersy-research/config.toml`:

```toml
[web]
provider = "builtin"
```

Provider disponibili:

- `builtin`: recupero HTTP standard, senza dipendenze aggiuntive;
- `crawl4ai`: browser headless, stealth ed estrazione PDF;
- `exa`: ricerca neurale ed estrazione, richiede `EXA_API_KEY`;
- `tavily`: ricerca ed estrazione per agenti, richiede `TAVILY_API_KEY`;
- `parallel`: ricerca via endpoint MCP Parallel, senza chiave;
- `serply`: ricerca Google e recupero pagina tramite Serply, richiede `SERPLY_API_KEY`;
- `keenable`: ricerca e testo pagina tramite Keenable, funziona anche senza chiave con limiti per IP.

Gli extra Python corrispondenti sono `crawl4ai`, `exa`, `tavily` e
`parallel`; Serply e Keenable non richiedono un extra separato.

## Provider accademici e specialistici

La ricerca accademica è disponibile con:

```bash
aethersy-research scholar search "query" -j
aethersy-research scholar sources
```

Provider supportati:

- **OpenAlex**: opere e citazioni su ampia copertura disciplinare;
- **Crossref**: metadati e DOI;
- **DOAB**: libri e capitoli open access peer-reviewed;
- **RePEc**: serie economiche e repertori, con limiti dichiarati dall'API;
- **SEC EDGAR**: ricerca e documenti di regolamentazione;
- **FRED**: serie economiche della Federal Reserve;
- **ClinicalTrials.gov**: studi clinici registrati;
- **CORE**: aggregatore di testi open access, richiede `CORE_API_KEY`.

I risultati delle fonti accademiche vengono deduplicati per DOI, titolo e anno.
Per SEC EDGAR e per i pool "polite" di OpenAlex/Crossref impostare
`AETHERSY_RESEARCH_CONTACT_EMAIL` con un indirizzo email reale.

## Sviluppo

```bash
python -m pip install -e ".[dev]"
pytest
ruff check src tests
mypy src/aethersy_research/
```

## Licenza

MIT. Vedere [`LICENSE`](LICENSE) e [`NOTICE.md`](NOTICE.md) per l'attribuzione
dell'opera originale.
