DO $$ BEGIN
  CREATE TYPE dimension AS ENUM ('completeness','accuracy','validity','timeliness','uniqueness','consistency');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE criticality   AS ENUM ('high','medium','low'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE asset_status  AS ENUM ('draft','active','archived'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE asset_kind AS ENUM ('critical','monitored'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE severity_level AS ENUM ('high','medium','low'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE root_cause     AS ENUM ('capture_ux','integration_etl','process_gap','reference_data','infrastructure','other'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE issue_status   AS ENUM ('open','in_progress','resolved'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE measure_method AS ENUM ('manual','automated'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE measure_source AS ENUM ('manual','seeded','warehouse','monitoring'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE remediation_type AS ENUM ('front_end_validation','etl_fix','training','reference_data','data_repair','process','other'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE TYPE action_status  AS ENUM ('todo','in_progress','done'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS data_assets (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  description text,
  business_purpose text,
  source_system text,
  uc_table_ref text,
  owner_email text,
  steward_email text,
  criticality criticality NOT NULL DEFAULT 'medium',
  status asset_status NOT NULL DEFAULT 'draft',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  created_by text,
  updated_by text
);

CREATE TABLE IF NOT EXISTS quality_rules (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  asset_id uuid NOT NULL REFERENCES data_assets(id) ON DELETE CASCADE,
  dimension dimension NOT NULL,
  name text NOT NULL,
  description text,
  measurement_method text,
  target_threshold numeric,
  unit text NOT NULL DEFAULT '%',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  created_by text,
  updated_by text,
  UNIQUE (asset_id, name)
);

CREATE TABLE IF NOT EXISTS measurements (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  rule_id uuid NOT NULL REFERENCES quality_rules(id) ON DELETE CASCADE,
  score numeric NOT NULL,
  measured_at timestamptz NOT NULL DEFAULT now(),
  method measure_method NOT NULL DEFAULT 'manual',
  source measure_source NOT NULL DEFAULT 'manual',
  evidence_note text,
  sample_size integer,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  created_by text,
  updated_by text
);
CREATE INDEX IF NOT EXISTS idx_measurements_rule_time ON measurements(rule_id, measured_at DESC);

CREATE TABLE IF NOT EXISTS issues (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  asset_id uuid NOT NULL REFERENCES data_assets(id) ON DELETE CASCADE,
  rule_id uuid REFERENCES quality_rules(id) ON DELETE SET NULL,
  title text NOT NULL,
  description text,
  dimension dimension,
  impact_tags text[] NOT NULL DEFAULT '{}',
  severity severity_level NOT NULL DEFAULT 'medium',
  likelihood severity_level NOT NULL DEFAULT 'medium',
  root_cause_category root_cause,
  status issue_status NOT NULL DEFAULT 'open',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  created_by text,
  updated_by text
);

CREATE TABLE IF NOT EXISTS actions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  asset_id uuid NOT NULL REFERENCES data_assets(id) ON DELETE CASCADE,
  issue_id uuid REFERENCES issues(id) ON DELETE SET NULL,
  title text NOT NULL,
  description text,
  remediation_type remediation_type,
  priority severity_level NOT NULL DEFAULT 'medium',
  assignee_email text,
  due_date date,
  status action_status NOT NULL DEFAULT 'todo',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  created_by text,
  updated_by text
);

CREATE TABLE IF NOT EXISTS asset_step_status (
  asset_id uuid NOT NULL REFERENCES data_assets(id) ON DELETE CASCADE,
  item_key text NOT NULL,          -- "1".."7" (parent) or "1a","1b",...,"7b" (sub-step)
  done boolean NOT NULL DEFAULT false,
  updated_at timestamptz NOT NULL DEFAULT now(),
  updated_by text,
  PRIMARY KEY (asset_id, item_key)
);

CREATE TABLE IF NOT EXISTS asset_tables (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  asset_id uuid NOT NULL REFERENCES data_assets(id) ON DELETE CASCADE,
  catalog_name text NOT NULL,
  schema_name text NOT NULL,
  table_name text NOT NULL,
  full_name text NOT NULL,          -- catalog.schema.table
  created_at timestamptz NOT NULL DEFAULT now(),
  created_by text,
  UNIQUE (asset_id, full_name)
);

-- ---------------------------------------------------------------------------
-- Enum extensions (idempotent; ADD VALUE is safe in a transaction on PG 14+
-- as long as the new value is not used in the same transaction;
-- Lakebase runs PG 16 so runtime is fine).
-- ---------------------------------------------------------------------------
ALTER TYPE issue_status  ADD VALUE IF NOT EXISTS 'blocked';
ALTER TYPE action_status ADD VALUE IF NOT EXISTS 'complete';
ALTER TYPE action_status ADD VALUE IF NOT EXISTS 'no_longer_relevant';
ALTER TYPE action_status ADD VALUE IF NOT EXISTS 'not_current_priority';
ALTER TYPE action_status ADD VALUE IF NOT EXISTS 'not_feasible';

-- ---------------------------------------------------------------------------
-- Extended columns for issues (GOV.UK DQAP template fields)
-- ---------------------------------------------------------------------------
ALTER TABLE issues ADD COLUMN IF NOT EXISTS reported_by          text;
ALTER TABLE issues ADD COLUMN IF NOT EXISTS assigned_to          text;
ALTER TABLE issues ADD COLUMN IF NOT EXISTS business_area        text;
ALTER TABLE issues ADD COLUMN IF NOT EXISTS data_subject         text;
ALTER TABLE issues ADD COLUMN IF NOT EXISTS impacted_systems     text;
ALTER TABLE issues ADD COLUMN IF NOT EXISTS example_reference    text;
ALTER TABLE issues ADD COLUMN IF NOT EXISTS system_owner         text;
ALTER TABLE issues ADD COLUMN IF NOT EXISTS related_issues       text;
ALTER TABLE issues ADD COLUMN IF NOT EXISTS comments             text;
ALTER TABLE issues ADD COLUMN IF NOT EXISTS status_date          date;
ALTER TABLE issues ADD COLUMN IF NOT EXISTS priority             severity_level;
ALTER TABLE issues ADD COLUMN IF NOT EXISTS contributing_factors text;
ALTER TABLE issues ADD COLUMN IF NOT EXISTS root_cause_detail    text;

-- ---------------------------------------------------------------------------
-- Extended columns for actions (GOV.UK DQAP template fields)
-- ---------------------------------------------------------------------------
ALTER TABLE actions ADD COLUMN IF NOT EXISTS start_date       date;
ALTER TABLE actions ADD COLUMN IF NOT EXISTS review_date      date;
ALTER TABLE actions ADD COLUMN IF NOT EXISTS completed_date   date;
ALTER TABLE actions ADD COLUMN IF NOT EXISTS success_criteria text;
ALTER TABLE actions ADD COLUMN IF NOT EXISTS notes            text;

-- ---------------------------------------------------------------------------
-- SQL-based measurement support (Phase 2)
-- ---------------------------------------------------------------------------
ALTER TABLE quality_rules ADD COLUMN IF NOT EXISTS measurement_sql text;
ALTER TABLE data_assets ADD COLUMN IF NOT EXISTS kind asset_kind NOT NULL DEFAULT 'critical';

-- ---------------------------------------------------------------------------
-- Customisable org-wide RACI matrix (Task 3)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raci_roles (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL UNIQUE,
  sort_order integer NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(),
  created_by text
);
CREATE TABLE IF NOT EXISTS raci_cells (
  activity_key text NOT NULL,
  role_id uuid NOT NULL REFERENCES raci_roles(id) ON DELETE CASCADE,
  value text NOT NULL DEFAULT '',
  updated_at timestamptz NOT NULL DEFAULT now(),
  updated_by text,
  PRIMARY KEY (activity_key, role_id)
);
