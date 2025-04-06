"""Fixtures for component tests."""

from typing import Iterator

import pytest


@pytest.fixture(scope="session")
def database_schema() -> Iterator[str]:
    return """
    CREATE TABLE IF NOT EXISTS shift (
        id SERIAL PRIMARY KEY,
        start_time TIMESTAMP WITH TIME ZONE NOT NULL,
        end_time TIMESTAMP WITH TIME ZONE,
        shift_type VARCHAR(10) NOT NULL,
        telescope VARCHAR(10) NOT NULL,
        status VARCHAR(10) NOT NULL
    );
    """


@pytest.fixture
def init_database(postgresql_my):
    """Initialize test database with required schema."""
    cur = postgresql_my.cursor()
    cur.execute(
        """
            CREATE TABLE IF NOT EXISTS public.tab_oda_slt (
                id SERIAL PRIMARY KEY,
                shift_id VARCHAR(50) NOT NULL,
                shift_start TIMESTAMPTZ NOT NULL,
                shift_end TIMESTAMPTZ,
                shift_operator VARCHAR(100) NOT NULL,
                shift_logs JSONB,
                annotations TEXT,
                created_by VARCHAR(50) NOT NULL,
                created_on TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_modified_by VARCHAR(50) NOT NULL,
                last_modified_on TIMESTAMPTZ NOT NULL,
                CONSTRAINT unique_shift UNIQUE (shift_id, shift_start),
                CONSTRAINT unique_shift_id UNIQUE (shift_id)
            );
            CREATE INDEX IF NOT EXISTS idx_tab_oda_slt_shift_id
            ON public.tab_oda_slt (shift_id);
            CREATE INDEX IF NOT EXISTS idx_tab_oda_slt_shift_start
            ON public.tab_oda_slt (shift_start);
            CREATE TABLE IF NOT EXISTS public.tab_oda_slt_shift_comments (
                id SERIAL PRIMARY KEY,
                shift_id VARCHAR(50) NOT NULL,
                operator_name VARCHAR(100) NOT NULL,
                comment TEXT,
                image jsonb NULL,
                created_by VARCHAR(100) NOT NULL,
                created_on TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_modified_on TIMESTAMPTZ NOT NULL,
                last_modified_by VARCHAR(100) NOT NULL,
                CONSTRAINT fk_shift FOREIGN KEY (shift_id)
                REFERENCES public.tab_oda_slt(shift_id)
            );
            CREATE INDEX IF NOT EXISTS idx_tab_oda_slt_shift_comments_shift_id
            ON public.tab_oda_slt_shift_comments (shift_id);
            CREATE INDEX IF NOT EXISTS idx_tab_oda_slt_shift_comments_operator_name
            ON public.tab_oda_slt_shift_comments (operator_name);
            CREATE TABLE IF NOT EXISTS public.tab_oda_slt_shift_log_comments (
                id SERIAL PRIMARY KEY,
                shift_id VARCHAR(50) NOT NULL,
                eb_id VARCHAR(60) NOT NULL,
                operator_name VARCHAR(100) NOT NULL,
                log_comment TEXT,
                image jsonb NULL,
                created_by VARCHAR(100) NOT NULL,
                created_on TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_modified_by VARCHAR(100) NOT NULL,
                last_modified_on TIMESTAMPTZ NOT NULL,
                CONSTRAINT fk_shift FOREIGN KEY (shift_id)
                REFERENCES public.tab_oda_slt(shift_id)
            );
            CREATE INDEX IF NOT EXISTS idx_tab_oda_slt_shift_log_comments_shift_id
            ON public.tab_oda_slt_shift_log_comments (shift_id);
            CREATE INDEX IF NOT EXISTS idx_tab_oda_slt_shift_log_comments_eb_id
            ON public.tab_oda_slt_shift_log_comments (eb_id);
            CREATE INDEX IF NOT EXISTS idx_tab_oda_slt_shift_log_comments_operator_name
            ON public.tab_oda_slt_shift_log_comments (operator_name);
            CREATE TABLE IF NOT EXISTS public.tab_oda_slt_shift_annotations (
                id SERIAL PRIMARY KEY,
                shift_id VARCHAR(50) NOT NULL,
                user_name VARCHAR(100) NOT NULL,
                annotation TEXT,
                created_by VARCHAR(100) NOT NULL,
                created_on TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_modified_on TIMESTAMPTZ NOT NULL,
                last_modified_by VARCHAR(100) NOT NULL,
                CONSTRAINT fk_shift FOREIGN KEY (shift_id)
                REFERENCES public.tab_oda_slt(shift_id)
            );
            CREATE INDEX IF NOT EXISTS idx_tab_oda_slt_shift_annotations_shift_id
            ON public.tab_oda_slt_shift_annotations (shift_id);
            CREATE INDEX IF NOT EXISTS idx_tab_oda_slt_shift_annotations_user_name
            ON public.tab_oda_slt_shift_annotations (user_name);
        """
    )
    postgresql_my.commit()
    cur.close()
    return postgresql_my
