# IncidentLens — תכנון Data Model, API וחוזי מערכת

> מסמך תכנון טכני לפני תחילת מימוש. המסמך נגזר מאפיון Portfolio v2 ומטרתו לנעול את בסיס הנתונים, מחזורי החיים, חוזי ה־API וגבולות האחריות. זהו Design v1; שינוי מבני לאחר תחילת המימוש יתועד ב־ADR וב־Migration ולא ייעשה באופן לא מתועד.

## 1. עקרונות והחלטות בסיס

### 1.1 רמות היקף

כל רכיב מסומן באחת משלוש רמות:

- **VS — Vertical Slice:** המסלול הראשון: Repository + Commit + Stack Trace → File + Symbol + Diff + Evidence Readiness.
- **MVP:** גרסת Portfolio מלאה עד Code-aware RAG, Hypotheses, Trust ו־Evaluation.
- **ROADMAP:** Team mode, Cloud connectors, Sandbox execution ויכולות שאינן נדרשות לגרסת Portfolio.

### 1.2 מוסכמות נתונים

- כל Primary Key עסקי יהיה `UUID` שנוצר באפליקציה.
- כל הזמנים יישמרו כ־`TIMESTAMPTZ` וב־UTC; התצוגה תתאים ל־Timezone של המשתמש.
- שמות טבלאות ועמודות יהיו `snake_case`.
- לכל ישות משתנה יהיו `created_at` ו־`updated_at`.
- ישויות שמייצגות Snapshot או Evidence יהיו Immutable לאחר השלמתן; שינוי יוצר Version חדש.
- `organization_id` ו־`workspace_id` ייכללו במפורש בישויות רגישות כדי לאפשר Scope ברור ושאילתות מאובטחות.
- Enums ימומשו כ־Django `TextChoices` עם `CheckConstraint`, ולא כ־PostgreSQL ENUM, כדי לשמור Migrations פשוטים.
- `JSONB` ישמש רק ל־Metadata משתנה. שדות שמשתתפים בהרשאות, JOIN, סינון או Index יהיו עמודות רגילות.
- אין Cascade delete אוטומטי ל־Audit ול־Resolution. מחיקות Workspace יתבצעו דרך Service מבוקר ו־Background job.
- אין Soft delete גורף. `Source` ו־`Workspace` יקבלו Status; נתונים נגזרים יימחקו פיזית בתהליך Purge מפורש.

### 1.3 החלטת Evidence מרכזית

`evidence_items` היא טבלת האב של כל יחידה שניתנת לאחזור ולציטוט. במקום `source_type + source_id` ללא Foreign Key, לכל טבלת מקור יהיה `OneToOneField` מפורש ל־`evidence_items`:

```text
evidence_items
   ├── code_symbols.evidence_item_id
   ├── document_chunks.evidence_item_id
   ├── log_events.evidence_item_id
   ├── trace_spans.evidence_item_id
   ├── deployments.evidence_item_id
   └── code_changes.evidence_item_id
```

היתרון: Referential integrity אמיתי, Provenance ברור ושאילתת Retrieval אחידה. `evidence_items` מכילה את הטקסט המסונן והמטא־דאטה הדרושים לחיפוש; טבלת המקור מכילה פרטים ייעודיים.

### 1.4 החלטת Embeddings

- Embedding יוצמד ל־`EvidenceItem`, לא רק ל־DocumentChunk.
- ב־MVP יהיה `EmbeddingIndex` פעיל יחיד לכל Workspace, עם Model/Version/Dimensions קבועים.
- `evidence_embeddings.vector` יהיה `vector(N)` בממד קבוע שננעל ב־Migration.
- שינוי למודל בעל ממד אחר דורש טבלה/עמודה ואינדקס חדשים או Migration מבוקר; לא משתמשים בריפוד אפסים.
- לא כל Log יקבל Embedding. רק Error templates, Stack Trace summaries ואירועים משמעותיים יהיו Eligible.

### 1.5 תפקידי מערכת

ב־Local mode קיים משתמש Owner יחיד. המודל נשמר מוכן ל־Team mode:

- `OWNER`: ניהול Workspace, Policies, External AI approval ומחיקה.
- `ENGINEER`: יצירת Incident, חקירה וצפייה ב־Evidence מורשה.
- `VIEWER`: צפייה בלבד.
- `COLLECTOR`: Machine identity עם Scopes מוגבלים ל־Scan/Ingestion.

## 2. תרשים קשרים לוגי

```text
Organization
 ├── Membership ── User
 └── Workspace
      ├── WorkspaceMembership
      ├── Service ── ServiceDependency
      ├── Source
      │    ├── RepositorySnapshot
      │    │    ├── CodeFile
      │    │    ├── CodeSymbol ── SymbolRelation
      │    │    └── CodeChange
      │    ├── SourceDocument ── DocumentChunk
      │    └── EvidenceBundle
      ├── EvidenceItem ── EvidenceEmbedding
      ├── Incident ── IncidentAttachment
      │    ├── ReadinessAssessment
      │    ├── InvestigationRun
      │    │    ├── InvestigationStep
      │    │    ├── RetrievalQuery ── RetrievalResult
      │    │    ├── ContextSnapshot ── ContextSnapshotItem
      │    │    └── Hypothesis ── Claim ── ClaimEvidence
      │    ├── Recommendation
      │    └── Resolution
      ├── EvaluationCase ── EvaluationRun ── EvaluationResult
      └── AuditEvent
```

## 3. טבלאות — Identity, Organization ו־Workspace

### 3.1 `organizations` — VS

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `name` | varchar(120) | not null |
| `slug` | varchar(80) | unique, not null |
| `mode` | varchar(20) | `LOCAL`, `SELF_HOSTED` |
| `is_active` | boolean | default true |
| `created_at` | timestamptz | not null |
| `updated_at` | timestamptz | not null |

ב־Local mode נוצרת Organization אחת ב־Seed/Migration.

### 3.2 `users` — VS

Custom Django user מה־Migration הראשון.

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `email` | varchar(254) | unique, normalized |
| `display_name` | varchar(120) | not null |
| `password` | varchar | מנוהל על ידי Django |
| `is_active` | boolean | default true |
| `is_staff` | boolean | Django Admin |
| `preferred_language` | varchar(5) | `he`, `en` |
| `failed_login_count` | integer | default 0 |
| `locked_until` | timestamptz nullable | Lockout זמני |
| `password_changed_at` | timestamptz nullable | ביטול Sessions ישנות |
| `created_at` | timestamptz | not null |
| `updated_at` | timestamptz | not null |

### 3.3 `organization_memberships` — VS

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `organization_id` | UUID | FK organizations, not null |
| `user_id` | UUID | FK users, not null |
| `role` | varchar(20) | `OWNER`, `ENGINEER`, `VIEWER` |
| `created_at` | timestamptz | not null |

Unique: `(organization_id, user_id)`.

### 3.4 `user_sessions` — VS

Registry מאובטח מעל Django session backend, לצורך הצגה וביטול Sessions. ה־Cookie הגולמי אינו נשמר כאן.

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `user_id` | UUID | FK users, not null |
| `session_key_hash` | char(64) | Hash של מזהה ה־Session, unique |
| `created_at` | timestamptz | not null |
| `last_seen_at` | timestamptz | not null |
| `idle_expires_at` | timestamptz | default: 30 דקות ללא פעילות |
| `absolute_expires_at` | timestamptz | default: 12 שעות |
| `revoked_at` | timestamptz nullable |  |
| `revoked_reason` | varchar(60) nullable | LOGOUT/PASSWORD_CHANGE/ROLE_CHANGE/USER_DISABLED/ADMIN |
| `ip_address` | inet nullable | להצגת Security activity מקומית |
| `user_agent_hash` | char(64) nullable | לא User-Agent גולמי |

Session תקפה רק אם Django session קיימת, הרשומה לא בוטלה ושני זמני התפוגה טרם עברו.

