"""Tests for hook installer and skill file provisioning (aethersy-research roster)."""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess

import pytest

from aethersy_research.core.hooks import (
    _RETIRED_AGENT_FILES,
    _RETIRED_SKILL_DIRS,
    _install_aethersy_research_skill,
    _install_claude_hook,
    _install_depth_critic_agent,
    _install_depth_investigator_agent,
    _install_dialectic_critic_agent,
    _install_instruction_critic_agent,
    _install_loci_analyst_agent,
    _install_patcher_agent,
    _install_polish_auditor_agent,
    _install_researcher_agent,
    _install_source_analyst_agent,
    _install_width_critic_agent,
    _prune_retired_agents,
    _write_hook_script,
    install_hooks,
)

# ---------------------------------------------------------------------------
# Entry skill — installs at /aethersy-research only (v0.8.1+)
# ---------------------------------------------------------------------------


def test_install_aethersy_research_skill_creates_skill_dir(tmp_vault):
    """The entry skill installs at .claude/skills/aethersy-research/SKILL.md so
    Claude Code registers `/aethersy-research` as the slash-command trigger.
    The /research alias was retired in v0.8.1 — only /aethersy-research now.
    """
    result = _install_aethersy_research_skill(tmp_vault.root)
    assert result is not None

    hyper_path = tmp_vault.root / ".claude" / "skills" / "aethersy-research" / "SKILL.md"
    assert hyper_path.exists()

    # /research dir must NOT be created
    research_path = tmp_vault.root / ".claude" / "skills" / "research" / "SKILL.md"
    assert not research_path.exists()

    hyper_body = hyper_path.read_text(encoding="utf-8")
    assert "name: aethersy-research" in hyper_body
    # Entry skill is the chain router — must reference step skills
    assert "aethersy-research-1-decompose" in hyper_body
    assert "aethersy-research-10-triple-draft" in hyper_body
    assert "aethersy-research-11-synthesize" in hyper_body
    assert "aethersy-research-16-readability-audit" in hyper_body
    # Chain mechanics: must explain Skill tool invocation
    assert "Skill" in hyper_body
    # Patching invariant must appear in the skill prose
    assert "PATCH" in hyper_body
    # The most common V7 failure mode (single-draft instead of ensemble) must be
    # called out by name in the entry skill
    assert "PIPELINE VIOLATION" in hyper_body


def test_install_aethersy_research_skill_idempotent(tmp_vault):
    first = _install_aethersy_research_skill(tmp_vault.root)
    assert first is not None
    second = _install_aethersy_research_skill(tmp_vault.root)
    assert second is None


def test_install_aethersy_research_step_skills_creates_all(tmp_vault):
    """Each step skill lives at .claude/skills/aethersy-research-N-name/SKILL.md so the
    orchestrator can invoke it via the Skill tool. All 18 (16 numbered +
    1.5 chapter-partition + 14.5 cite-check) must install on a fresh vault."""
    from aethersy_research.core.hooks import (
        _AETHERSY_RESEARCH_STEP_SKILLS,
        _install_aethersy_research_step_skills,
    )

    result = _install_aethersy_research_step_skills(tmp_vault.root)
    assert result is not None
    assert len(_AETHERSY_RESEARCH_STEP_SKILLS) == 18

    skills_root = tmp_vault.root / ".claude" / "skills"
    for skill_name in _AETHERSY_RESEARCH_STEP_SKILLS:
        skill_path = skills_root / skill_name / "SKILL.md"
        assert skill_path.exists(), f"missing step skill: {skill_name}"

        body = skill_path.read_text(encoding="utf-8")
        # Every step skill must have its name in frontmatter so the Skill tool
        # can invoke it
        assert f"name: {skill_name}" in body
        # Every step skill (except 16, the terminal step) must point to the
        # next step via the Skill tool
        if skill_name != "aethersy-research-16-readability-audit":
            assert "Skill" in body


def test_install_aethersy_research_step_skills_idempotent(tmp_vault):
    from aethersy_research.core.hooks import _install_aethersy_research_step_skills

    first = _install_aethersy_research_step_skills(tmp_vault.root)
    assert first is not None
    second = _install_aethersy_research_step_skills(tmp_vault.root)
    assert second is None


