from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from src.config_loader import (
    load_database_settings,
    # load_quality_rules,
    load_raw_data,
    load_reference_data,
)
from src.crawler import crawl_to_files
from src.database import load_to_postgresql
from src.models import PipelinePaths, PipelineResult
from src.quality_checker import validate_books
# from src.reporting import build_report, save_file_outputs
from src.standardizer import standardize_books


def run_full_pipeline(
    paths: PipelinePaths,
    # host: str,
    # port: int,
    skip_crawl: bool,
    load_database: bool,
    env_path: Path,
) -> PipelineResult:
    started_at = datetime.now().replace(microsecond=0)
    crawl_result = None

    if skip_crawl:
        raw_df = load_raw_data(paths.raw_csv)
        crawl_status = "SKIPPED"
        crawl_metadata = None
    else:
        target_url = paths.site_dir
        crawl_result = crawl_to_files(
            site_dir=paths.site_dir,
            url=target_url,
            # host=host,
            # port=port,
            raw_html_path=paths.raw_html,
            raw_csv_path=paths.raw_csv,
            collection_csv_path=paths.collection_csv,
            collection_json_path=paths.collection_json,
        )
        raw_df = crawl_result.raw_df
        crawl_status = "SUCCESS"
        crawl_metadata = crawl_result.metadata

    references = load_reference_data(paths.reference_dir)
    # rules = load_quality_rules(paths.quality_rules)

    standardized_df = standardize_books(
        raw_df=raw_df,
        references=references,
    )
    # validation = validate_books(
    #     standardized_df=standardized_df,
    #     rules=rules,
    # )
    # report = build_report(
    #     standardized_df=standardized_df,
    #     # validation=validation,
    # )
    # save_file_outputs(
    #     standardized_df=standardized_df,
    #     # validation=validation,
    #     # report=report,
    #     paths=paths,
    # )

    database_summary = None
    if load_database:
        settings = load_database_settings(env_path)
        database_summary = load_to_postgresql(
            raw_df=raw_df,
            standardized_df=standardized_df,
            # validation=validation,
            settings=settings,
        )
        paths.database_json.write_text(
            json.dumps(database_summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    completed_at = datetime.now().replace(microsecond=0)
    execution_summary = {
        "started_at": started_at.isoformat(sep=" "),
        "completed_at": completed_at.isoformat(sep=" "),
        "crawl_status": crawl_status,
        "crawl_url": crawl_metadata["final_url"] if crawl_metadata else None,
        "crawl_http_status": crawl_metadata["http_status"] if crawl_metadata else None,
        "raw_csv": str(paths.raw_csv),
        "database_load_requested": load_database,
        "database_load_status": (
            database_summary["status"] if database_summary else "SKIPPED"
        ),
        # **report.payload,
    }
    paths.execution_json.write_text(
        json.dumps(execution_summary, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    # return PipelineResult(
    #     crawl=crawl_result,
    #     # validation=validation,
    #     # report=report,
    #     database_summary=database_summary,
    # )