### 3.5 `workspaces` — VS

Workspace הוא גבול הסריקה, האינדוקס וההרשאה.

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `organization_id` | UUID | FK, not null |
| `name` | varchar(120) | not null |
| `slug` | varchar(80) | not null |
| `status` | varchar(20) | `ACTIVE`, `DISABLED`, `PURGING` |
| `root_alias` | varchar(120) | Alias בלבד, לא Host path מלא |
| `language` | varchar(30) | ב־MVP: `PYTHON` |
| `ai_mode` | varchar(30) | `MOCK`, `LOCAL`, `CONTROLLED_EXTERNAL` |
| `external_sharing_policy` | varchar(20) | `DENY`, `ASK`, `ALLOW` |
| `ignore_rules` | text | כללי `.incidentlensignore` מנורמלים |
| `sensitivity_default` | smallint | 0–4 |
| `active_snapshot_id` | UUID nullable | FK repository_snapshots; נוסף לאחר יצירת הטבלה |
| `created_at` | timestamptz | not null |
| `updated_at` | timestamptz | not null |

Unique: `(organization_id, slug)`.

### 3.6 `workspace_memberships` — MVP

מאפשר הרשאה מצומצמת יותר מ־Organization membership.

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `workspace_id` | UUID | FK |
| `user_id` | UUID | FK |
| `role` | varchar(20) | Owner/Engineer/Viewer |
| `environment_access` | varchar[] | למשל `development`, `staging` |
| `sensitivity_ceiling` | smallint | 0–4 |

Unique: `(workspace_id, user_id)`.

### 3.7 `collector_api_tokens` — VS

Token ל־CLI/Collector בלבד. ה־Secret המלא מוצג פעם אחת ואינו נשמר.

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `organization_id` | UUID | FK, not null |
| `workspace_id` | UUID | FK, not null |
| `created_by_id` | UUID | FK users |
| `name` | varchar(120) | תיאור המכשיר/Collector |
| `token_prefix` | varchar(16) | unique, מוצג לצורך זיהוי |
| `secret_hash` | varchar(255) | Password-style hash של Secret אקראי |
| `scopes` | varchar[] | למשל `snapshot:create`, `ingestion:write` |
| `expires_at` | timestamptz | חובה; ללא Token קבוע |
| `last_used_at` | timestamptz nullable |  |
| `revoked_at` | timestamptz nullable |  |
| `rotated_from_id` | UUID nullable | Self FK לצורך Rotation trail |
| `created_at` | timestamptz |  |

Token אינו יכול לקבל Scopes של `evidence:read`, `external_ai:approve` או `users:manage` ב־MVP.

## 4. טבלאות — Services, Sources ו־Secure Intake

### 4.1 `services` — VS

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `workspace_id` | UUID | FK, not null |
| `name` | varchar(120) | not null |
| `runtime_name` | varchar(160) | שם שמופיע ב־Logs/Traces |
| `repository_subpath` | varchar(500) | נתיב יחסי בלבד |
| `language` | varchar(30) | `PYTHON` |
| `default_branch` | varchar(120) | nullable |
| `owner_label` | varchar(120) | nullable |
| `is_active` | boolean | default true |

Unique: `(workspace_id, name)`.

### 4.2 `service_dependencies` — MVP

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `workspace_id` | UUID | FK |
| `source_service_id` | UUID | FK services |
| `target_service_id` | UUID | FK services |
| `relation_type` | varchar(30) | `HTTP`, `QUEUE`, `DATABASE`, `LIBRARY` |
| `criticality` | smallint | 1–5 |
| `valid_from` | timestamptz nullable |  |
| `valid_to` | timestamptz nullable |  |

Check: source != target. Unique active relation לפי source/target/type.

### 4.3 `sources` — VS

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `workspace_id` | UUID | FK |
| `service_id` | UUID nullable | FK services |
| `source_type` | varchar(30) | `LOCAL_REPOSITORY`, `EVIDENCE_BUNDLE`, `LOG`, `TRACE`, `RUNBOOK`, `DEPLOYMENT` |
| `name` | varchar(160) | not null |
| `status` | varchar(20) | `REGISTERED`, `SCANNING`, `READY`, `FAILED`, `DISABLED` |
| `data_policy` | varchar(30) | `LOCAL_ONLY`, `EXTERNAL_AI_ALLOWED` |
| `sensitivity` | smallint | 0–4 |
| `checkpoint` | jsonb | Cursor/version metadata בלבד |
| `last_scanned_at` | timestamptz nullable |  |
| `created_at` | timestamptz |  |
| `updated_at` | timestamptz |  |

### 4.4 `repository_snapshots` — VS

Snapshot קבוע של Commit. Investigation לעולם לא מצביע ל־Branch משתנה בלבד.

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `workspace_id` | UUID | FK |
| `source_id` | UUID | FK sources, source_type=LOCAL_REPOSITORY |
| `requested_ref` | varchar(200) | Branch/Tag/SHA שהמשתמש ביקש |
| `commit_sha` | char(40) | SHA מלא, not null |
| `parent_commit_sha` | char(40) nullable | לצורך Diff |
| `tree_hash` | char(40) | not null |
| `status` | varchar(20) | `QUEUED`, `SCANNING`, `READY`, `FAILED`, `CANCELLED` |
| `parser_version` | varchar(40) | not null |
| `ignore_rules_hash` | char(64) | SHA-256 |
| `file_count` | integer | default 0 |
| `symbol_count` | integer | default 0 |
| `redaction_count` | integer | default 0 |
| `failure_code` | varchar(80) nullable | ללא Payload רגיש |
| `started_at` | timestamptz nullable |  |
| `completed_at` | timestamptz nullable |  |
| `created_at` | timestamptz |  |

Unique: `(workspace_id, commit_sha, parser_version, ignore_rules_hash)`.

### 4.5 `evidence_bundles` — MVP

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `workspace_id` | UUID | FK |
| `source_id` | UUID | FK sources |
| `object_key` | varchar(500) | MinIO/local storage key; לא נתיב משתמש |
| `original_filename` | varchar(255) | sanitized |
| `content_type` | varchar(120) | allowlisted |
| `size_bytes` | bigint | מוגבל |
| `sha256` | char(64) | not null |
| `scan_status` | varchar(20) | `PENDING`, `SCANNING`, `SAFE`, `REJECTED`, `FAILED` |
| `rejection_code` | varchar(80) nullable |  |
| `created_by_id` | UUID | FK users |
| `created_at` | timestamptz |  |

### 4.6 `ingestion_jobs` — VS

מצב עסקי של עבודות Scan/Ingestion; Celery אינו מקור האמת.

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `workspace_id` | UUID | FK |
| `source_id` | UUID | FK |
| `snapshot_id` | UUID nullable | FK |
| `job_type` | varchar(30) | `SCAN_REPOSITORY`, `INGEST_BUNDLE`, `EMBED`, `PURGE` |
| `status` | varchar(20) | `QUEUED`, `RUNNING`, `SUCCEEDED`, `FAILED`, `CANCELLED` |
| `progress_current` | integer | default 0 |
| `progress_total` | integer | default 0 |
| `attempt` | smallint | default 0 |
| `max_attempts` | smallint | default 3 |
| `error_code` | varchar(80) nullable |  |
| `error_summary` | varchar(500) nullable | מסונן |
| `started_at` | timestamptz nullable |  |
| `completed_at` | timestamptz nullable |  |
| `created_at` | timestamptz |  |

## 5. טבלאות — Code Intelligence

### 5.1 `code_files` — VS

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `snapshot_id` | UUID | FK repository_snapshots |
| `service_id` | UUID nullable | FK services |
| `relative_path` | varchar(1000) | לא Host path |
| `language` | varchar(30) | `PYTHON` |
| `sha256` | char(64) | not null |
| `size_bytes` | bigint | not null |
| `line_count` | integer | not null |
| `parse_status` | varchar(20) | `PARSED`, `SKIPPED`, `FAILED` |
| `skip_reason` | varchar(80) nullable |  |
| `redaction_state` | varchar(20) | `CLEAN`, `REDACTED`, `BLOCKED` |
| `created_at` | timestamptz |  |