def test_installed_skills_carry_the_resolved_cli_path(tmp_vault):
    """Skills must name the CLI by the path install resolved, the way CLAUDE.md
    and the agent prompts do. `$ARES` shipped for months with nothing defining
    it, so `$ARES run finish` ran as `run finish` (#133)."""
    from aethersy_research.core.hooks import (
        _AETHERSY_RESEARCH_STEP_SKILLS,
        _install_aethersy_research_step_skills,
    )

    ares = r"C:\venv\Scripts\aethersy_research.exe"
    _install_aethersy_research_skill(tmp_vault.root, ares)
    _install_aethersy_research_step_skills(tmp_vault.root, ares)

    skills_root = tmp_vault.root / ".claude" / "skills"
    bodies = {
        name: (skills_root / name / "SKILL.md").read_text(encoding="utf-8")
        for name in ["aethersy-research", *_AETHERSY_RESEARCH_STEP_SKILLS]
    }
    for name, body in bodies.items():
        assert "$ARES" not in body, name
        assert "{ares_path}" not in body, name
    assert "C:/venv/Scripts/aethersy_research.exe run finish" in bodies["aethersy-research"]


# ---------------------------------------------------------------------------
# Subagent installers — per-agent sanity checks
# ---------------------------------------------------------------------------


def test_install_fetcher_agent(tmp_vault):
    result = _install_researcher_agent(tmp_vault.root, "aethersy-research")
    agent_path = tmp_vault.root / ".claude" / "agents" / "aethersy-research-fetcher.md"
    assert agent_path.exists()
    body = agent_path.read_text(encoding="utf-8")
    assert "model: sonnet" in body
    # Summary policy is length-proportional — no hard one-sentence cap.
    # Long sources should get multi-paragraph summaries, short ones stay
    # short. The prompt must discuss both ends of that range AND flag
    # long-source delegation to aethersy-research-source-analyst.
    assert "proportional" in body.lower()
    assert "aethersy-research-source-analyst" in body
    assert "5000 words" in body
    assert result is not None


def test_install_loci_analyst_agent(tmp_vault):
    result = _install_loci_analyst_agent(tmp_vault.root, "aethersy-research")
    agent_path = tmp_vault.root / ".claude" / "agents" / "aethersy-research-loci-analyst.md"
    assert agent_path.exists()
    body = agent_path.read_text(encoding="utf-8")
    assert "model: sonnet" in body
    assert "corpus_evidence" in body
    assert "analyst_id" in body
    assert result is not None


def test_install_depth_investigator_agent(tmp_vault):
    result = _install_depth_investigator_agent(tmp_vault.root, "aethersy-research")
    agent_path = tmp_vault.root / ".claude" / "agents" / "aethersy-research-depth-investigator.md"
    assert agent_path.exists()
    body = agent_path.read_text(encoding="utf-8")
    assert "model: sonnet" in body
    # Depth investigator must have Task tool so it can spawn fetcher subagents
    assert "Task" in body
    assert "interim" in body.lower()
    assert "10 new" in body  # the fetch budget rule
    assert result is not None


def test_install_source_analyst_agent(tmp_vault):
    """The source-analyst reads ONE long source end-to-end on Sonnet's 1M
    context window and produces a structured source-analysis note
    backlinked to the original. Leaf subagent — no Task tool (no
    recursive spawns)."""
    result = _install_source_analyst_agent(tmp_vault.root, "aethersy-research")
    agent_path = tmp_vault.root / ".claude" / "agents" / "aethersy-research-source-analyst.md"
    assert agent_path.exists()
    body = agent_path.read_text(encoding="utf-8")
    assert "model: sonnet" in body
    # Leaf subagent: no Task, cannot spawn other subagents
    assert "tools: Bash, Read, Write" in body
    tools_line = body.split("tools:")[1].split("\n")[0]
    assert "Task" not in tools_line
    # Must produce a source-analysis note (canonical NoteType value)
    assert "source-analysis" in body
    # Structural template sections the prompt mandates
    assert "Thesis / Central claim" in body
    assert "Methodology / Basis of claims" in body
    assert "Key findings" in body
    assert "Load-bearing citations" in body
    assert "Relevance to research_query" in body
    # Backlink mechanism via body breadcrumb (no custom CLI flag needed)
    assert "Suggested by" in body
    # Word-count threshold that decides whether the analyst is appropriate
    assert "5000" in body
    assert result is not None


def test_install_dialectic_critic_agent(tmp_vault):
    result = _install_dialectic_critic_agent(tmp_vault.root, "aethersy-research")
    agent_path = tmp_vault.root / ".claude" / "agents" / "aethersy-research-dialectic-critic.md"
    assert agent_path.exists()
    body = agent_path.read_text(encoding="utf-8")
    assert "model: opus" in body
    # Critics have Bash + Read + Write (Write for JSON output; no Edit
    # since they don't mutate the draft — that's the revisor's job)
    assert "tools: Bash, Read, Write" in body
    assert "recommendation" in body
    assert "location" in body
    assert "surgical" in body.lower()
    assert result is not None


