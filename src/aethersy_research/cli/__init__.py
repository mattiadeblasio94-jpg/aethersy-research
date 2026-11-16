"""Aethersy Research CLI — main typer application."""

import os
import sys

# Python version guard. The pyproject.toml `requires-python = ">=3.11,<3.14"`
# normally blocks pip from installing on unsupported versions, but users who
# bypass it (--ignore-requires-python, constraints overrides, or running from
# the source tree) can still land here on 3.14+ where Crawl4AI's lxml~=5.3
# pin breaks. One-line stderr warning so they understand the failure mode
# before it manifests as a cryptic compile error or runtime ImportError.
# Set AETHERSY_RESEARCH_SKIP_PYVER_CHECK=1 to silence (CI, tests).
if sys.version_info >= (3, 14) and not os.environ.get("AETHERSY_RESEARCH_SKIP_PYVER_CHECK"):
    sys.stderr.write(
        f"[aethersy-research] WARNING: Python {sys.version_info.major}.{sys.version_info.minor} "
        "is not yet supported. Please use Python 3.11, 3.12, or 3.13. "
        "Tracking upstream fix at https://github.com/unclecode/crawl4ai/issues/1903\n"
    )

# Fix Windows console encoding — crawl4ai's rich logger uses Unicode chars that
# crash on Windows cp1252 consoles. Reconfigure streams to UTF-8 at startup.
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    os.environ["PYTHONUTF8"] = "1"
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name)
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass

import typer

from aethersy_research import __version__


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"aethersy-research v{__version__}")
        raise typer.Exit()


app = typer.Typer(
    name="aethersy-research",
    help="Agent-driven research knowledge base.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)


@app.callback()
def main(
    version: bool = typer.Option(False, "--version", "-V", callback=_version_callback, is_eager=True, help="Show version"),
) -> None:
    pass


# Root-level commands
from aethersy_research.cli.archive import archive_run as _archive_run
from aethersy_research.cli.dedup import dedup as _dedup
from aethersy_research.cli.fetch import fetch as _fetch
from aethersy_research.cli.import_cmd import import_vault as _import
from aethersy_research.cli.install import install as _install
from aethersy_research.cli.main import init as _init
from aethersy_research.cli.main import status as _status
from aethersy_research.cli.main import sync as _sync
from aethersy_research.cli.mcp_cmd import mcp as _mcp
from aethersy_research.cli.note import note_show as _show
from aethersy_research.cli.repair import repair as _repair
from aethersy_research.cli.research import research as _research
from aethersy_research.cli.search import search as _search
from aethersy_research.cli.serve import serve as _serve
from aethersy_research.cli.tag import tag_list as _tags
from aethersy_research.cli.vault_tag import vault_tag as _vault_tag
from aethersy_research.cli.watch import watch as _watch

app.command("install")(_install)

from aethersy_research.cli.setup import setup as _setup

app.command("setup")(_setup)
app.command("init")(_init)
app.command("status")(_status)
app.command("sync")(_sync)
app.command("search")(_search)
app.command("fetch")(_fetch)

from aethersy_research.cli.fetch_batch import fetch_batch as _fetch_batch

app.command("fetch-batch")(_fetch_batch)
app.command("research")(_research)
app.command("tags")(_tags)
app.command("show", hidden=True)(_show)
app.command("dedup")(_dedup)
app.command("archive-run")(_archive_run)
app.command("vault-tag")(_vault_tag)
app.command("import")(_import)
app.command("repair")(_repair)
app.command("watch")(_watch)
app.command("serve")(_serve)
app.command("mcp")(_mcp)

# Sub-apps
from aethersy_research.cli.batch import app as batch_app
from aethersy_research.cli.config_cmd import app as config_app
from aethersy_research.cli.export import app as export_app
from aethersy_research.cli.git_cmd import app as git_app
from aethersy_research.cli.graph import app as graph_app
from aethersy_research.cli.index import app as index_app
from aethersy_research.cli.lint import app as lint_app
from aethersy_research.cli.note import app as note_app
from aethersy_research.cli.tag import app as tag_app
from aethersy_research.cli.template import app as template_app
from aethersy_research.cli.topic import app as topic_app

app.add_typer(note_app, name="note", help="Note CRUD operations.")
app.add_typer(graph_app, name="graph", help="Knowledge graph and link analysis.")
app.add_typer(index_app, name="index", help="Auto-generated index pages.")
app.add_typer(lint_app, name="lint", help="Health-check the vault.")
app.add_typer(export_app, name="export", help="Export notes.")
app.add_typer(config_app, name="config", help="Configuration.")
app.add_typer(topic_app, name="topic", help="Topic hierarchy.")
app.add_typer(batch_app, name="batch", help="Bulk operations.")
app.add_typer(template_app, name="template", help="Note templates.")
app.add_typer(git_app, name="git", help="Git integration.")
app.add_typer(tag_app, name="tag", help="Tag management.")

from aethersy_research.cli.assets import app as assets_app
from aethersy_research.cli.citecheck_cmd import app as citecheck_app
from aethersy_research.cli.claims_cmd import app as claims_app
from aethersy_research.cli.embed_cmd import app as embed_app
from aethersy_research.cli.escalation_cmd import app as escalation_app
from aethersy_research.cli.levers_cmd import app as levers_app
from aethersy_research.cli.link import app as link_app
from aethersy_research.cli.profile_cmd import app as profile_app
from aethersy_research.cli.run_cmd import app as run_app
from aethersy_research.cli.scholar_cmd import app as scholar_app
from aethersy_research.cli.sources import app as sources_app

app.add_typer(profile_app, name="profile", help="Pipeline profiles (scale parameters).")
app.add_typer(claims_app, name="claims", help="Fetcher-extracted claims (ingest + query).")
app.add_typer(embed_app, name="embed", help="Semantic-search embeddings.")
app.add_typer(run_app, name="run", help="Per-run workspaces + manifest (init/status/resume).")
app.add_typer(escalation_app, name="escalation", help="Browser-lane queue for blocked fetches.")
app.add_typer(citecheck_app, name="citecheck", help="Citation-sentence binding verification.")
app.add_typer(levers_app, name="levers", help="Run levers (register/domain/inference shims).")

app.add_typer(scholar_app, name="scholar", help="Academic and specialist source discovery.")
app.add_typer(sources_app, name="sources", help="Fetched web sources.")
app.add_typer(assets_app, name="assets", help="Downloaded images, screenshots, and media.")
app.add_typer(link_app, name="link", help="Auto-discover and insert wiki-links.")