Unique: `(snapshot_id, relative_path)`.

### 5.2 `evidence_items` — VS

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `organization_id` | UUID | FK, not null |
| `workspace_id` | UUID | FK, not null |
| `service_id` | UUID nullable | FK |
| `snapshot_id` | UUID nullable | FK repository_snapshots |
| `evidence_type` | varchar(30) | `CODE`, `DOCUMENT`, `LOG`, `TRACE`, `DEPLOYMENT`, `CODE_CHANGE`, `STACK_TRACE` |
| `title` | varchar(300) | not null |
| `search_text` | text | Redacted normalized text |
| `search_vector` | tsvector | generated/updated on ingestion |
| `occurred_at` | timestamptz nullable | Runtime time |
| `environment` | varchar(50) nullable |  |
| `trace_id` | varchar(128) nullable |  |
| `error_code` | varchar(160) nullable |  |
| `file_path` | varchar(1000) nullable | relative |
| `symbol_name` | varchar(500) nullable |  |
| `line_start` | integer nullable | 1-based |
| `line_end` | integer nullable | 1-based |
| `commit_sha` | char(40) nullable |  |
| `sensitivity` | smallint | 0–4 |
| `source_status` | varchar(20) | `ACTIVE`, `DISABLED`, `PURGING` |
| `redaction_state` | varchar(20) | CLEAN/REDACTED |
| `content_hash` | char(64) | not null |
| `provenance` | jsonb | Parser/source version; ללא סודות |
| `created_at` | timestamptz |  |

Check: `line_start <= line_end`, כאשר שניהם קיימים.

### 5.3 `code_symbols` — VS

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `evidence_item_id` | UUID | OneToOne evidence_items, unique |
| `snapshot_id` | UUID | FK |
| `code_file_id` | UUID | FK |
| `qualified_name` | varchar(1000) | not null |
| `name` | varchar(300) | not null |
| `kind` | varchar(30) | `MODULE`, `CLASS`, `FUNCTION`, `METHOD`, `TEST`, `ROUTE`, `HANDLER` |
| `line_start` | integer | not null |
| `line_end` | integer | not null |
| `signature` | text nullable | מסונן |
| `doc_summary` | text nullable |  |
| `ast_fingerprint` | char(64) | not null |
| `created_at` | timestamptz |  |

Unique: `(snapshot_id, qualified_name, line_start)`.

### 5.4 `symbol_relations` — VS

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `snapshot_id` | UUID | FK |
| `from_symbol_id` | UUID | FK code_symbols |
| `to_symbol_id` | UUID nullable | FK; nullable אם unresolved |
| `to_qualified_name` | varchar(1000) | not null |
| `relation_type` | varchar(30) | `CALLS`, `IMPORTS`, `DEFINES`, `TESTS`, `HANDLES_EXCEPTION` |
| `confidence` | numeric(4,3) | 0–1; סטטי, לא LLM |
| `line_number` | integer nullable |  |

Unique: `(snapshot_id, from_symbol_id, to_qualified_name, relation_type, line_number)`.

### 5.5 `source_documents` — MVP

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `source_id` | UUID | FK sources |
| `workspace_id` | UUID | FK |
| `uri` | varchar(1000) | logical URI |
| `title` | varchar(300) |  |
| `version` | varchar(120) |  |
| `sha256` | char(64) |  |
| `object_key` | varchar(500) nullable |  |
| `status` | varchar(20) | ACTIVE/DISABLED |
| `created_at` | timestamptz |  |

### 5.6 `document_chunks` — MVP

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `evidence_item_id` | UUID | OneToOne evidence_items |
| `document_id` | UUID | FK source_documents |
| `ordinal` | integer | not null |
| `heading_path` | varchar[] | section hierarchy |
| `page_number` | integer nullable |  |
| `line_start` | integer nullable |  |
| `line_end` | integer nullable |  |
| `chunker_version` | varchar(40) |  |

Unique: `(document_id, ordinal)`.

## 6. טבלאות — Runtime Evidence

### 6.1 `log_events` — MVP

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `evidence_item_id` | UUID | OneToOne evidence_items |
| `workspace_id` | UUID | FK |
| `service_id` | UUID nullable | FK |
| `occurred_at` | timestamptz | not null |
| `severity` | varchar(20) | DEBUG/INFO/WARNING/ERROR/CRITICAL |
| `message_template` | text nullable |  |
| `trace_id` | varchar(128) nullable |  |
| `span_id` | varchar(64) nullable |  |
| `request_id` | varchar(128) nullable |  |
| `attributes` | jsonb | redacted |

Partitioning לפי זמן יתווסף רק לאחר Benchmark. אינדקס ראשוני: `(workspace_id, service_id, occurred_at desc)` ו־`trace_id`.

### 6.2 `trace_spans` — MVP

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `evidence_item_id` | UUID | OneToOne |
| `workspace_id` | UUID | FK |
| `service_id` | UUID nullable | FK |
| `trace_id` | varchar(128) | not null |
| `span_id` | varchar(64) | not null |
| `parent_span_id` | varchar(64) nullable |  |
| `operation_name` | varchar(300) |  |
| `started_at` | timestamptz |  |
| `duration_ms` | numeric(14,3) | >= 0 |
| `status` | varchar(20) | UNSET/OK/ERROR |
| `attributes` | jsonb | redacted |

Unique: `(workspace_id, trace_id, span_id)`.

### 6.3 `deployments` — MVP

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `evidence_item_id` | UUID | OneToOne |
| `workspace_id` | UUID | FK |
| `service_id` | UUID | FK |
| `environment` | varchar(50) |  |
| `version` | varchar(160) |  |
| `commit_sha` | char(40) |  |
| `deployed_at` | timestamptz |  |
| `status` | varchar(20) | STARTED/SUCCEEDED/FAILED/ROLLED_BACK |
| `metadata` | jsonb | redacted |

### 6.4 `code_changes` — VS

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `evidence_item_id` | UUID | OneToOne |
| `snapshot_id` | UUID | FK |
| `code_file_id` | UUID | FK |
| `symbol_id` | UUID nullable | FK code_symbols |
| `commit_sha` | char(40) |  |
| `parent_commit_sha` | char(40) |  |
| `change_type` | varchar(20) | ADDED/MODIFIED/DELETED/RENAMED |
| `diff_text` | text | redacted, bounded |
| `lines_added` | integer |  |
| `lines_deleted` | integer |  |

## 7. טבלאות — Incidents ו־Readiness

### 7.1 `incidents` — VS

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `organization_id` | UUID | FK |
| `workspace_id` | UUID | FK |
| `snapshot_id` | UUID nullable | FK repository_snapshots |
| `created_by_id` | UUID | FK users |
| `title` | varchar(200) | not null |
| `description` | text | symptom בלבד |
| `severity` | varchar(10) | `SEV1`–`SEV4` |
| `status` | varchar(20) | `DRAFT`, `OPEN`, `INVESTIGATING`, `RESOLVED`, `CLOSED` |
| `environment` | varchar(50) |  |
| `started_at` | timestamptz nullable |  |
| `time_uncertainty_seconds` | integer | default 0 |
| `business_impact_started_at` | timestamptz nullable |  |
| `error_code` | varchar(160) nullable |  |
| `trace_id` | varchar(128) nullable |  |
| `request_id` | varchar(128) nullable |  |
| `runtime_version` | varchar(160) nullable |  |
| `readiness_band` | varchar(20) | `UNKNOWN`, `LOW`, `MEDIUM`, `HIGH` |
| `created_at` | timestamptz |  |
| `updated_at` | timestamptz |  |

### 7.2 `incident_services` — VS

