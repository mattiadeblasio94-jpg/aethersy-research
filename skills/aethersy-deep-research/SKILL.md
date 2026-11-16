---
name: aethersy-deep-research
description: Ricerca approfondita multi-fonte con Aethersy Research. Lara usa questa skill quando l'utente chiede una ricerca approfondita, un report documentato, una revisione della letteratura o un'analisi multi-fonte con citazioni verificate. Verifica che la CLI aethersy-research sia installata, prepara il vault del progetto e affida il lavoro alla pipeline Aethersy a 16 passaggi. Non usarla per ricerche rapide risolvibili con una o due ricerche.
license: MIT
compatibility: Richiede Python 3.11+ e la CLI aethersy-research (`pip install aethersy-research`), oltre all'accesso alla rete per recuperare le fonti.
---

# Ricerca approfondita con Aethersy Research

Questa skill è un bootstrap. La pipeline vera è composta da una skill di ingresso,
16 procedure e un insieme di subagent, installati nel progetto dalla CLI
`aethersy-research`. Lara non deve rispondere alla domanda con le proprie
conoscenze: il deliverable è il report prodotto dalla pipeline.

## 1. Verifica la CLI

Esegui:

```bash
aethersy-research --version
```

Se il comando non esiste, informa l'utente:

> aethersy-research non è installato. Installalo con `pip install "aethersy-research[mcp,parallel] @ git+https://github.com/mattiadeblasio94-jpg/aethersy-research.git"` e riprova.

Non installare pacchetti senza il consenso esplicito dell'utente.

## 2. Prepara il vault

Nel workspace dell'agente che esegue la pipeline, inizializza il vault:

```bash
aethersy-research init . --json
```

Il comando crea `.aethersy-research/` e `research/`. La configurazione del vault
si trova in `.aethersy-research/config.toml`.

## 3. Avvia la pipeline

L'agente che esegue la pipeline deve passare la richiesta dell'utente a
`aethersy-research` senza sintetizzarla o rispondere al posto della pipeline.
La CLI espone il flusso di ricerca, la gestione delle fonti e i controlli del
vault; l'agente segue gli output, i manifest e le fasi richieste.

Usa il comando principale e l'alias interchangeably:

```bash
aethersy-research research "<richiesta dell'utente>"
ares research "<richiesta dell'utente>"
```

Per l'installazione completa della pipeline e degli agenti, usa:

```bash
aethersy-research install . --json
```

Se l'ambiente non supporta un target specifico, l'agente continua a usare la
CLI e il vault; l'installazione è un bootstrap, non un prerequisito per la
logica di ricerca.

## 4. Usa il vault

Il vault conserva note Markdown indicizzate in SQLite. L'agente può cercare,
leggere e collega fonti tra un'esecuzione e la successiva:

```bash
aethersy-research search "argomento" --include-body -j
aethersy-research note show <id> -j
aethersy-research fetch "<url>" --tag <argomento> -j
aethersy-research lint -j
```

## 5. Cita e verifica

La pipeline deve concludere con il controllo di citazioni e il gate finale.
Prima di consegnare il report, verifica il risultato di:

```bash
aethersy-research run finish <vault_tag> --json
```

Il report è pronto solo quando il gate riporta `"passed": true`. Se il gate
fallisce, correggi i problemi segnalati oppure dichiara il run bloccato senza
presentare come completato un report non verificato.

## Ruolo di Lara

Lara coordina la richiesta, controlla il vault e consegna il report verificato.
L'agente che esegue la pipeline svolge il lavoro procedurale; Lara non deve
inventare fonti, citazioni o risultati al posto della pipeline.