def test_install_depth_critic_agent(tmp_vault):
    result = _install_depth_critic_agent(tmp_vault.root, "aethersy-research")
    agent_path = tmp_vault.root / ".claude" / "agents" / "aethersy-research-depth-critic.md"
    assert agent_path.exists()
    body = agent_path.read_text(encoding="utf-8")
    assert "model: opus" in body
    assert "tools: Bash, Read" in body
    assert "interim" in body.lower()
    assert result is not None


def test_install_width_critic_agent(tmp_vault):
    result = _install_width_critic_agent(tmp_vault.root, "aethersy-research")
    agent_path = tmp_vault.root / ".claude" / "agents" / "aethersy-research-width-critic.md"
    assert agent_path.exists()
    body = agent_path.read_text(encoding="utf-8")
    assert "model: opus" in body
    assert "tools: Bash, Read" in body
    assert "coverage" in body.lower()
    assert result is not None


def test_install_instruction_critic_agent(tmp_vault):
    """Instruction-critic specifically targets the instruction-following
    dimension by checking the draft against prompt-decomposition atomic
    items. Read-only tool lock — it produces findings, never patches."""
    result = _install_instruction_critic_agent(tmp_vault.root, "aethersy-research")
    agent_path = (
        tmp_vault.root / ".claude" / "agents" / "aethersy-research-instruction-critic.md"
    )
    assert agent_path.exists()
    body = agent_path.read_text(encoding="utf-8")
    assert "model: opus" in body
    assert "tools: Bash, Read" in body
    # The critic explicitly consumes the decomposition artifact
    assert "prompt-decomposition.json" in body
    assert "atomic_item" in body
    # Failure modes it tracks
    assert "missing|under-covered|wrong-order|wrong-format" in body
    # Structural-mirror check: runs FIRST, emits findings against
    # required_section_headings. This is the highest-leverage InstF lever.
    assert "STRUCTURAL MIRROR CHECK" in body
    assert "required_section_headings" in body
    # Escalation field for restructures the patcher cannot handle
    assert "requires_orchestrator_restructure" in body
    assert result is not None


def test_install_patcher_agent_is_edit_only(tmp_vault):
    """The revisor (patcher) MUST be tool-locked to Read + Edit only — no
    Write, no Bash. This is the load-bearing invariant that enforces
    REVISE-NOT-REGEN."""
    result = _install_patcher_agent(tmp_vault.root, "aethersy-research")
    agent_path = tmp_vault.root / ".claude" / "agents" / "aethersy-research-patcher.md"
    assert agent_path.exists()
    body = agent_path.read_text(encoding="utf-8")
    # Opus: substance-integration judgment about which findings serve
    # the research_query is a reasoning task Sonnet underperforms on.
    assert "model: opus" in body
    # Tool lock: must be exactly "Read, Edit" — not Write, not Bash. The
    # tool lock is what enforces the no-regeneration invariant.
    assert "tools: Read, Edit" in body
    assert "tools: Bash" not in body
    assert "Write" not in body.split("tools:")[1].split("\n")[0]
    assert "regenerat" in body.lower()  # the invariant spelled out
    assert "surgical" in body.lower()
    # Integrate-don't-caveat rule lifts insight score by preventing
    # hedge-appending edits that dilute committed claims.
    assert "Integrate, don't caveat" in body
    assert "scoping the claim" in body
    # Dynamic revision: revisor reads findings with location/issue/
    # recommendation fields and applies edits using its own judgment.
    assert "location" in body
    assert "recommendation" in body
    assert "requires_orchestrator_restructure" in body
    assert result is not None


def test_install_polish_auditor_agent_is_edit_only(tmp_vault):
    """The polish auditor is the second tool-locked [Read, Edit] agent.
    Same invariant: no regeneration path."""
    result = _install_polish_auditor_agent(tmp_vault.root, "aethersy-research")
    agent_path = tmp_vault.root / ".claude" / "agents" / "aethersy-research-polish-auditor.md"
    assert agent_path.exists()
    body = agent_path.read_text(encoding="utf-8")
    # Opus: semantic rewrites of scaffold vocabulary + hedge-language
    # judgment need strong prose comprehension.
    assert "model: opus" in body
    assert "tools: Read, Edit" in body
    assert "tools: Bash" not in body
    # scaffold-only section list must be injected
    assert "User Prompt (VERBATIM" in body
    # Hedge-language cutting category — strikes softeners on claims the
    # paragraph already supports with evidence. Highest-leverage polish cut.
    assert "Hedge language that softens committed claims" in body
    assert "suggests that" in body
    assert result is not None