Many-to-many בין Incident לשירותים חשודים/מושפעים.

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `incident_id` | UUID | FK |
| `service_id` | UUID | FK |
| `relation` | varchar(20) | `SUSPECTED`, `AFFECTED`, `ROOT_CAUSE` |
| `added_by` | varchar(20) | `USER`, `SYSTEM` |

Unique: `(incident_id, service_id, relation)`.

### 7.3 `incident_attachments` — VS

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `incident_id` | UUID | FK |
| `attachment_type` | varchar(30) | STACK_TRACE/LOG/SCREENSHOT/BUNDLE_ITEM/DEPLOYMENT_METADATA |
| `object_key` | varchar(500) nullable |  |
| `inline_text` | text nullable | מוגבל ומסונן |
| `content_type` | varchar(120) |  |
| `size_bytes` | bigint |  |
| `sha256` | char(64) |  |
| `scan_status` | varchar(20) | PENDING/SAFE/REDACTED/REJECTED/FAILED |
| `redaction_report` | jsonb | Types/counts בלבד |
| `created_by_id` | UUID | FK users |
| `created_at` | timestamptz |  |

Check: בדיוק אחד מ־`object_key`, `inline_text` נדרש לפי סוג הקלט.

### 7.4 `readiness_assessments` — VS

שומרים כל חישוב כדי להסביר מדוע החקירה הורשתה או נחסמה.

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `incident_id` | UUID | FK |
| `assessment_version` | varchar(40) |  |
| `band` | varchar(20) | LOW/MEDIUM/HIGH |
| `can_investigate` | boolean |  |
| `code_version_score` | smallint | 0–100 |
| `error_localization_score` | smallint | 0–100 |
| `runtime_evidence_score` | smallint | 0–100 |
| `provenance_diversity_score` | smallint | 0–100 |
| `available_items` | jsonb | מפת Boolean/IDs |
| `missing_items` | jsonb | Codes + user-facing labels |
| `reason_codes` | varchar[] | דטרמיניסטי |
| `created_at` | timestamptz |  |

ה־Incident שומר רק את ה־Band האחרון; הטבלה שומרת היסטוריה.

## 8. טבלאות — Embeddings ו־Retrieval

### 8.1 `embedding_indexes` — MVP

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `workspace_id` | UUID | FK |
| `model_name` | varchar(160) |  |
| `model_version` | varchar(120) |  |
| `dimensions` | integer | חייב להתאים לסכמה |
| `distance_metric` | varchar(20) | COSINE/IP/L2 |
| `status` | varchar(20) | BUILDING/ACTIVE/RETIRED/FAILED |
| `created_at` | timestamptz |  |
| `activated_at` | timestamptz nullable |  |

Partial unique: Index פעיל אחד לכל Workspace.

### 8.2 `evidence_embeddings` — MVP

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `evidence_item_id` | UUID | FK |
| `embedding_index_id` | UUID | FK |
| `vector` | vector(N) | not null |
| `content_hash` | char(64) | חייב להתאים ל־Evidence בעת היצירה |
| `created_at` | timestamptz |  |

Unique: `(evidence_item_id, embedding_index_id)`. HNSW index על `vector`.

### 8.3 `retrieval_queries` — MVP

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `investigation_run_id` | UUID nullable | FK |
| `workspace_id` | UUID | FK |
| `query_type` | varchar(30) | INCIDENT/SUBQUESTION/FOLLOW_UP/DEBUG |
| `query_text` | text | redacted |
| `filters` | jsonb | Workspace/Commit/Environment/Time scope |
| `pipeline_version` | varchar(40) |  |
| `started_at` | timestamptz |  |
| `completed_at` | timestamptz nullable |  |

### 8.4 `retrieval_results` — MVP

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `retrieval_query_id` | UUID | FK |
| `evidence_item_id` | UUID | FK |
| `exact_rank` | integer nullable |  |
| `fts_rank` | integer nullable |  |
| `vector_rank` | integer nullable |  |
| `temporal_rank` | integer nullable |  |
| `structural_rank` | integer nullable |  |
| `rrf_score` | numeric |  |
| `reranker_score` | numeric nullable |  |
| `final_rank` | integer |  |
| `selection_reason` | varchar[] |  |
| `selected_for_context` | boolean | default false |

Unique: `(retrieval_query_id, evidence_item_id)`.

## 9. טבלאות — Investigation, Hypotheses ו־Citations

### 9.1 `investigation_runs` — MVP

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `incident_id` | UUID | FK |
| `snapshot_id` | UUID | FK; קבוע להרצה |
| `requested_by_id` | UUID | FK users |
| `status` | varchar(30) | QUEUED/PLANNING/RETRIEVING/GENERATING/VALIDATING/COMPLETED/INSUFFICIENT/FAILED/CANCELLED |
| `result_state` | varchar(20) nullable | VERIFIED/PROBABLE/INSUFFICIENT_EVIDENCE |
| `ai_mode` | varchar(30) | MOCK/LOCAL/CONTROLLED_EXTERNAL |
| `pipeline_version` | varchar(40) |  |
| `prompt_version` | varchar(40) |  |
| `sufficiency_iteration` | smallint | default 0 |
| `stop_reason` | varchar(80) nullable |  |
| `context_token_count` | integer | default 0 |
| `input_tokens` | integer | default 0 |
| `output_tokens` | integer | default 0 |
| `estimated_cost` | numeric(12,6) | default 0 |
| `started_at` | timestamptz nullable |  |
| `completed_at` | timestamptz nullable |  |
| `created_at` | timestamptz |  |

Partial unique מומלץ: רק Run פעיל אחד לכל Incident, אלא אם המשתמש יוצר Revision מפורש.

### 9.2 `investigation_steps` — MVP

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `investigation_run_id` | UUID | FK |
| `ordinal` | integer |  |
| `step_type` | varchar(40) | READINESS/PLANNING/RETRIEVAL/EXPANSION/RERANK/SUFFICIENCY/GENERATION/VALIDATION |
| `status` | varchar(20) | QUEUED/RUNNING/SUCCEEDED/FAILED/SKIPPED |
| `input_summary` | jsonb | IDs/counts, לא Payload מלא |
| `output_summary` | jsonb | IDs/counts |
| `duration_ms` | integer nullable |  |
| `error_code` | varchar(80) nullable |  |
| `started_at` | timestamptz nullable |  |
| `completed_at` | timestamptz nullable |  |

Unique: `(investigation_run_id, ordinal)`.

### 9.3 `context_snapshots` — MVP

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `investigation_run_id` | UUID | OneToOne |
| `status` | varchar(20) | DRAFT/AWAITING_APPROVAL/APPROVED/REJECTED/SENT |
| `ai_mode` | varchar(30) |  |
| `estimated_tokens` | integer |  |
| `redaction_count` | integer |  |
| `approved_by_id` | UUID nullable | FK users |
| `approved_at` | timestamptz nullable |  |
| `created_at` | timestamptz |  |

### 9.4 `context_snapshot_items` — MVP

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `context_snapshot_id` | UUID | FK |
| `evidence_item_id` | UUID | FK |
| `ordinal` | integer |  |
| `included_text_hash` | char(64) | מוכיח איזה טקסט נשלח |
| `line_start` | integer nullable |  |
| `line_end` | integer nullable |  |
| `was_redacted` | boolean |  |
| `approved` | boolean | default true |

Unique: `(context_snapshot_id, evidence_item_id)`.

### 9.5 `hypotheses` — MVP

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `investigation_run_id` | UUID | FK |
| `rank` | smallint | 1–3 |
| `title` | varchar(300) |  |
| `summary` | text |  |
| `scope_type` | varchar(30) | SERVICE/FILE/SYMBOL/CONFIG/DEPENDENCY |
| `scope_reference` | varchar(1000) nullable | relative/sanitized |
| `confidence_band` | varchar(20) | LOW/MEDIUM/HIGH |
| `confidence_score_internal` | numeric(5,4) | לא מוצג כאחוז הסתברות |
| `status` | varchar(20) | PROPOSED/ACCEPTED/REJECTED |
| `created_at` | timestamptz |  |

