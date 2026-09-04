-- Phase 1 schema (no foreign key on training_courses.ncs_cd)
CREATE TABLE IF NOT EXISTS ncs_codes (
    major_cd VARCHAR(2) NOT NULL,
    mid_cd   VARCHAR(2) NOT NULL,
    minor_cd VARCHAR(2) NOT NULL,
    detail_cd VARCHAR(8) PRIMARY KEY,
    detail_nm VARCHAR(255) NOT NULL,
    major_nm VARCHAR(255),
    mid_nm   VARCHAR(255),
    minor_nm VARCHAR(255)
);

-- Index for fast look‑up (soft FK)
CREATE INDEX IF NOT EXISTS idx_ncs_codes_detail_cd ON ncs_codes(detail_cd);

CREATE TABLE IF NOT EXISTS training_courses (
    trpr_id   VARCHAR(20) NOT NULL,
    trpr_degr VARCHAR(20) NOT NULL,
    ncs_cd    VARCHAR(8),
    course_nm VARCHAR(255),
    provider_nm VARCHAR(255),
    start_dt  DATE,
    end_dt    DATE,
    PRIMARY KEY (trpr_id, trpr_degr)
);

-- Soft foreign‑key: just an index for JOIN performance
CREATE INDEX IF NOT EXISTS idx_training_courses_ncs_cd ON training_courses(ncs_cd);