# ---------------------------------------------------------------------------
# Idempotency — at least one agent confirms the pattern holds
# ---------------------------------------------------------------------------


def test_loci_analyst_install_idempotent(tmp_vault):
    first = _install_loci_analyst_agent(tmp_vault.root, "aethersy-research")
    assert first is not None
    second = _install_loci_analyst_agent(tmp_vault.root, "aethersy-research")
    assert second is None


def test_patcher_install_idempotent(tmp_vault):
    first = _install_patcher_agent(tmp_vault.root, "aethersy-research")
    assert first is not None
    second = _install_patcher_agent(tmp_vault.root, "aethersy-research")
    assert second is None


# ---------------------------------------------------------------------------
# Retired-roster pruning
# ---------------------------------------------------------------------------


def test_prune_retired_agents_removes_old_files(tmp_vault):
    """Pre-aethersy-research vaults have analyst/auditor/rewriter/subrun/merger agent
    files and a research-ensemble skill dir. Installing onto such a vault
    must prune those so the installed state matches the current architecture."""
    agents_dir = tmp_vault.root / ".claude" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    for name in _RETIRED_AGENT_FILES:
        (agents_dir / name).write_text("pre-aethersy-research content\n", encoding="utf-8")

    skills_dir = tmp_vault.root / ".claude" / "skills"
    for name in _RETIRED_SKILL_DIRS:
        retired_skill = skills_dir / name
        retired_skill.mkdir(parents=True, exist_ok=True)
        # What we actually shipped into these dirs: the entry skill, renamed.
        # Every version of it named the project in its body.
        (retired_skill / "SKILL.md").write_text(
            f"---\nname: {name}\n---\n\n# Deep research\n\nRun the aethersy-research pipeline.\n",
            encoding="utf-8",
        )

    result = _prune_retired_agents(tmp_vault.root)
    assert result is not None
    assert "Pruned retired" in result

    for name in _RETIRED_AGENT_FILES:
        assert not (agents_dir / name).exists(), f"{name} still present"
    for name in _RETIRED_SKILL_DIRS:
        assert not (skills_dir / name).exists(), f"skill dir {name} still present"


def test_prune_retired_agents_noop_on_clean_vault(tmp_vault):
    """On a fresh vault, prune is a no-op."""
    result = _prune_retired_agents(tmp_vault.root)
    assert result is None


def test_prune_retired_agents_spares_a_users_own_research_skill(tmp_vault):
    """`research` is an obvious name for a hand-written personal skill, and on a
    --global install the prune runs against ~/.claude/skills/. Deleting on name
    alone destroyed user content that was never ours (#73)."""
    skills_dir = tmp_vault.root / ".claude" / "skills"
    mine = skills_dir / "research"
    mine.mkdir(parents=True, exist_ok=True)
    (mine / "SKILL.md").write_text(
        "---\nname: research\ndescription: My own literature workflow\n---\n\nStep 1...\n",
        encoding="utf-8",
    )
    (mine / "reference.md").write_text("notes I wrote\n", encoding="utf-8")

    result = _prune_retired_agents(tmp_vault.root)

    assert (mine / "SKILL.md").read_text(encoding="utf-8").startswith("---\nname: research")
    assert (mine / "reference.md").exists()
    # And the user is told it was left behind, rather than it happening silently.
    assert result is not None
    assert "Left alone (not ours)" in result
    assert ".claude/skills/research" in result


def test_prune_retired_agents_spares_a_dir_with_no_skill_file(tmp_vault):
    """No SKILL.md means we have no evidence it was ever ours, so leave it."""
    skills_dir = tmp_vault.root / ".claude" / "skills"
    mine = skills_dir / "research"
    mine.mkdir(parents=True, exist_ok=True)
    (mine / "scratch.txt").write_text("something\n", encoding="utf-8")

    _prune_retired_agents(tmp_vault.root)

    assert (mine / "scratch.txt").exists()


# ---------------------------------------------------------------------------
# PreToolUse hook — the reminder must reach the model (#94)
# ---------------------------------------------------------------------------