Unique: `(investigation_run_id, rank)`.

### 9.6 `claims` — MVP

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `hypothesis_id` | UUID | FK |
| `ordinal` | integer |  |
| `text` | text | טענה אטומית |
| `claim_type` | varchar(20) | FACT/INFERENCE/UNKNOWN |
| `validation_status` | varchar(20) | PENDING/SUPPORTED/UNSUPPORTED/CONTRADICTED |
| `validation_reason` | varchar(500) nullable |  |

### 9.7 `claim_evidence` — MVP

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `claim_id` | UUID | FK |
| `evidence_item_id` | UUID | FK |
| `relation` | varchar(20) | SUPPORTING/CONTRADICTING/CONTEXTUAL |
| `referential_valid` | boolean |  |
| `support_score` | numeric(5,4) nullable | NLI/rules score, לא certainty |
| `source_span` | jsonb | line/time span |

Unique: `(claim_id, evidence_item_id, relation)`.

### 9.8 `recommendations` — MVP

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `investigation_run_id` | UUID | FK |
| `hypothesis_id` | UUID nullable | FK |
| `title` | varchar(300) |  |
| `instructions` | text | הצעה בלבד |
| `risk_level` | varchar(20) | LOW/MEDIUM/HIGH |
| `status` | varchar(20) | PROPOSED/PLANNED/PERFORMED/SUCCEEDED/FAILED/DISMISSED |
| `user_result` | text nullable |  |
| `created_at` | timestamptz |  |
| `updated_at` | timestamptz |  |

### 9.9 `resolutions` — MVP

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `incident_id` | UUID | OneToOne |
| `verified_by_id` | UUID | FK users |
| `root_cause_summary` | text | אנושי |
| `responsible_service_id` | UUID nullable | FK |
| `responsible_symbol_id` | UUID nullable | FK |
| `verification_method` | varchar(40) | DIRECT_EVIDENCE/REPRODUCTION/OPERATOR_CONFIRMATION/OTHER |
| `fix_reference` | varchar(500) nullable | Commit/PR/Change ID |
| `resolved_at` | timestamptz |  |
| `created_at` | timestamptz |  |

## 10. טבלאות — Evaluation, Security ו־Audit

### 10.1 `evaluation_cases` — MVP

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `workspace_id` | UUID | FK demo workspace |
| `name` | varchar(200) | unique per workspace |
| `dataset_version` | varchar(40) |  |
| `snapshot_id` | UUID | FK |
| `incident_fixture` | jsonb | ללא סודות |
| `expected_result_state` | varchar(20) |  |
| `expected_service_id` | UUID nullable | FK |
| `expected_file_path` | varchar(1000) nullable |  |
| `expected_symbol` | varchar(1000) nullable |  |
| `expected_root_cause` | text |  |
| `required_evidence_ids` | UUID[] | Demo evidence בלבד |
| `security_assertions` | jsonb | secret/injection/authorization expectations |

### 10.2 `evaluation_runs` — MVP

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `dataset_version` | varchar(40) |  |
| `pipeline_version` | varchar(40) |  |
| `embedding_index_id` | UUID nullable | FK |
| `ai_mode` | varchar(30) |  |
| `status` | varchar(20) | QUEUED/RUNNING/COMPLETED/FAILED |
| `configuration` | jsonb | RRF/top-k/reranker/prompt |
| `started_at` | timestamptz nullable |  |
| `completed_at` | timestamptz nullable |  |

### 10.3 `evaluation_results` — MVP

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `evaluation_run_id` | UUID | FK |
| `evaluation_case_id` | UUID | FK |
| `passed` | boolean |  |
| `file_localization_correct` | boolean nullable |  |
| `symbol_localization_correct` | boolean nullable |  |
| `retrieval_recall_at_5` | numeric(5,4) |  |
| `mrr` | numeric(5,4) |  |
| `root_cause_score` | numeric(5,4) | exact/partial rubric |
| `citation_correctness` | numeric(5,4) |  |
| `unsupported_claim_rate` | numeric(5,4) |  |
| `abstention_correct` | boolean |  |
| `secret_leakage_count` | integer | יעד 0 |
| `latency_ms` | integer |  |
| `input_tokens` | integer |  |
| `output_tokens` | integer |  |
| `estimated_cost` | numeric(12,6) |  |
| `details` | jsonb | bounded diagnostics |

Unique: `(evaluation_run_id, evaluation_case_id)`.

### 10.4 `redaction_findings` — VS

לא נשמר הערך הסודי.

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `workspace_id` | UUID | FK |
| `snapshot_id` | UUID nullable | FK |
| `attachment_id` | UUID nullable | FK |
| `relative_path` | varchar(1000) nullable |  |
| `finding_type` | varchar(80) | API_KEY/PRIVATE_KEY/TOKEN/PII/etc. |
| `line_number` | integer nullable |  |
| `detector` | varchar(40) | REGEX/ENTROPY/POLICY |
| `action` | varchar(20) | REDACTED/BLOCKED |
| `fingerprint` | char(64) | hash לא הפיך לצורך dedup |
| `created_at` | timestamptz |  |

Check: לפחות אחד מ־snapshot/attachment קיים.

### 10.5 `external_ai_approvals` — MVP

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `context_snapshot_id` | UUID | OneToOne |
| `requested_by_id` | UUID | FK |
| `decision` | varchar(20) | APPROVED/REJECTED/EXPIRED |
| `evidence_ids` | UUID[] | IDs בלבד |
| `provider_name` | varchar(120) |  |
| `policy_version` | varchar(40) |  |
| `decided_at` | timestamptz |  |

### 10.6 `audit_events` — VS

| עמודה | טיפוס | אילוץ/הערה |
|---|---|---|
| `id` | UUID | PK |
| `organization_id` | UUID | FK |
| `workspace_id` | UUID nullable | FK |
| `actor_user_id` | UUID nullable | FK |
| `actor_type` | varchar(20) | USER/COLLECTOR/SYSTEM |
| `action` | varchar(120) | structured code |
| `object_type` | varchar(80) |  |
| `object_id` | UUID nullable |  |
| `request_id` | UUID nullable |  |
| `outcome` | varchar(20) | SUCCEEDED/DENIED/FAILED |
| `ip_address` | inet nullable |  |
| `metadata` | jsonb | IDs/counts בלבד |
| `created_at` | timestamptz | append-only |

Index: `(workspace_id, created_at desc)`, `(actor_user_id, created_at desc)`.

## 11. אינדקסים מרכזיים

### 11.1 Scope והרשאות

```text
evidence_items(workspace_id, source_status, sensitivity, environment)
evidence_items(workspace_id, snapshot_id, evidence_type)
incidents(workspace_id, status, created_at desc)
repository_snapshots(workspace_id, commit_sha)
```

### 11.2 Exact ו־Structural retrieval

```text
evidence_items(workspace_id, trace_id) WHERE trace_id IS NOT NULL
evidence_items(workspace_id, error_code) WHERE error_code IS NOT NULL
evidence_items(snapshot_id, file_path, line_start, line_end)
code_symbols(snapshot_id, qualified_name)
symbol_relations(snapshot_id, from_symbol_id, relation_type)
symbol_relations(snapshot_id, to_symbol_id, relation_type)
```

### 11.3 Full-Text ו־Vector

```sql
CREATE INDEX evidence_search_vector_gin
ON evidence_items USING GIN (search_vector);

CREATE INDEX evidence_embedding_hnsw
ON evidence_embeddings USING hnsw (vector vector_cosine_ops);
```

שאילתת ANN חייבת לכלול `workspace_id`, `snapshot_id`, `source_status`, `sensitivity` ו־`environment` ב־WHERE. לפני הצגה או שליחה למודל מתבצעת בדיקת Policy נוספת.

