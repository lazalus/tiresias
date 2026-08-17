"""
런타임 재시작 복구 도구
프로세스 재시작 전에 진행 중이던 그래프/보고서 작업을 실패 상태로 정리합니다.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

from ..models.project import Project, ProjectManager, ProjectStatus
from ..models.task import TaskManager, TaskStatus
from ..utils.logger import get_logger
from .report_agent import Report, ReportManager, ReportStatus


logger = get_logger("tiresias.runtime_recovery")
PROCESS_STARTED_AT = datetime.now()

INCOMPLETE_REPORT_STATUSES = {
    ReportStatus.PENDING,
    ReportStatus.PLANNING,
    ReportStatus.GENERATING,
}


def _parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None

    try:
        normalized = str(value).strip()
        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"
        return datetime.fromisoformat(normalized)
    except Exception:
        return None


def _was_updated_before_process_start(value: Optional[str]) -> bool:
    parsed = _parse_iso_datetime(value)
    return parsed is not None and parsed < PROCESS_STARTED_AT


def _build_interrupted_message(task_label: str) -> str:
    return (
        f"{task_label} 작업이 백엔드 재시작으로 중단되었습니다. "
        "같은 입력으로 다시 시도해주세요."
    )


def reconcile_graph_project_state(project: Optional[Project]) -> Optional[Project]:
    if not project or project.status != ProjectStatus.GRAPH_BUILDING:
        return project

    if not _was_updated_before_process_start(project.updated_at):
        return project

    task = None
    if project.graph_build_task_id:
        task = TaskManager().get_task(project.graph_build_task_id)

    if task and task.status in {TaskStatus.PENDING, TaskStatus.PROCESSING}:
        return project

    project.status = ProjectStatus.FAILED
    project.graph_build_task_id = None
    project.error = _build_interrupted_message("그래프 구축")
    ProjectManager.save_project(project)
    logger.warning("중단된 그래프 구축 작업을 실패 처리했습니다: project_id=%s", project.project_id)
    return project


def _get_report_last_updated_at(report_id: str, report: Optional[Report]) -> Optional[str]:
    progress = ReportManager.get_progress(report_id)
    if progress and progress.get("updated_at"):
        return progress["updated_at"]

    if report and report.completed_at:
        return report.completed_at

    if report and report.created_at:
        return report.created_at

    report_folder = ReportManager._get_report_folder(report_id)
    try:
        if os.path.isdir(report_folder):
            return datetime.fromtimestamp(os.path.getmtime(report_folder)).isoformat()
    except Exception:
        return None

    return None


def _mark_report_failed(report_id: str, report: Optional[Report], message: str) -> Optional[Report]:
    progress = ReportManager.get_progress(report_id) or {}
    completed_titles = progress.get("completed_sections") or []

    if report is None:
        report = Report(
            report_id=report_id,
            simulation_id="",
            graph_id="",
            simulation_requirement="",
            status=ReportStatus.FAILED,
            created_at=datetime.now().isoformat(),
            error=message,
        )
    else:
        report.status = ReportStatus.FAILED
        report.error = message

    ReportManager.save_report(report)
    ReportManager.update_progress(
        report_id,
        "failed",
        -1,
        message,
        completed_sections=completed_titles,
    )
    logger.warning("중단된 보고서 작업을 실패 처리했습니다: report_id=%s", report_id)
    return report


def reconcile_report_state(report_id: str) -> Optional[Report]:
    report = ReportManager.get_report(report_id)
    progress = ReportManager.get_progress(report_id) or {}
    current_status = None

    if report is not None:
        current_status = report.status
    elif progress.get("status"):
        try:
            current_status = ReportStatus(progress["status"])
        except Exception:
            current_status = None

    if current_status not in INCOMPLETE_REPORT_STATUSES:
        return report

    last_updated_at = _get_report_last_updated_at(report_id, report)
    if not _was_updated_before_process_start(last_updated_at):
        return report

    return _mark_report_failed(report_id, report, _build_interrupted_message("보고서 생성"))


def recover_interrupted_runtime_state() -> None:
    recovered_projects = 0
    recovered_reports = 0

    for project in ProjectManager.list_projects(limit=100000):
        previous_status = project.status
        reconciled = reconcile_graph_project_state(project)
        if reconciled and previous_status == ProjectStatus.GRAPH_BUILDING and reconciled.status == ProjectStatus.FAILED:
            recovered_projects += 1

    ReportManager._ensure_reports_dir()
    for item in os.listdir(ReportManager.REPORTS_DIR):
        item_path = os.path.join(ReportManager.REPORTS_DIR, item)
        if os.path.isdir(item_path):
            report_id = item
        elif item.endswith(".json"):
            report_id = item[:-5]
        else:
            continue

        report = ReportManager.get_report(report_id)
        previous_status = report.status if report else None
        reconciled = reconcile_report_state(report_id)
        if previous_status in INCOMPLETE_REPORT_STATUSES:
            if reconciled and reconciled.status == ReportStatus.FAILED:
                recovered_reports += 1

    if recovered_projects or recovered_reports:
        logger.warning(
            "런타임 복구 완료: interrupted_graph_builds=%s interrupted_reports=%s",
            recovered_projects,
            recovered_reports,
        )
    else:
        logger.info("런타임 복구 완료: 중단된 그래프/보고서 작업 없음")