def test_installed_hook_delivers_reminder_through_the_injection_channel(tmp_vault):
    """Exit 0 + hookSpecificOutput JSON on stdout is the only channel that
    reaches the model. stderr at exit 0 is written to the debug log, so a hook
    that writes the reminder there has no effect at all."""
    script = _write_hook_script(tmp_vault.root, "aethersy-research").read_text(encoding="utf-8")

    assert "hookSpecificOutput" in script
    assert "hookEventName: 'PreToolUse'" in script
    assert "additionalContext" in script
    assert "process.stderr.write" not in script


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_installed_hook_emits_parseable_injection_json(tmp_vault):
    """Run the installed script the way Claude Code does, and read the channel
    the model reads."""
    hook_path = _write_hook_script(tmp_vault.root, "aethersy-research")

    proc = subprocess.run(
        ["node", str(hook_path)],
        capture_output=True,
        text=True,
        env={**os.environ, "CLAUDE_PROJECT_DIR": str(tmp_vault.root)},
        timeout=60,
    )

    assert proc.returncode == 0, proc.stderr
    assert proc.stderr == ""
    output = json.loads(proc.stdout)["hookSpecificOutput"]
    assert output["hookEventName"] == "PreToolUse"
    assert "AETHERSY_RESEARCH" in output["additionalContext"]
    assert "aethersy-research fetch" in output["additionalContext"]


# ---------------------------------------------------------------------------
# install_hooks — end-to-end integration
# ---------------------------------------------------------------------------


def test_install_hooks_registers_full_aethersy_research_roster(tmp_vault):
    """install_hooks wires the hook, both entry-skill aliases, and the agent roster."""
    actions = install_hooks(tmp_vault.root, "aethersy-research")
    assert actions  # something happened

    # All agent files must be present
    agents_dir = tmp_vault.root / ".claude" / "agents"
    expected_agents = {
        "aethersy-research-fetcher.md",
        "aethersy-research-loci-analyst.md",
        "aethersy-research-depth-investigator.md",
        "aethersy-research-source-analyst.md",
        "aethersy-research-corpus-critic.md",
        "aethersy-research-dialectic-critic.md",
        "aethersy-research-depth-critic.md",
        "aethersy-research-width-critic.md",
        "aethersy-research-instruction-critic.md",
        "aethersy-research-patcher.md",
        "aethersy-research-polish-auditor.md",
        "aethersy-research-readability-recommender.md",
        "aethersy-research-draft-orchestrator.md",
        "aethersy-research-synthesizer.md",
        "aethersy-research-browser-fetcher.md",
        "aethersy-research-cite-checker.md",
    }
    actual_agents = {p.name for p in agents_dir.iterdir() if p.is_file()}
    assert expected_agents == actual_agents, (
        f"missing: {expected_agents - actual_agents}, extra: {actual_agents - expected_agents}"
    )

    # Entry skill registered as /aethersy-research (the /research alias was
    # retired in v0.8.1)
    assert (tmp_vault.root / ".claude" / "skills" / "aethersy-research" / "SKILL.md").exists()
    assert not (tmp_vault.root / ".claude" / "skills" / "research" / "SKILL.md").exists()

    # Hook settings written
    assert (tmp_vault.root / ".claude" / "settings.json").exists()
    assert (tmp_vault.root / ".aethersy-research" / "hook.js").exists()


def test_install_hooks_second_run_is_noop(tmp_vault):
    first = install_hooks(tmp_vault.root, "aethersy-research")
    assert first
    second = install_hooks(tmp_vault.root, "aethersy-research")
    # Hook installer may still report the hook is already installed → no
    # actions or a trivial subset. Must not crash, must not reinstall files.
    assert not second or all("pruned" not in a.lower() for a in second)


# ---------------------------------------------------------------------------
# The registered command must survive the shell that runs it
# ---------------------------------------------------------------------------


def test_installed_hook_command_keeps_the_script_path_in_one_argument(tmp_path):
    """Claude Code runs a hook command through a shell, so an unquoted path is
    split at its first space and node receives a truncated script path. Project
    directories with spaces are ordinary — a Windows user directory, or anything
    under "My Documents" — and the hook then fails on every matching tool call
    without the reminder ever appearing."""
    project = tmp_path / "my project"
    project.mkdir()

    _install_claude_hook(project, "aethersy-research")

    settings = json.loads((project / ".claude" / "settings.json").read_text(encoding="utf-8"))
    command = settings["hooks"]["PreToolUse"][0]["hooks"][0]["command"]

    assert shlex.split(command) == ["node", (project / ".aethersy-research" / "hook.js").as_posix()]