## 12. State Machines

### 12.1 Repository Snapshot

```text
QUEUED → SCANNING → READY
                  ↘ FAILED
QUEUED/SCANNING → CANCELLED
```

רק Snapshot במצב `READY` ניתן להצמיד ל־Investigation.

### 12.2 Incident

```text
DRAFT → OPEN → INVESTIGATING → RESOLVED → CLOSED
             ↘ OPEN
```

`RESOLVED` מחייב Resolution. פתיחה מחדש יוצרת Audit event ואינה מוחקת Resolution קודם; היא יוצרת Revision או מסמנת אותו Superseded בהרחבה עתידית.

### 12.3 Investigation Run

```text
QUEUED → PLANNING → RETRIEVING → GENERATING → VALIDATING → COMPLETED
                    ↘ INSUFFICIENT
כל מצב פעיל → FAILED / CANCELLED
```

ב־`CONTROLLED_EXTERNAL`, לאחר Context selection:

```text
RETRIEVING → AWAITING_CONTEXT_APPROVAL → GENERATING
```

### 12.4 Claim Validation

```text
PENDING → SUPPORTED
        → UNSUPPORTED
        → CONTRADICTED
```

Claim `UNSUPPORTED` אינו מוצג כ־Fact.

## 13. API — מוסכמות כלליות

### 13.1 Base URL ו־Content Types

- Base: `/api/v1`.
- JSON כברירת מחדל.
- Upload באמצעות `multipart/form-data` רק ל־Evidence Bundle ו־Attachment.
- SSE ב־`text/event-stream`.

### 13.2 Authentication

- Web: Django server-side Session + Cookie אטום `HttpOnly`;‏ `Secure` ב־HTTPS;‏ `SameSite=Strict/Lax`; CSRF לכל פעולה משנה.
- אין Access/Refresh JWT ב־Web MVP. Session ניתנת לביטול בצד השרת ואינה חושפת Refresh credential ארוך־חיים.
- Login מסובב Session key. Idle timeout: 30 דקות; Absolute timeout: 12 שעות. Password/role change או user disable מבטלים Sessions.
- Password hashing: Argon2. Login throttling לפי Account+IP ו־Lockout זמני מדורג.
- Collector: Bearer token אקראי, Prefix+Hash, Workspace ו־Scopes, Expiration, Rotation ו־Revocation.
- Local mode: bind ל־`127.0.0.1` כברירת מחדל.

אם בעתיד נדרש Public API/SSO/Mobile: OIDC Authorization Code + PKCE, Access token קצר ו־Refresh rotation אצל Identity Provider. אין מימוש JWT ביתי.

### 13.3 Pagination

- Cursor pagination לרשימות Events/Evidence/Audit.
- Page number לרשימות קטנות ב־Admin.
- `page_size` ברירת מחדל 25, מקסימום 100.

### 13.4 Error envelope

```json
{
  "error": {
    "code": "INSUFFICIENT_EVIDENCE",
    "message": "Not enough evidence to start an investigation.",
    "details": {
      "missing": ["STACK_TRACE_OR_LOG", "REPOSITORY_SNAPSHOT"]
    },
    "request_id": "5f64d81d-78b9-4dd5-b43a-e79d22a1c9c5"
  }
}
```

### 13.5 Idempotency

Endpoints שמפעילים Job יקבלו `Idempotency-Key`:

- יצירת Snapshot.
- Upload Bundle.
- פתיחת Investigation.
- הרצת Evaluation.

המפתח יישמר עם actor, endpoint ו־response reference למשך זמן מוגדר.

## 14. API — Auth, Workspace ו־Sources

| Method | Endpoint | Scope | מטרה |
|---|---|---|---|
| `GET` | `/auth/csrf` | Public-local | קבלת CSRF cookie |
| `POST` | `/auth/login` | Public | התחברות |
| `POST` | `/auth/logout` | Authenticated | התנתקות |
| `GET` | `/auth/me` | Authenticated | משתמש, Organization ו־Workspaces |
| `GET` | `/auth/sessions` | Authenticated | Sessions פעילות של המשתמש |
| `DELETE` | `/auth/sessions/{id}` | Session owner | ביטול Session ספציפית |
| `POST` | `/auth/sessions/revoke-others` | Authenticated | ביטול כל Session אחרת |
| `POST` | `/auth/change-password` | Authenticated | שינוי סיסמה וביטול Sessions אחרות |
| `POST` | `/auth/password-reset/request` | Public | תשובה אחידה ללא User enumeration |
| `POST` | `/auth/password-reset/confirm` | Public | Token חד־פעמי קצר־חיים |
| `GET` | `/collector-tokens` | Owner | רשימת Tokens ללא Secret |
| `POST` | `/collector-tokens` | Owner | יצירת Token; Secret מוחזר פעם אחת |
| `POST` | `/collector-tokens/{id}/rotate` | Owner | Rotation וביטול הישן |
| `DELETE` | `/collector-tokens/{id}` | Owner | Revocation |
| `GET` | `/workspaces` | Member | רשימת Workspaces מורשים |
| `GET` | `/workspaces/{id}` | Member | פרטי Workspace ללא Host path |
| `PATCH` | `/workspaces/{id}` | Owner | Policy, AI mode ו־ignore rules |
| `GET` | `/workspaces/{id}/snapshots` | Member | רשימת Snapshots |
| `POST` | `/workspaces/{id}/snapshots` | Owner/Collector | יצירת Snapshot ל־ref שכבר נגיש ל־Collector |
| `GET` | `/workspaces/{id}/snapshots/{snapshot_id}` | Member | Scan status וסיכום |
| `POST` | `/workspaces/{id}/snapshots/{snapshot_id}/cancel` | Owner | ביטול Scan אם אפשר |
| `GET` | `/sources` | Member | מקורות לפי Workspace |
| `POST` | `/evidence-bundles` | Engineer | Upload Bundle |
| `GET` | `/evidence-bundles/{id}` | Member | Scan status/coverage |

אין Endpoint שמקבל Host path שרירותי. רישום Path נעשה דרך CLI/Management command מקומי:

```bash
incidentlens workspace register --name demo --path C:\projects\demo
```

אין Endpoint `/auth/refresh` ב־MVP. הדפדפן מחזיק Session ID אטום בלבד; הארכה מוגבלת מתבצעת בצד השרת לפי Idle/Absolute timeout. Collector token אינו מקבל Refresh Token — מבצעים Rotation מפורש ומבוקר.

### 14.1 Login

```http
POST /api/v1/auth/login
X-CSRFToken: <csrf-token>
```

```json
{
  "email": "owner@example.local",
  "password": "********"
}
```

Response `200` מחזיר User metadata בלבד; ה־Session Cookie נקבעת בכותרת `Set-Cookie` ואינה נגישה ל־JavaScript:

```json
{
  "user": {
    "id": "...",
    "email": "owner@example.local",
    "display_name": "Local Owner"
  },
  "session": {
    "idle_expires_at": "2026-08-13T13:00:00Z",
    "absolute_expires_at": "2026-08-14T00:30:00Z"
  }
}
```

שגיאת Login תמיד מחזירה `INVALID_CREDENTIALS`, ללא הבחנה בין משתמש לא קיים לסיסמה שגויה.

### 14.2 יצירת Collector token

```http
POST /api/v1/collector-tokens
```

```json
{
  "workspace_id": "...",
  "name": "local-docker-collector",
  "scopes": ["snapshot:create", "ingestion:write"],
  "expires_in_days": 30
}
```

ה־Response מחזיר `token` פעם אחת בלבד. לאחר מכן ניתן לראות רק `token_prefix`, Scopes, Expiration ו־Last used.

### 14.3 יצירת Snapshot

```http
POST /api/v1/workspaces/{workspace_id}/snapshots
Idempotency-Key: scan-demo-a17c92
```

