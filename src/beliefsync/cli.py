from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import BeliefSyncConfig, load_config
from .engine import BeliefSyncEngine
from .llm import LLMConfig, OpenAICompatibleLLMClient, load_text
from .reporting import ReportRenderer
from .store import load_beliefs, load_events, save_actions, save_assessments, save_beliefs, save_report
from .validation import render_validation_report, validate_beliefs, validate_events
from .workspace import (
    WorkspaceState,
    default_scan_output_dir,
    discover_workspace,
    init_workspace,
    load_workspace_config,
    load_workspace_state,
    save_workspace_state,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="beliefsync", description="BeliefSync CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Initialize a local BeliefSync workspace")
    init_parser.add_argument("--path", default=".", help="Target repository path")
    init_parser.add_argument("--repo-id", default="unknown/repo", help="Repository identifier for the workspace config")

    status_parser = subparsers.add_parser("status", help="Show workspace status")
    status_parser.add_argument("--path", default=".", help="Repository or workspace path")

    show_config_parser = subparsers.add_parser("show-config", help="Show the active BeliefSync config")
    show_config_parser.add_argument("--path", default=".", help="Repository or workspace path")
    show_config_parser.add_argument("--config-file", default=None)

    snapshot_parser = subparsers.add_parser("snapshot", help="Create or refresh the baseline belief snapshot in the workspace")
    snapshot_parser.add_argument("--repo-id", required=True)
    snapshot_parser.add_argument("--repo-path", required=True)
    snapshot_parser.add_argument("--issue-file", required=True)
    snapshot_parser.add_argument("--test-log", required=True)
    snapshot_parser.add_argument("--issue-id", default="")
    snapshot_parser.add_argument("--head-ref", default="HEAD")
    snapshot_parser.add_argument("--config-file", default=None)

    refresh_parser = subparsers.add_parser("refresh", help="Refresh stale-belief analysis from the latest workspace snapshot")
    refresh_parser.add_argument("--repo-path", required=True)
    refresh_parser.add_argument("--base-ref", default=None)
    refresh_parser.add_argument("--head-ref", default="HEAD")
    refresh_parser.add_argument("--extra-events-file", default=None)
    refresh_parser.add_argument("--output-dir", default=None)
    refresh_parser.add_argument("--config-file", default=None)
    refresh_parser.add_argument("--format", choices=["text", "json", "markdown", "html"], default="text")

    llm_smoke_parser = subparsers.add_parser("llm-smoke-test", help="Run an LLM smoke test using env-based credentials")

    llm_extract_parser = subparsers.add_parser("llm-extract", help="Use an OpenAI-compatible LLM to extract candidate beliefs")
    llm_extract_parser.add_argument("--repo-id", required=True)
    llm_extract_parser.add_argument("--issue-file", required=True)
    llm_extract_parser.add_argument("--test-log", required=True)
    llm_extract_parser.add_argument("--issue-id", default="")
    llm_extract_parser.add_argument("--commit-hash", default="")
    llm_extract_parser.add_argument("--output", required=True)

    demo_parser = subparsers.add_parser("demo", help="Run the bundled end-to-end demo")
    demo_parser.add_argument("--output-dir", default=None, help="Optional output directory")

    extract_parser = subparsers.add_parser("extract", help="Extract beliefs from issue and test inputs")
    extract_parser.add_argument("--repo-id", required=True)
    extract_parser.add_argument("--issue-file", required=True)
    extract_parser.add_argument("--test-log", required=True)
    extract_parser.add_argument("--commit-hash", default="")
    extract_parser.add_argument("--issue-id", default="")
    extract_parser.add_argument("--output", required=True)

    detect_parser = subparsers.add_parser("detect", help="Detect stale beliefs")
    detect_parser.add_argument("--beliefs-file", required=True)
    detect_parser.add_argument("--events-file", required=True)
    detect_parser.add_argument("--output", default=None)
    detect_parser.add_argument("--config-file", default=None)

    plan_parser = subparsers.add_parser("plan", help="Plan targeted revalidation actions")
    plan_parser.add_argument("--beliefs-file", required=True)
    plan_parser.add_argument("--events-file", required=True)
    plan_parser.add_argument("--output", default=None)
    plan_parser.add_argument("--config-file", default=None)

    report_parser = subparsers.add_parser("report", help="Produce a combined analysis report")
    report_parser.add_argument("--beliefs-file", required=True)
    report_parser.add_argument("--events-file", required=True)
    report_parser.add_argument("--output", default=None)
    report_parser.add_argument("--format", choices=["text", "json", "markdown", "html"], default="text")
    report_parser.add_argument("--config-file", default=None)

    git_parser = subparsers.add_parser("ingest-git", help="Turn a git diff into BeliefSync events")
    git_parser.add_argument("--repo-path", required=True)
    git_parser.add_argument("--base-ref", required=True)
    git_parser.add_argument("--head-ref", default="HEAD")
    git_parser.add_argument("--output", required=True)
    git_parser.add_argument("--config-file", default=None)

    scan_parser = subparsers.add_parser("scan", help="Run extract + ingest-git + report in one command")
    scan_parser.add_argument("--repo-id", required=True)
    scan_parser.add_argument("--repo-path", required=True)
    scan_parser.add_argument("--issue-file", required=True)
    scan_parser.add_argument("--test-log", required=True)
    scan_parser.add_argument("--base-ref", required=True)
    scan_parser.add_argument("--head-ref", default="HEAD")
    scan_parser.add_argument("--issue-id", default="")
    scan_parser.add_argument("--output-dir", default=None)
    scan_parser.add_argument("--config-file", default=None)
    scan_parser.add_argument("--extra-events-file", default=None)
    scan_parser.add_argument("--format", choices=["text", "json", "markdown", "html"], default="text")

    validate_beliefs_parser = subparsers.add_parser("validate-beliefs", help="Validate a belief JSON file")
    validate_beliefs_parser.add_argument("--beliefs-file", required=True)

    validate_events_parser = subparsers.add_parser("validate-events", help="Validate an events JSON file")
    validate_events_parser.add_argument("--events-file", required=True)

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    config = _load_config(args)
    engine = BeliefSyncEngine(config=config)
    renderer = ReportRenderer()

    if args.command == "init":
        workspace = init_workspace(args.path, BeliefSyncConfig(repo_id=args.repo_id))
        print(f"Initialized BeliefSync workspace at {workspace}")
        return

    if args.command == "status":
        workspace = discover_workspace(args.path)
        if workspace is None:
            print("No BeliefSync workspace found.")
            return
        state = load_workspace_state(args.path)
        report_count = len(list((workspace / "reports").glob("*"))) if (workspace / "reports").exists() else 0
        cache_count = len(list((workspace / "cache").glob("*"))) if (workspace / "cache").exists() else 0
        print(f"workspace={workspace}")
        print(f"reports={report_count}")
        print(f"cache_entries={cache_count}")
        print(f"config={(workspace / 'config.json').exists()}")
        if state is not None:
            print(f"repo_id={state.repo_id}")
            print(f"last_head_ref={state.last_head_ref or 'unknown'}")
            print(f"snapshot_beliefs={state.beliefs_file or 'none'}")
        return

    if args.command == "show-config":
        active_config = _load_config(args)
        if active_config is None:
            active_config = BeliefSyncConfig()
        print(json.dumps(active_config.to_dict(), indent=2, ensure_ascii=False))
        return

    if args.command == "llm-smoke-test":
        llm = OpenAICompatibleLLMClient(LLMConfig.from_env())
        smoke = llm.smoke_test()
        result = {
            "base_url": llm.config.base_url,
            "configured_model": llm.config.model,
            "model_used": smoke.get("_beliefsync_model_used", llm.config.model),
            "models_count": smoke.get("_beliefsync_models_count", 0),
            "assistant_reply": smoke["choices"][0]["message"]["content"],
            "usage": smoke.get("usage", {}),
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    if args.command == "llm-extract":
        llm = OpenAICompatibleLLMClient(LLMConfig.from_env())
        beliefs = llm.extract_candidate_beliefs(
            repo_id=args.repo_id,
            issue_text=load_text(args.issue_file),
            test_log_text=load_text(args.test_log),
            issue_id=args.issue_id,
            commit_hash=args.commit_hash,
        )
        save_beliefs(args.output, beliefs)
        print(f"Saved {len(beliefs)} LLM-extracted beliefs to {args.output}")
        return

    if args.command == "snapshot":
        workspace = discover_workspace(args.repo_path)
        if workspace is None:
            workspace = init_workspace(args.repo_path, BeliefSyncConfig(repo_id=args.repo_id))
        beliefs = engine.extract_from_files(
            repo_id=args.repo_id,
            issue_file=args.issue_file,
            test_log_file=args.test_log,
            commit_hash=args.head_ref,
            issue_id=args.issue_id,
        )
        beliefs_file = workspace / "beliefs.json"
        save_beliefs(beliefs_file, beliefs)
        resolved_head = engine.git_events.current_head(args.repo_path) if args.head_ref == "HEAD" else args.head_ref
        state = WorkspaceState(
            repo_id=args.repo_id,
            repo_path=str(Path(args.repo_path).resolve()),
            last_head_ref=resolved_head,
            issue_file=str(Path(args.issue_file).resolve()),
            test_log_file=str(Path(args.test_log).resolve()),
            issue_id=args.issue_id,
            beliefs_file=str(beliefs_file),
        )
        save_workspace_state(workspace / "state.json", state)
        print(f"Saved snapshot with {len(beliefs)} beliefs to {beliefs_file}")
        return

    if args.command == "demo":
        base = Path(__file__).resolve().parents[2] / "examples"
        output_dir = Path(args.output_dir) if args.output_dir else None
        beliefs = engine.extract_from_files(
            repo_id="demo/repo",
            issue_file=base / "demo_issue.md",
            test_log_file=base / "demo_test_log.txt",
            commit_hash="base-demo-commit",
            issue_id="demo-issue-1",
        )
        report = engine.analyze_from_files(
            beliefs_file=_write_temp_beliefs(beliefs, output_dir),
            events_file=base / "demo_events.json",
        )
        print(renderer.render_text(report))
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            save_report(output_dir / "demo_report.json", report)
        return

    if args.command == "extract":
        beliefs = engine.extract_from_files(
            repo_id=args.repo_id,
            issue_file=args.issue_file,
            test_log_file=args.test_log,
            commit_hash=args.commit_hash,
            issue_id=args.issue_id,
        )
        save_beliefs(args.output, beliefs)
        print(f"Saved {len(beliefs)} beliefs to {args.output}")
        return

    if args.command == "validate-beliefs":
        report = validate_beliefs(load_beliefs(args.beliefs_file))
        print(render_validation_report(report, "Belief Validation"))
        return

    if args.command == "validate-events":
        report = validate_events(load_events(args.events_file))
        print(render_validation_report(report, "Event Validation"))
        return

    if args.command == "ingest-git":
        events = engine.ingest_git_events(args.repo_path, args.base_ref, args.head_ref)
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps([event.to_dict() for event in events], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"Saved {len(events)} git-derived events to {args.output}")
        return

    if args.command == "scan":
        output_dir = Path(args.output_dir) if args.output_dir else default_scan_output_dir(args.repo_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        beliefs = engine.extract_from_files(
            repo_id=args.repo_id,
            issue_file=args.issue_file,
            test_log_file=args.test_log,
            commit_hash=args.head_ref,
            issue_id=args.issue_id,
        )
        beliefs_file = output_dir / "beliefs.json"
        save_beliefs(beliefs_file, beliefs)

        events = engine.ingest_git_events(args.repo_path, args.base_ref, args.head_ref)
        if args.extra_events_file:
            events.extend(load_events(args.extra_events_file))
        events_file = output_dir / "events.json"
        events_file.write_text(
            json.dumps([event.to_dict() for event in events], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        report = engine.analyze_from_objects(beliefs, events)
        save_report(output_dir / "report.json", report)
        (output_dir / "report.md").write_text(renderer.render_markdown(report), encoding="utf-8")
        (output_dir / "report.txt").write_text(renderer.render_text(report), encoding="utf-8")
        (output_dir / "report.html").write_text(renderer.render_html(report), encoding="utf-8")
        print(_render_report(renderer, report, args.format))
        print(f"Saved scan artifacts to {output_dir}")
        return

    if args.command == "refresh":
        workspace = discover_workspace(args.repo_path)
        if workspace is None:
            raise SystemExit("No BeliefSync workspace found. Run `beliefsync snapshot` first.")
        state = load_workspace_state(args.repo_path)
        if state is None or not state.beliefs_file:
            raise SystemExit("No BeliefSync snapshot state found. Run `beliefsync snapshot` first.")

        base_ref = args.base_ref or state.last_head_ref
        if not base_ref:
            raise SystemExit("No base ref available. Provide --base-ref or create a snapshot first.")
        head_ref = args.head_ref
        output_dir = Path(args.output_dir) if args.output_dir else default_scan_output_dir(args.repo_path)
        output_dir.mkdir(parents=True, exist_ok=True)

        baseline_beliefs = load_beliefs(Path(state.beliefs_file))
        save_beliefs(output_dir / "beliefs_baseline.json", baseline_beliefs)

        events = engine.ingest_git_events(args.repo_path, base_ref, head_ref)
        if args.extra_events_file:
            events.extend(load_events(args.extra_events_file))
        (output_dir / "events.json").write_text(
            json.dumps([event.to_dict() for event in events], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        report = engine.analyze_from_objects(baseline_beliefs, events)
        save_report(output_dir / "report.json", report)
        (output_dir / "report.md").write_text(renderer.render_markdown(report), encoding="utf-8")
        (output_dir / "report.txt").write_text(renderer.render_text(report), encoding="utf-8")
        (output_dir / "report.html").write_text(renderer.render_html(report), encoding="utf-8")

        refreshed_beliefs = engine.extract_from_files(
            repo_id=state.repo_id,
            issue_file=state.issue_file,
            test_log_file=state.test_log_file,
            commit_hash=head_ref,
            issue_id=state.issue_id,
        )
        workspace_beliefs = workspace / "beliefs.json"
        save_beliefs(workspace_beliefs, refreshed_beliefs)
        save_beliefs(output_dir / "beliefs_refreshed.json", refreshed_beliefs)

        resolved_head = engine.git_events.current_head(args.repo_path) if head_ref == "HEAD" else head_ref
        state.last_base_ref = base_ref
        state.last_head_ref = resolved_head
        state.beliefs_file = str(workspace_beliefs)
        state.last_report_dir = str(output_dir)
        save_workspace_state(workspace / "state.json", state)
        print(_render_report(renderer, report, args.format))
        print(f"Saved refreshed artifacts to {output_dir}")
        return

    report = engine.analyze_from_files(args.beliefs_file, args.events_file)

    if args.command == "detect":
        if args.output:
            save_assessments(args.output, report.assessments)
            print(f"Saved {len(report.assessments)} stale-belief assessments to {args.output}")
        else:
            print(json.dumps([item.to_dict() for item in report.assessments], indent=2, ensure_ascii=False))
        return

    if args.command == "plan":
        if args.output:
            save_actions(args.output, report.actions)
            print(f"Saved {len(report.actions)} revalidation actions to {args.output}")
        else:
            print(json.dumps([item.to_dict() for item in report.actions], indent=2, ensure_ascii=False))
        return

    if args.command == "report":
        rendered = _render_report(renderer, report, args.format)
        if args.output:
            Path(args.output).write_text(rendered, encoding="utf-8")
            print(f"Saved {args.format} report to {args.output}")
        else:
            print(rendered)
        return


def _write_temp_beliefs(beliefs, output_dir: Path | None) -> Path:
    target_dir = output_dir if output_dir else Path.cwd() / ".beliefsync"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / "demo_beliefs.json"
    save_beliefs(target_path, beliefs)
    return target_path


def _load_config(args):
    config_file = getattr(args, "config_file", None)
    if config_file:
        return load_config(config_file)

    candidate_paths: list[Path] = []
    for attr in ("repo_path", "path", "beliefs_file", "events_file", "output"):
        value = getattr(args, attr, None)
        if not value:
            continue
        candidate_paths.append(Path(value).resolve().parent if Path(value).suffix else Path(value).resolve())
    candidate_paths.append(Path.cwd())

    for candidate in candidate_paths:
        config = load_workspace_config(candidate)
        if config is not None:
            return config
    return None


def _render_report(renderer: ReportRenderer, report, output_format: str) -> str:
    if output_format == "json":
        return renderer.render_json(report)
    if output_format == "markdown":
        return renderer.render_markdown(report)
    if output_format == "html":
        return renderer.render_html(report)
    return renderer.render_text(report)