```json
{
  "source_id": "c82bd45f-5c01-44f5-81a0-7a85ef0993d0",
  "git_ref": "a17c92",
  "service_ids": ["8b0bf31d-6068-4f3e-a648-b0a0e88aa61a"]
}
```

Response `202`:

```json
{
  "snapshot_id": "aa089def-90fa-401b-bb85-86e97b78d572",
  "job_id": "399177f1-a580-4ee4-8ca1-38817d1bba75",
  "status": "QUEUED"
}
```

## 15. API — Services ו־Dependencies

| Method | Endpoint | Scope | מטרה |
|---|---|---|---|
| `GET` | `/services` | Member | רשימה מסוננת לפי Workspace |
| `POST` | `/services` | Owner | יצירת Service |
| `GET` | `/services/{id}` | Member | פרטי Service |
| `PATCH` | `/services/{id}` | Owner | עדכון Metadata |
| `DELETE` | `/services/{id}` | Owner | Disable אם בשימוש |
| `GET` | `/service-dependencies` | Member | גרף תלות |
| `POST` | `/service-dependencies` | Owner | יצירת קשר |
| `DELETE` | `/service-dependencies/{id}` | Owner | סיום/מחיקת קשר |

## 16. API — Incidents ו־Evidence Readiness

| Method | Endpoint | Scope | מטרה |
|---|---|---|---|
| `GET` | `/incidents` | Member | רשימת Incidents |
| `POST` | `/incidents` | Engineer | פתיחת Incident/Draft |
| `GET` | `/incidents/{id}` | Member | Incident מלא |
| `PATCH` | `/incidents/{id}` | Engineer | עדכון לפני/במהלך חקירה |
| `POST` | `/incidents/{id}/attachments` | Engineer | Stack Trace/Log/Screenshot metadata |
| `DELETE` | `/incidents/{id}/attachments/{attachment_id}` | Engineer | לפני שימוש ב־Snapshot context |
| `POST` | `/incidents/{id}/readiness/evaluate` | Engineer | חישוב Readiness ללא LLM |
| `GET` | `/incidents/{id}/readiness` | Member | חישוב אחרון והיסטוריה קצרה |
| `GET` | `/incidents/{id}/timeline` | Member | Timeline מאוחד |
| `POST` | `/incidents/{id}/resolve` | Engineer | יצירת Resolution |
| `POST` | `/incidents/{id}/close` | Engineer | סגירה לאחר Resolution |

### 16.1 יצירת Incident

```json
{
  "workspace_id": "b2c0642a-b7cf-4d85-a02e-83509208e322",
  "snapshot_id": "aa089def-90fa-401b-bb85-86e97b78d572",
  "title": "Checkout returns 503 after auth deployment",
  "description": "Customers cannot complete checkout since approximately 14:06.",
  "severity": "SEV2",
  "environment": "staging",
  "started_at": "2026-08-13T11:06:00Z",
  "time_uncertainty_seconds": 600,
  "error_code": "AUTH_TOKEN_EXPIRED",
  "trace_id": "tr_2048",
  "service_ids": ["8b0bf31d-6068-4f3e-a648-b0a0e88aa61a"]
}
```

Response `201`:

```json
{
  "id": "6bb25dd0-012d-44bc-949d-5507b08ea39d",
  "status": "OPEN",
  "readiness_band": "UNKNOWN"
}
```

### 16.2 Readiness response

```json
{
  "band": "HIGH",
  "can_investigate": true,
  "scores": {
    "code_version": 100,
    "error_localization": 90,
    "runtime_evidence": 75,
    "provenance_diversity": 70
  },
  "available": [
    "READY_REPOSITORY_SNAPSHOT",
    "STACK_TRACE",
    "APPLICATION_LOG",
    "COMMIT_MATCH"
  ],
  "missing": ["DISTRIBUTED_TRACE"],
  "reason_codes": ["CODE_AND_RUNTIME_EVIDENCE_PRESENT"]
}
```

## 17. API — Search ו־Evidence

| Method | Endpoint | Scope | מטרה |
|---|---|---|---|
| `POST` | `/search` | Engineer | Hybrid search עצמאי |
| `GET` | `/evidence/{id}` | Member+Policy | Evidence ו־Provenance |
| `GET` | `/evidence/{id}/context` | Member+Policy | שורות/אירועים מסביב בגבול מוגבל |
| `GET` | `/symbols/{id}` | Member | Symbol ויחסים |
| `GET` | `/symbols/{id}/relations` | Member | callers/callees/tests |
| `GET` | `/snapshots/{id}/diff` | Member | Diff מסונן מול parent |

### 17.1 Search request

```json
{
  "workspace_id": "b2c0642a-b7cf-4d85-a02e-83509208e322",
  "snapshot_id": "aa089def-90fa-401b-bb85-86e97b78d572",
  "query": "expired token is not refreshed",
  "environment": "staging",
  "time_range": {
    "from": "2026-08-13T10:00:00Z",
    "to": "2026-08-13T12:30:00Z"
  },
  "channels": ["EXACT", "FTS", "VECTOR", "TEMPORAL", "STRUCTURAL"],
  "limit": 20
}
```

Response כולל לכל Result:

```json
{
  "evidence_id": "...",
  "title": "validate_token",
  "source": {
    "type": "CODE",
    "file": "auth_service/token_validator.py",
    "lines": [61, 103],
    "commit": "a17c92..."
  },
  "scores": {
    "exact": 1.0,
    "fts": 0.73,
    "vector": 0.88,
    "structural": 0.95,
    "rrf": 0.061
  },
  "selection_reasons": ["STACK_FRAME_MATCH", "CHANGED_IN_DEPLOYED_COMMIT"]
}
```

## 18. API — Investigations

| Method | Endpoint | Scope | מטרה |
|---|---|---|---|
| `POST` | `/incidents/{id}/investigations` | Engineer | פתיחת Run |
| `GET` | `/investigations/{id}` | Member | Status/Result |
| `POST` | `/investigations/{id}/cancel` | Requester/Owner | ביטול best-effort |
| `GET` | `/investigations/{id}/events` | Member | SSE progress |
| `GET` | `/investigations/{id}/steps` | Member | Trace טכני מסונן |
| `GET` | `/investigations/{id}/context-preview` | Engineer | EvidenceSet לפני External AI |
| `POST` | `/investigations/{id}/context-approval` | Owner/Policy | אישור/דחייה |
| `GET` | `/investigations/{id}/hypotheses` | Member | Hypotheses/Claims/Citations |
| `POST` | `/investigations/{id}/questions` | Engineer | Follow-up עם Retrieval חדש |

### 18.1 פתיחת Investigation

```json
{
  "ai_mode": "LOCAL",
  "max_subquestions": 4,
  "max_sufficiency_iterations": 2
}
```

Response `202`:

```json
{
  "investigation_id": "129f53da-59c4-4652-90f1-d651aa14ade9",
  "status": "QUEUED",
  "events_url": "/api/v1/investigations/129f53da-59c4-4652-90f1-d651aa14ade9/events"
}
```

אם Readiness אינו מאפשר חקירה: `409 INSUFFICIENT_EVIDENCE` עם רשימת מידע חסר.

### 18.2 SSE events

```text
event: progress
data: {"stage":"RETRIEVING","percent":35,"message_code":"SEARCHING_CODE_AND_LOGS"}

event: awaiting_approval
data: {"context_snapshot_id":"...","estimated_tokens":3120}

event: completed
data: {"result_state":"PROBABLE"}
```

SSE אינו מקור האמת. Reconnect משתמש `Last-Event-ID` או נופל ל־GET `/investigations/{id}`.

## 19. API — Hypotheses, Recommendations ו־Resolution

| Method | Endpoint | Scope | מטרה |
|---|---|---|---|
| `POST` | `/hypotheses/{id}/feedback` | Engineer | Accept/Reject + note |
| `PATCH` | `/recommendations/{id}` | Engineer | עדכון סטטוס ותוצאה |
| `GET` | `/incidents/{id}/resolution` | Member | Root Cause אנושי |
| `POST` | `/incidents/{id}/resolve` | Engineer | יצירת Resolution |
| `GET` | `/incidents/{id}/report` | Member | Markdown report |

אין Endpoint ל־Execute, Patch repository, Commit, Push, Restart או Rollback ב־MVP.

## 20. API — Evaluation, Privacy ו־Operations

| Method | Endpoint | Scope | מטרה |
|---|---|---|---|
| `GET` | `/evaluation-cases` | Owner | Golden cases |
| `POST` | `/evaluations` | Owner | הרצת Evaluation |
| `GET` | `/evaluations/{id}` | Member | Status ומדדים |
| `GET` | `/evaluations/{id}/results` | Member | Per-case results |
| `GET` | `/evaluations/compare?base=&candidate=` | Member | השוואת גרסאות |
| `GET` | `/workspaces/{id}/privacy` | Owner | Policies וסטטיסטיקות |
| `GET` | `/workspaces/{id}/redactions` | Owner | Findings ללא values |
| `POST` | `/workspaces/{id}/purge` | Owner | מחיקה מבוקרת |
| `GET` | `/audit-events` | Owner | Audit מסונן |
| `GET` | `/health` | Public-local | Liveness |
| `GET` | `/readiness` | Public-local | DB/Redis/storage readiness |

## 21. שכבות קוד וגבולות אחריות

```text
DRF View / ViewSet
    ↓ HTTP, auth, permission, serializer
Application Service
    ↓ use-case + transaction boundaries
Domain Policy / Selector / Repository Port
    ↓
Django ORM Adapter / Storage Adapter / rag_core Port
    ↓
PostgreSQL / MinIO / Celery / AI Provider
```

### 21.1 DRF

- Parsing ו־Validation של Request.
- Authentication, Permission ו־Throttle.
- החזרת HTTP status ו־Serializer output.
- לא מריץ RAG ולא מכיל לוגיקה עסקית מורכבת.

### 21.2 Application Services

- `WorkspaceService`
- `SnapshotService`
- `IncidentService`
- `ReadinessService`
- `InvestigationService`
- `ContextApprovalService`
- `ResolutionService`
- `EvaluationService`

ה־Service מגדיר Transaction boundary ומשתמש ב־`transaction.on_commit()` לשליחת Celery task.

### 21.3 `code_intelligence`

- Safe file scanner.
- Python AST parser.
- Stack Trace parser.
- Git read-only adapter.
- Symbol graph builder.
- ללא תלות ב־Django.

### 21.4 `rag_core`

- Query planning.
- Retrieval ports.
- RRF ו־Reranking.
- Context selection ו־Sufficiency.
- Hypothesis generation schemas.
- Citation validation.
- ללא גישה ישירה ל־HTTP או ל־Django ORM.

## 22. Background Jobs

| Task | קלט | פלט עסקי |
|---|---|---|
| `scan_repository_snapshot` | snapshot_id | CodeFiles, Symbols, Relations, Evidence, Redactions |
| `ingest_evidence_bundle` | bundle_id | Sources, Attachments, Evidence |
| `build_embeddings` | embedding_index_id + evidence IDs | EvidenceEmbeddings |
| `evaluate_incident_readiness` | incident_id | ReadinessAssessment |
| `run_investigation` | investigation_run_id | Steps, Retrieval, Context, Hypotheses |
| `run_evaluation` | evaluation_run_id | EvaluationResults |
| `purge_workspace` | workspace_id | מחיקה מדורגת + Audit |

כל Task:

- Idempotent ככל האפשר.
- מקבל IDs בלבד, לא ORM objects.
- טוען State מחדש בתוך ה־Worker.
- מעדכן Status לפני ואחרי שלבים.
- אינו כותב Secrets ללוגים.
- משתמש ב־Retry רק עבור כשלים זמניים; Parser error קבוע אינו Retry אינסופי.

## 23. סדר Migrations

### Migration 0001 — Identity ו־Web Sessions

`organizations`, custom `users`, `organization_memberships`, `user_sessions` והגדרת Argon2/session policies.

### Migration 0002 — Workspace ו־Services

`workspaces`, `workspace_memberships`, `services`, `service_dependencies`.

### Migration 0003 — Sources ו־Snapshots

`sources`, `repository_snapshots`, `ingestion_jobs`, `collector_api_tokens`, ולאחר מכן FK `workspaces.active_snapshot_id`.

### Migration 0004 — Evidence ו־Code Intelligence

`code_files`, `evidence_items`, `code_symbols`, `symbol_relations`, `code_changes`, `redaction_findings`.

### Migration 0005 — Incidents

`incidents`, `incident_services`, `incident_attachments`, `readiness_assessments`.

### Migration 0006 — Documents ו־Runtime

`source_documents`, `document_chunks`, `evidence_bundles`, `log_events`, `trace_spans`, `deployments`.

### Migration 0007 — Embeddings ו־Retrieval

`embedding_indexes`, `evidence_embeddings`, GIN/HNSW indexes, `retrieval_queries`, `retrieval_results`.

### Migration 0008 — Investigation

`investigation_runs`, `investigation_steps`, `context_snapshots`, `context_snapshot_items`, `hypotheses`, `claims`, `claim_evidence`, `recommendations`, `external_ai_approvals`.

### Migration 0009 — Resolution ו־Evaluation

`resolutions`, `evaluation_cases`, `evaluation_runs`, `evaluation_results`.

### Migration 0010 — Audit indexes ו־Hardening

`audit_events`, partial indexes, Check constraints ו־performance indexes שנבדקו.

## 24. מה בונים בפועל בהתחלה

לא מיישמים את כל הטבלאות יחד. סדר ה־Vertical Slice:

1. `organizations`, `users`, `organization_memberships`, `user_sessions` ומסלול Login/Logout מאובטח.
2. `workspaces`, `services`, `sources`, `repository_snapshots`, `ingestion_jobs`.
3. `code_files`, `evidence_items`, `code_symbols`, `symbol_relations`, `code_changes`, `redaction_findings`.
4. `incidents`, `incident_services`, `incident_attachments`, `readiness_assessments`.
5. Endpoints של Workspace, Snapshot, Incident, Attachment, Readiness, Symbol ו־Diff.
6. רק לאחר שהמסלול עובד: Embeddings, `/search`, Investigation ו־LLM.

### Definition of Done ל־Data/API Slice הראשון

- ניתן לרשום Workspace מקומית בלי לשלוח Host path מהדפדפן.
- ניתן ליצור Snapshot ל־Commit מאושר.
- Scanner מסנן `.env` ומפתחות ושומר Finding ללא ערך סודי.
- AST parser שומר File, Symbol ו־Relations.
- Stack Trace attachment מתקשר לקובץ ול־Symbol.
- Git Diff נשמר כ־Evidence מסונן.
- Readiness מחזיר Band ו־Reason codes ללא LLM.
- כל Endpoint מוגן ב־Workspace scope.
- כל Response שגיאה כולל `request_id` ו־error code יציב.
- קיימות Unit tests, Integration tests ו־Migration check.

## 25. החלטות שלא משאירים פתוחות לתחילת המימוש

- Custom User נוצר לפני Migration ראשון.
- Local-first ו־localhost-only הם ברירת מחדל.
- Python היא שפת הקוד היחידה הנתמכת ב־MVP הראשוני.
- Repository הוא Read-only ואין Code execution.
- Snapshot מצביע ל־Commit מלא, לא ל־Branch משתנה.
- EvidenceItem הוא בסיס ה־Retrieval וה־Citation.
- Readiness הוא דטרמיניסטי ונפרד מ־Confidence.
- אין Generic endpoint לקריאת קובץ לפי path.
- אין ריפוד Embeddings בין ממדים שונים.
- אין External AI ללא Policy ו־Context approval.
- אין שינוי Repository או פעולת Production דרך API.
