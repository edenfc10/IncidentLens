# IncidentLens — מסמך אפיון

> גרסת תיק עבודות (Portfolio), מהדורה משופרת לאחר חידוד מודל הקלט, האבטחה ותפקיד ה-RAG. מטרת המסמך: לתכנן ולתעד מערכת AI-assisted incident investigation שמדגימה יכולת הנדסית מלאה — ניתוח קוד וראיות Runtime, RAG מבוסס מקורות, פרטיות Local-first, אמינות מדידה ו-Evaluation — ולא רק "עוד RAG demo".

## 1. תקציר ומטרת המערכת

IncidentLens היא סביבת חקירת תקלות מקומית כברירת מחדל (Local-first), שמחברת בין גרסת הקוד שרצה בזמן האירוע לבין הראיות שנוצרו ב-Runtime. במקום שמהנדס יעבור ידנית בין Repository, Stack Trace, Logs, Traces, Deployments, Tests ו-Runbooks, המערכת מרכזת את החומרים, בודקת אם יש מספיק מידע לחקירה, מבצעת Code-aware RAG ומייצרת מספר השערות מנומקות עם ציטוטים לראיות אמיתיות.

המערכת אינה מבטיחה לפתור כל תקלה ואינה מציגה השערה כעובדה. ההבטחה המוצרית היא להגיע למסקנה הטובה ביותר שהראיות מאפשרות, להסביר כיצד התקבלה, ולהציג בדיוק איזה מידע חסר כאשר אי אפשר לקבוע Root Cause.

למערכת שני מסלולי קלט:

1. **Local Repository Mode — המסלול המומלץ:** המשתמש מחבר Repository מקומי כ-Read-only, בוחר Commit/Tag/Branch ומצרף Stack Trace, Logs ופרטי Deployment. הקוד והאינדקס נשארים מקומיים.
2. **Evidence Bundle Mode — מסלול פרטיות חלופי:** המשתמש אינו חושף Repository שלם, אלא מעלה חבילה מצומצמת הכוללת Stack Trace, Logs, קבצי מקור רלוונטיים, Dependency manifest ו-Deployment metadata. המערכת מציגה שהכיסוי מוגבל יותר.

צילום מסך הוא קלט משלים בלבד. ניתן לחלץ ממנו Error code, זמן או Request ID, אך אין להשתמש בו לבדו כדי לקבוע Root Cause.

המערכת בנויה סביב שישה עקרונות ליבה:

1. **אין תשובה בלי ראיה** — כל טענה מהותית חייבת Citation למקור שנכלל בפועל בהקשר החקירה.
2. **ריבוי השערות, לא החלטה יחידה** — המערכת מציגה כמה הסברים אפשריים, ראיות תומכות וסותרות ומידע חסר.
3. **Readiness לפני Generation** — לפני הפעלת מודל נבדק אם קיימים Code version, Error artifact ו-Runtime evidence מספיקים. אם לא, המערכת מבקשת מידע ממוקד.
4. **שלוש רמות תוצאה** — `VERIFIED`, `PROBABLE` או `INSUFFICIENT_EVIDENCE`. רק שחזור מבוקר או ראיה ישירה מאפשרים `VERIFIED`.
5. **פרטיות כברירת מחדל** — Repository, Embeddings ו-Artifacts נשמרים מקומית; קוד אינו נשלח במלואו למודל חיצוני.
6. **הרשאות לפני Retrieval** — תוכן שאינו מורשה או אינו מאושר לסריקה לא נכנס לאינדקס הפעיל, לא מוחזר בחיפוש ולא נשלח ל-LLM.

תפקיד ה-RAG מוגדר היטב: רכיבי Parsing וניתוח קוד מייצרים Evidence מובנה; מנוע ה-RAG בוחר מתוך הקוד והראיות את החלקים הרלוונטיים; ה-LLM מחבר אותם להשערות; שכבת Validation בודקת Provenance, הרשאות וציטוטים. ה-RAG אינו מחליף AST analysis, Git analysis, Secret scanning או שחזור תקלה.

## 2. תרחישי שימוש לדוגמה

**חקירת Regression ברמת קוד:** המשתמש מחבר Repository מקומי ב-Commit `a17c92`, מצרף Stack Trace שמצביע על `token_validator.py:87` ולוגים מטווח האירוע. המערכת מוצאת את `validate_token`, מרחיבה לפונקציה `refresh_token`, משווה ל-Commit הקודם ומזהה שהקריאה לחידוש טוקן הוחלפה ב-Exception. התוצאה מסומנת `PROBABLE`, משום שהקוד והלוגים תומכים בהשערה אך התקלה טרם שוחזרה.

**חקירת Deployment עם Telemetry:** לאחר Deployment של `auth-service`, משתמשים מקבלים `503` ב-Checkout. המערכת מקשרת Trace בין Checkout, Payment ו-Auth, מאתרת `AUTH_TOKEN_EXPIRED`, מתאימה את ה-Deployment ל-Commit הנכון ומוצאת שינוי ב-`AUTH_REFRESH_TTL`. Runbook ו-Incident קודם מחזקים את ההשערה לכשל בחידוש טוקנים.

**Evidence Bundle ללא Repository מלא:** משתמש שחושש לחשוף קוד מעלה Stack Trace, עשרה קבצי מקור רלוונטיים, Log ו-Dependency manifest. המערכת מנתחת רק את החבילה, מסמנת שה-call graph חלקי ומונעת הצגת Confidence גבוה אם חסרים callers או configuration references.

**צילום מסך בלבד:** המשתמש מעלה צילום של שגיאת `500`. OCR מחלץ Request ID, אך אין Logs או גרסת קוד. המערכת מחזירה `INSUFFICIENT_EVIDENCE` ומבקשת Stack Trace או Logs ו-Commit/Version; היא אינה מייצרת רשימת פתרונות כללית כאילו מדובר באבחון.

**מקרה של מידע חסר:** קיימת עלייה ב-Timeouts, אך אין Trace, Metrics או נתוני Dependency. המערכת מציגה Hypotheses ברמת ביטחון נמוכה ורשימת איסוף ממוקדת: health של השירות התלוי, span מהקריאה החיצונית וטווח זמן מדויק.

**תרחיש אבטחה:** Repository כולל `.env`, מפתח פרטי ו-Log עם Authorization header. קבצים חסומים באמצעות Allowlist, `.gitignore` ו-`.incidentlensignore`; Secret scanner מסיר ערכים רגישים; מסך Context Preview מציג למשתמש מה יישלח למודל החיצוני לפני אישור.

**תרחיש גרסה שגויה:** Stack Trace מתייחס לגרסה `2.4.1`, אך המשתמש בחר `main`. המערכת מזהה אי-התאמה בין Build metadata ל-Commit ומונעת אבחון ברמת Confidence גבוהה עד לבחירת ה-Commit הנכון.

**תרחיש Evaluation:** מפתח משנה Chunking ברמת Symbol או Reranker ומריץ Golden Dataset. המערכת משווה File/Function localization, Retrieval Recall, Root Cause Accuracy, Citation Correctness, Secret leakage, Latency ועלות מול Baseline.

## 3. דרישות פונקציונליות

### 3.1 ניהול שירותים ותלויות

קטלוג שירותים, Owners, Repositories, Environments וקשרים מכוונים בין שירותים (`ServiceDependency`). הקטלוג משמש להרחבת חיפוש ב-1–2 hops מהשירות החשוד ולמיפוי Trace בין רכיבים.

ב-MVP ייטען קטלוג סינתטי של מערכת הדמו. חיבור אוטומטי ל-Service catalog ארגוני אינו נדרש. כל Service ישמור Runtime name, נתיב Repository מקומי או Evidence Bundle, שפת קוד, Default branch ו-Deployment identifier convention.

### 3.2 ניהול מקורות מידע

רישום ומעקב אחר מקורות מסוג Local Repository, Evidence Bundle, Stack Trace, Logs, Traces, Deployments, Code Changes, Tests, Runbooks ו-Postmortems.

מקור Repository יירשם באמצעות Collector מקומי או mount לקריאה בלבד; ממשק Web אינו מקבל גישה שרירותית למערכת הקבצים. המשתמש מפעיל פקודה מקומית או מגדיר path מפורש ב-Docker Compose, ולאחר מכן בוחר Workspace שכבר אושר.

לכל מקור נשמרים Scope, סטטוס, גרסה, Checksum, זמן אינדוקס, מדיניות Retention, רמת רגישות, ומצב `LOCAL_ONLY` או `EXTERNAL_AI_ALLOWED`. מקור שנחסם או נמחק יוצא מיד מ-Retrieval ומטופל במחיקה אסינכרונית בהתאם למדיניות.

### 3.3 Ingestion ואינדוקס

תהליך הקליטה:

```text
Source registration
→ Path and type validation
→ Ignore/allowlist rules
→ Checksum and version resolution
→ Secret/PII scan
→ Parsing and normalization
→ Code-aware chunking
→ EvidenceItem creation
→ Embeddings for eligible content
→ Indexing and readiness update
```

**Repository safety:** ה-Repository מחובר לקריאה בלבד. ב-MVP אין התקנת Dependencies, הרצת Hooks, הרצת Tests או ביצוע קוד מה-Repository. ה-Scanner פועל ברשת מבודדת ללא Egress ואינו טוען מודולים באמצעות import דינמי.

**קבצים מותרים:** ברירת המחדל היא Allowlist לשפות ולקבצי Manifest נתמכים. המערכת מכבדת `.gitignore` ו-`.incidentlensignore`, וחוסמת `.env`, private keys, credentials, binaries, archives, `node_modules`, `vendor`, build output ו-generated files אלא אם הוגדר חריג מפורש.

**Code-aware parsing:** ב-MVP התמיכה המלאה היא ב-Python באמצעות AST סטטי. החלוקה מתבצעת לפי Module, Class, Function, Method, Exception handler, Route ו-Test; כל Chunk שומר path, שורות, symbol, imports, callers/callees בסיסיים, Commit ו-Service. TypeScript יתווסף לאחר השלמת Pipeline מדיד ל-Python.

**Stack Trace parsing:** המערכת מחלצת שפה, קובץ, שורה, symbol, exception type ו-message. Frames פנימיים מקבלים עדיפות; Frames של ספריות צד שלישי משמשים Context בלבד אלא אם מקורן נכלל ב-Workspace.

**Logs:** לא כל שורת Log מקבלת Embedding. Logs נשמרים ומחופשים בעיקר באמצעות Exact/FTS/Temporal/Trace ID; Embeddings נוצרים רק לתבניות שגיאה, Stack Traces, clusters מסוכמים או אירועים שסומנו כמשמעותיים, כדי למנוע עלות ורעש.

**EvidenceItem:** שכבת קריאה מנורמלת שנבנית בזמן Ingestion. היא מחזיקה `source_type`, `source_id`, `text`, `timestamp`, `service_id`, `trace_id`, `file_path`, `symbol`, `line_start`, `line_end`, `commit_sha`, `sensitivity`, `organization_id`, `environment`, `content_hash` ו-Provenance. זהו הבסיס ל-Retrieval ול-Citation Validation.

**Embeddings:** ב-MVP מוגדר מודל Embedding פעיל יחיד לכל Workspace וסכמת Vector בממד קבוע. החלפת מודל יוצרת Index version חדש ומפעילה Re-embedding מבוקר. לא משתמשים בריפוד אפסים בין מודלים בעלי ממדים שונים, משום שהדבר מסבך אינדוקס וחישוב דמיון ועלול לפגוע בנכונות. תמיכה בכמה מודלים במקביל תיעשה בעתיד באמצעות טבלה/עמודה ואינדקס נפרדים לכל משפחת ממדים.

התהליך אידמפוטנטי: `(source_version, content_hash, parser_version)` מונעים יצירת כפילויות. כשל חלקי נשמר כ-Job failure עם Retry מוגבל ו-Dead Letter state.

### 3.4 פתיחת Incident

Incident כולל כותרת, תיאור סימפטום, חומרה, סביבה, טווח זמן, שירותים חשודים, Error codes, Request/Trace ID, Runtime version, Commit/Tag/Branch, Stack Trace וקבצים מצורפים.

המערכת אינה מחייבת את המשתמש לדעת את Root Cause. היא כן דורשת מינימום לחקירה:

- תיאור סימפטום, Environment וטווח זמן או זמן משוער.
- מקור קוד מזוהה: Repository+Commit או Evidence Bundle.
- לפחות Error artifact אחד: Stack Trace, Log, Trace ID, Request ID או Error code ייחודי.

צילום מסך יכול לשמש לחילוץ מזהה או הודעה, אך אינו מקיים לבדו את דרישת ה-Evidence.

לפני יצירת InvestigationRun, המערכת מפיקה `Evidence Readiness` נפרד מ-Confidence:

- `HIGH`: קיימים Code version, Stack Trace/Trace ו-Runtime evidence מספיקים ל-Code-level diagnosis.
- `MEDIUM`: ניתן ליצור השערות אך חסרים נתוני Runtime, Configuration או Version certainty.
- `LOW`: אין מספיק חומר להפעלת Generation; המשתמש מקבל רשימת דרישות ממוקדת.

### 3.5 בניית Timeline

Timeline מאחד Deployments, Code Changes, Error Logs, Failed Spans, Audit Events והתחלת השפעה עסקית. הוא נבנה באמצעות UNION query/View ולא כטבלת אירועים כפולה.

כל אירוע כולל Provenance ו-Time certainty. אירוע ללא Timestamp אמין מסומן `TIME_UNKNOWN` ואינו משמש לחישוב Temporal correlation. קרבה בזמן מוצגת כקורלציה ולא כהוכחת סיבתיות.

`business_impact_started_at` נשמר על Incident. אם אין נתון מדויק, נשמר טווח משוער ולא זמן מומצא.

### 3.6 חיפוש היברידי

ה-Retrieval משלב ערוצים משלימים:

1. **Exact Match:** Error code, Exception, file path, symbol, Trace/Request ID, Commit SHA ו-Version.
2. **PostgreSQL Full-Text Search:** הודעות שגיאה, תיעוד, Runbooks ו-Code identifiers.
3. **Vector Search:** דמיון סמנטי בין תיאור התקלה לבין Functions, Tests, Error templates, Runbooks ו-Incidents קודמים.
4. **Temporal Search:** אירועים בטווח ה-Incident עם decay לפי מרחק מהאירוע.
5. **Structural Expansion:** הרחבה מתוך Stack Frame ל-Symbol, callers/callees, Tests, Config references ו-Code Changes. זהו רכיב Code-aware שאינו מבוסס Embedding בלבד.

כל ערוץ מחזיר top-N מוגבל; התוצאות מאוחדות באמצעות RRF עם פרמטרים הניתנים לכיול ב-Evaluation. אין להציג `k=60` כערך נכון אוניברסלית — הוא Baseline בלבד.

לאחר מכן מתבצעים Deduplication לפי Provenance/content hash, Diversity selection כדי למנוע עשרה Chunks מאותו קובץ, ו-Reranking מקומי. Cross-encoder הוא Provider אופציונלי; אם הוא אינו זמין, קיימת אסטרטגיית דירוג דטרמיניסטית המבוססת Exact/Structural/Temporal scores.

HNSW הוא ברירת המחדל ל-pgvector עבור Dataset הדמו. כל שאילתת ANN כוללת מראש Workspace/Organization, Source status, Sensitivity, Environment ו-Commit scope. אם Pre-filter מצמצם Recall, יש למדוד זאת מול Exact search ולא להסיר את ההרשאות.

פלט ה-Retrieval הוא `EvidenceSet` מוגבל בתקציב Context, ולא טקסט חופשי. כל פריט כולל ID, Source, Span מדויק, Score components וסיבה לבחירה.

### 3.7 חקירה רב-שלבית

זרימת החקירה:

```text
INTAKE_VALIDATION
→ EVIDENCE_READINESS
→ QUERY_AND_CODE_PLANNING
→ RETRIEVAL (מקבילי לערוצים)
→ STRUCTURAL_EXPANSION
→ RERANKING_AND_CONTEXT_SELECTION
→ SUFFICIENCY_CHECK
→ HYPOTHESIS_GENERATION
→ CITATION_AND_POLICY_VALIDATION
→ VERIFIED / PROBABLE / INSUFFICIENT_EVIDENCE
```

ה-Planning משתמש תחילה בנתונים דטרמיניסטיים: Stack Frames, Service, Commit, Error codes וטווח זמן. ה-LLM יכול להציע תת-שאלות, אך אינו רשאי להרחיב Scope לנתיב או מקור שלא אושר.

תקציבי ברירת מחדל:

- עד 6 תת-שאלות.
- עד 2 איטרציות Sufficiency.
- עד 2 hops ב-ServiceDependency וב-Symbol graph.
- תקרת זמן, Context, Tokens ועלות לכל InvestigationRun.
- עצירה מיידית בחריגה מ-Scope, הרשאה או תקציב.

Retrieval לערוצים שונים רץ במקביל; Hypotheses נוצרות בקריאת Generation אחת עם Structured Output. פעולות DB/ORM סינכרוניות אינן מורצות ישירות בתוך Event loop ללא Adapter מתאים.

Progress מועבר באמצעות SSE. אם Proxy או סביבת Hosting אינם תומכים ב-Streaming אמין, ה-Frontend נופל ל-Polling על סטטוס שמור ב-PostgreSQL. Celery task אינו תלוי בחיבור SSE פתוח.

**Sufficiency:** הבדיקה מחושבת לפי כיסוי מינימלי של Code version, Error localization, Runtime evidence ו-Provenance diversity. LLM יכול לתאר מידע חסר, אך החלטת עצירה אינה נשענת רק על self-assessment שלו.

### 3.8 יצירת השערות

המודל מחזיר עד שלוש Hypotheses במבנה Pydantic מחייב. לכל Hypothesis:

- הסבר קצר.
- טענות אטומיות.
- Evidence IDs תומכים וסותרים.
- מידע חסר.
- פעולות אימות בטוחות.
- Scope: file, symbol, service, config או dependency.
- Result state מוצע, שאינו מאושר אוטומטית.

Confidence אינו אחוז שה-LLM ממציא. Confidence Band מחושב בקוד לפי משקל מקורות, Directness, Version match, Temporal proximity, Structural match, contradictions ו-Missing critical evidence.

רמות התוצאה:

- `VERIFIED`: ראיה ישירה חד-משמעית או שחזור מבוקר שנשמר כתוצאת Verification. ב-MVP, ללא Sandbox כללי, מצב זה מתקבל רק בתרחישי הדמו שבהם Verification harness מוגדר מראש.
- `PROBABLE`: מספר ראיות בלתי תלויות תומכות בהשערה, אך אין שחזור או הוכחה ישירה.
- `INSUFFICIENT_EVIDENCE`: החומר אינו מאפשר מסקנה אחראית. המערכת מציגה מה לאסוף, ללא Padding של תשובה כללית.

### 3.9 Citation Validation

הבדיקה מחולקת לשתי שכבות כדי לא לטעון ליכולת דטרמיניסטית שאינה קיימת:

1. **Referential validation — דטרמיניסטי:** Evidence ID קיים, היה חלק מה-Context שנשלח, שייך לגרסה ול-Workspace הנכונים, נגיש למשתמש, ומצביע ל-span מדויק במקור.
2. **Support validation — משולב:** כללי התאמה עבור File/Line/Symbol/Error code ו-NLI/Reranker אופציונלי לבדיקת תמיכה סמנטית. טענה שלא ניתן לאמת מסומנת `UNSUPPORTED` או `INFERENCE`, ולא מוצגת כעובדה.

ה-LLM אינו מאשר את עצמו. Claims נשמרים כישויות או JSON structured records, וכל Claim מהותי חייב לפחות Citation אחד. Citation למקור שלא נכלל ב-Snapshot מבטל את הטענה.

### 3.10 המלצות לפעולות

המערכת מציעה פעולות בדיקה בלבד:

- פתיחת File/Symbol חשוד.
- השוואת Commit לגרסה הקודמת.
- בדיקת Environment Variable ללא הצגת ערכו הרגיש.
- הרצת Test שהמשתמש בוחר מחוץ ל-IncidentLens.
- איסוף Trace/Metric חסר.
- שחזור Request בסביבת בדיקה.

ב-MVP אין Code execution, dependency installation, Restart, Rollback, Push, Pull Request או Production action. המשתמש יכול לסמן Recommendation כ-Planned/Performed/Succeeded/Failed ולצרף תוצאה ידנית.

Sandbox להרצת Tests הוא Roadmap נפרד, עם Isolation, Egress deny, CPU/Memory/time limits ו-Ephemeral filesystem; הוא אינו תנאי להשלמת גרסת Portfolio.

### 3.11 שאלות המשך

שאלת המשך מקבלת את Snapshot החקירה אך מפעילה Retrieval חדש, עם אותו Workspace, Commit, Environment והרשאות. המערכת אינה מסתמכת רק על Chat history.

אם המשתמש משנה Commit, מצרף Log חדש או מרחיב זמן, נוצרת Revision חדשה של Investigation context כדי לשמור Reproducibility.

שאלה המבקשת פעולה אסורה, כגון "בצע Rollback", מוחזרת כהמלצה בלבד ולא מתורגמת ל-Tool execution.

### 3.12 פתרון וסגירת Incident

בעת סגירה נשמרים Root Cause מאומת על ידי המשתמש, שירות ורכיב אחראים, Commit/Config קשורים, פעולת פתרון, זמן פתרון, Verification method והערות.

המערכת מפרידה בין `system_hypothesis` לבין `human_verified_root_cause`. אישור אנושי אינו משנה היסטוריית פלט אלא מוסיף Resolution record.

Incident סגור יכול להפוך למקור היסטורי ולמועמד ל-Golden Dataset רק לאחר Review והסרת מידע רגיש.

### 3.13 משוב

המשתמש יכול לאשר או לדחות Hypothesis, לסמן Evidence כרלוונטי/לא רלוונטי, להעריך Recommendation ולציין מה היה חסר.

המשוב משמש ל-Evaluation ולכיול Ranking בלבד. אין Online learning אוטומטי, אין שינוי Prompt ללא Versioning ואין שינוי משקל מקור ללא Baseline comparison.

### 3.14 Evaluation

Evaluation הוא רכיב ליבה ומסך דגל של הפרויקט.

**Golden Dataset:** מערכת Microservices סינתטית עם תרחישים מבוימים ו-Ground Truth: שירות, Root Cause, Commit, Symbol, Required Evidence ו-Expected result state.

התרחישים כוללים:

- Regression עם Stack Trace וקובץ נכון.
- Configuration mismatch.
- Dependency failure שמופיע כסימפטום בשירות אחר.
- Wrong-commit mismatch.
- Missing evidence שמחייב Abstention.
- Prompt injection בתוך Runbook או Log.
- Secret בתוך קובץ/Log שחייב לעבור Redaction.
- Evidence Bundle חלקי.

**מדדים:**

- File Localization Accuracy.
- Symbol Localization Accuracy.
- Retrieval Recall@k ו-MRR.
- Required Evidence Coverage.
- Root Cause exact/partial Accuracy.
- Result-state correctness (`VERIFIED/PROBABLE/INSUFFICIENT`).
- Citation referential correctness.
- Claim support rate ו-Unsupported Claims rate.
- Secret leakage count — יעד אפס בסט הבדיקה.
- Abstention quality כאשר חסר מידע.
- Latency p50/p95, Tokens ועלות.

כל EvaluationRun שומר Dataset version, Parser version, Index version, Embedding, Reranker, Prompt, LLM ו-Configuration. שינוי אינו נחשב שיפור אם הוא מעלה Accuracy אך פוגע באבטחה, Abstention או Latency מעבר לתקרה.

### 3.15 ממשק ניהול

Django Admin משמש לניהול Workspaces/Organizations, משתמשים, Services, Sources, Parser/Index versions, Evaluation cases, Jobs שנכשלו ו-Retention.

בגרסת Local-first קיימת Organization אחת כברירת מחדל ומשתמש מקומי. מודלי Organization/RBAC נשמרים כדי להדגים Boundary נכון ולאפשר Self-hosted team mode, אך Multi-tenant SaaS אינו חלק מה-MVP.

Admin אינו מציג Secrets גולמיים, Context מלא שנשלח למודל או ערכי Environment רגישים. פעולות Re-index/Delete מחייבות אישור ומתועדות ב-Audit.

## 4. דרישות לא פונקציונליות

### 4.1 ביצועים

- יעד ה-MVP המקומי: משתמש יחיד ועד 5 חקירות פעילות/ממתינות, ולא הבטחת 100 משתמשים שאינה רלוונטית ל-Portfolio Local-first.
- יעד Self-hosted עתידי: 100 משתמשים פעילים, רק לאחר Load test ו-Scale-out ל-Web/Workers.
- טעינת מסכים מרכזיים מתחת ל-2 שניות על Dataset הדמו; מידע כבד נטען בהדרגה.
- p95 נמוך מ-300ms ל-CRUD מקומי רגיל שאינו מפעיל AI.
- p95 נמוך מ-2 שניות ל-Hybrid Retrieval על Golden Dataset בגודל המוצהר, לא כולל Reranker חיצוני.
- יעד חקירה p95 של 30 שניות הוא יעד Stretch ותלוי בחומרה ובספק. יעד הקבלה ל-MVP: 90% מחקירות הדמו מסתיימות בתוך 60 שניות, עם Progress ושמירת תוצאה גם אם הלקוח התנתק.
- Repository בגודל יעד: עד 100,000 שורות קוד Python לאחר סינון. Repository גדול יותר דורש Incremental indexing והצגת זמן משוער.
- Ingestion משתמש Batch insert/COPY. יעד 10,000 Log events לדקה נמדד בנפרד ואינו מבטיח Vectorization של כל Log.
- אינדקסים על Workspace/Organization, Service, Environment, Timestamp, Trace ID, Commit, File path, Symbol, Full-Text vector ו-Embedding.
- Partitioning ל-LogEvent/TraceSpan לפי זמן כאשר נפח ה-Dataset מצדיק זאת; אין להוסיף Partitioning ללא Benchmark לדמו קטן.
- כל Benchmark שומר חומרה, Dataset size, Model mode ו-Configuration כדי שהמספרים יהיו ניתנים לשחזור.

### 4.2 אבטחה

**מודל פריסה:** Local-first הוא ברירת המחדל. הקוד, האינדקס, Embeddings ו-Artifacts נשמרים ב-Volumes מקומיים. Self-hosted team mode הוא הרחבה; SaaS ציבורי אינו חלק מה-MVP.

**Authentication — משתמשי Web:** גם ב־Local mode קיימת התחברות, משום שהמערכת מחזיקה קוד וראיות פרטיים. כאשר Next.js ו־Django מוגשים תחת אותו Origin, ברירת המחדל היא Django server-side session ולא JWT מותאם אישית. הדפדפן מקבל Cookie אטום המכיל Session ID בלבד; ה־Cookie מוגדר `HttpOnly`,‏ `Secure` ב־HTTPS ו־`SameSite=Strict` או `Lax` לפי זרימת ההתחברות. פעולות שינוי דורשות CSRF token. Session ניתנת לביטול מיידי בצד השרת, ולכן אין Refresh Token שמסתובב בדפדפן.

**Session lifecycle:** התחברות מסובבת את Session key למניעת Session fixation. ברירת המחדל היא Idle timeout של 30 דקות ו־Absolute lifetime של 12 שעות; שינוי סיסמה, שינוי תפקיד, השבתת משתמש או Logout מבטלים Sessions רלוונטיות. מסך Security מאפשר לראות Sessions פעילות ולבטל את כולן. אפשרות "זכור אותי" אינה פעילה ב־MVP עבור Workspaces רגישים.

**Passwords ו־Login protection:** סיסמאות מגובבות באמצעות Argon2 דרך מנגנון ה־Password hashers של Django. Login מוגבל לפי Account ו־IP, ניסיונות כושלים מתועדים ומובילים ל־Lockout זמני מדורג. הודעת Login אינה חושפת אם כתובת אימייל קיימת. Password reset דורש Token חד־פעמי קצר־חיים ואינו נרשם בלוג.

**Collector/M2M authentication:** ה־Local Collector אינו מקבל Session של משתמש. הוא משתמש ב־API Token אקראי, בעל Prefix לזיהוי, Secret שמוצג פעם אחת בלבד, Hash הנשמר במסד, Scopes מצומצמים, Workspace קבוע, Expiration, Rotation ו־Revocation. אין לו הרשאה לצפות ב־Evidence, לאשר External AI או לנהל משתמשים.

**מדוע אין Access/Refresh JWT ב־MVP:** Refresh Token נחוץ בעיקר כאשר קיים Authorization server ולקוחות נפרדים כגון Mobile או Public API. במבנה Same-origin מקומי, Session בצד השרת פשוטה יותר לביטול ומצמצמת את הסיכון של Refresh Token ארוך־חיים. אם בעתיד יתווספו SaaS, Mobile או SSO, המערכת תשתלב ב־OIDC Authorization Code + PKCE עם Access Token קצר ו־Refresh rotation אצל ספק זהויות; לא נפתח מנגנון JWT ביתי.

**Authorization:** לאחר Authentication מתבצעת הרשאה לפי Organization, Workspace, Role, Environment ו־Sensitivity. Authentication מוצלח אינו מעניק אוטומטית גישה ל־Repository או ל־Evidence.

**Repository isolation:** mount לקריאה בלבד, Scanner ללא Egress, ללא Code execution וללא imports דינמיים. נתיבי Host אינם מתקבלים ישירות מ-Web request; רק Workspaces שאושרו בהגדרה מקומית זמינים.

**Scope controls:** Allowlist לקבצים, `.gitignore`, `.incidentlensignore`, Content Type validation, Size limits ו-Archive bomb protection עבור Evidence Bundles.

**Secrets/PII:** סריקה משולבת Regex, entropy ודפוסים ניתנים להרחבה. Redaction מתבצע לפני Embedding ולפני Context selection. ממצאי Secret נשמרים כ-Type/Location בלבד, לא כערך גולמי.

**Embeddings are sensitive:** Vector indexes נחשבים נגזרת של הקוד ומקבלים אותה מדיניות Retention והרשאה. הם אינם מועלים אוטומטית לשירות חיצוני.

**שלושה מצבי AI:**

1. `MOCK` — בדיקות ו-CI ללא רשת.
2. `LOCAL` — מודל מקומי, ללא Data egress.
3. `CONTROLLED_EXTERNAL` — רק EvidenceSet מצומצם ומסונן נשלח דרך LLM Gateway לאחר Context Preview ואישור משתמש או Policy מפורשת.

Repository מלא, `.env`, Git objects ו-Artifacts שאינם חלק מה-EvidenceSet לעולם אינם נשלחים למודל החיצוני. ה-LLM Gateway הוא הרכיב היחיד המורשה ל-Egress, עם Timeout, Host allowlist, Budget ו-Audit metadata.

**Prompt Injection:** תוכן מאוחזר עטוף כ-Untrusted evidence; Structured Output מחייב Pydantic schema; אין Tool execution מתוך Generation; הוראות המופיעות בקוד או במסמך אינן מקבלות סמכות. תרחישי Injection נכללים ב-Golden Dataset.

**Authorization:** כל Retrieval query כולל Workspace/Organization, Environment, Sensitivity, Source status ו-Commit scope בתוך ה-WHERE. אין Post-filter כתחליף להרשאה. Context selection מבצע בדיקה נוספת לפני LLM Gateway.

**Context Preview:** במצב חיצוני המשתמש רואה סוגי מקורות, קבצים, טווחי שורות, Redactions ונפח לפני שליחה. ניתן לחסום קטע או לעבור למודל מקומי. אין צורך להציג Secrets שהוסרו.

**Data lifecycle:** מחיקת Workspace מבטלת Retrieval מיד ומוחקת Chunks, Embeddings ו-Artifacts לפי Job מתועד. Investigation Snapshots נשמרים לפי Policy ואינם מחזיקים טקסט מלא מעבר לנדרש.

**Web security:** HTTPS ב-Team mode, Security Headers, CORS מפורש, Rate limiting, Upload limits ו-Rate limit נפרד לחקירות יקרות. Budget circuit breaker נאכף בזמן ריצה.

**Audit:** תיעוד חיבור Repository, שינוי Scope, Re-index, External AI approval, שמות המקורות שנשלחו, שינוי הרשאות, צפייה בראיה רגישה ומחיקה. Payload רגיש אינו נכתב ל-Audit log.

המערכת אינה טוענת לעמידה רגולטורית מלאה כפרויקט Portfolio; היא מדגימה Controls ועקרונות שניתן להרחיב בביקורת אבטחה אמיתית.

### 4.3 תאימות

- Chrome, Edge, Safari ו-Firefox מודרניים.
- Desktop/Laptop כיעד ראשי, Tablet שימושי ו-Mobile לצפייה בסיסית.
- עברית ואנגלית, כולל RTL מלא.
- OpenAPI באמצעות `drf-spectacular`, Versioning תחת `/api/v1`.
- הרצה מקומית ב-Windows/macOS/Linux דרך Docker Compose, בכפוף לדרך שונה להגדרת bind mount בכל מערכת.
- MVP מנתח Python באופן מלא; TypeScript מסומן Beta/שלב הבא ולא מוצג כשווה-יכולת לפני Evaluation נפרד.
- Evidence Bundle תומך תחילה ב-UTF-8 text, JSON, Markdown ו-Log text. PDF ותמונות הם תוספת, לא מקור חובה לאבחון קוד.

## 5. ארכיטקטורה

### 5.1 חבילת טכנולוגיות

**Frontend:** TypeScript, Next.js App Router, React, TanStack Query, Zod, Tailwind CSS ו-Recharts. SSE עבור Progress עם Polling fallback. תצוגת קוד מתחילה ברכיב Highlight קל; Monaco יתווסף רק אם גודל Bundle וביצועים מצדיקים זאת.

**Backend:** Python, Django ו-DRF כ-Control Plane לניהול Workspace, Auth, Sources, Incidents, Permissions, Admin ו-API. הלוגיקה העסקית נמצאת ב-Application Services; Views ו-Models נשארים דקים.

**Local Collector:** פקודת CLI ב-Python או Management command שרושמת Repository מאושר, מאמתת path/Commit ומפעילה Scan. ה-Collector אינו שירות ענן ואינו מקבל פקודות שרירותיות מהדפדפן.

**Code Intelligence:** Python AST parser ב-MVP, Stack Trace parser, Git CLI בקריאה בלבד עם פקודות allowlisted, Symbol index ו-call relationships בסיסיים. Parsing אינו מבצע import לקוד המשתמש.

**RAG Core:** חבילת Python עצמאית ב-`packages/rag_core` בגבול hexagonal. היא כוללת Query planning, Retrieval adapters, RRF, Structural expansion, Reranking, Context selection, Sufficiency, Hypothesis generation ו-Citation validation. היא אינה תלויה ישירות ב-Django ORM; Ports מקבלים DTOs/Pydantic models.

**Background Processing:** Celery עבור Scan, Ingestion, Embeddings, Investigation ו-Evaluation; Redis כ-Broker/Cache זמני. PostgreSQL הוא מקור האמת לכל Status עסקי.

**Database:** PostgreSQL + pgvector/HNSW, Full-Text Search ו-JSONB. מודל Embedding פעיל יחיד ל-Workspace ב-MVP. Exact baseline נשמר ל-Evaluation של ANN recall.

**Object Storage:** MinIO מקומי עבור Evidence Bundles, Logs גדולים, Trace exports ו-Evaluation artifacts. אם רוצים פרופיל הרצה מינימלי, Adapter מקומי מבוסס Volume יכול להחליף אותו; Domain אינו תלוי ב-S3 API ישירות.

**AI Gateway:** Adapter משותף ל-MOCK, LOCAL ו-CONTROLLED_EXTERNAL. הוא מבצע Redaction check, Context budget, Policy check, Preview approval, Timeout, Usage accounting ו-Structured Output validation.

**Observability:** OpenTelemetry עבור Django, Celery, Retrieval ו-LLM Gateway; Grafana, Prometheus ו-Tempo/Jaeger ב-Compose profile אופציונלי. אין להסתמך על Semantic conventions ניסיוניים כחוזה נתונים עסקי.

**Infrastructure:** Docker Compose, Networks נפרדות ל-Scanner ול-LLM Gateway, Volumes מקומיים, Health checks ו-GitHub Actions ל-Lint, Type check, Tests, Build ו-Security scanning.

זרימת הרכיבים:

```text
Local repository (read-only) / Evidence bundle
        ↓
Collector + Secret scanner + Code parser
        ↓
Evidence store + Symbol index + pgvector
        ↓
Incident + Readiness gate
        ↓
Code-aware hybrid retrieval
        ↓
Context selector
        ↓
LLM Gateway (local or approved external)
        ↓
Hypotheses + Citation validation
        ↓
VERIFIED / PROBABLE / INSUFFICIENT_EVIDENCE
```

### 5.2 מודל נתונים

**Organization / Workspace:** Organization נשמרת כגבול עתידי ל-Team mode; Workspace הוא יחידת Local repository/index בפועל. הוא כולל Root identifier, Active commit, Parser version, Active embedding index, AI mode, Ignore policy ו-External sharing policy.

**User / TeamMembership:** משתמש Django, תפקיד, Workspace access, Environment access ו-Sensitivity ceiling. Local mode כולל משתמש יחיד; Team mode מפעיל את מלוא RBAC.

**Service / ServiceDependency:** שירות, Owner, Repository workspace, Runtime names, שפה, Environments ותגיות; קשר מכוון עם פרוטוקול, Endpoint וקריטיות.

**RepositorySnapshot:** Workspace, Commit SHA, Branch/Tag, Tree hash, Scan status, Indexed paths, Ignore rules hash, Parser version ויצירת זמן. Investigation מצביע ל-Snapshot קבוע ולא ל-`main` משתנה.

**Source / SourceDocument:** סוג מקור, מצב Local/external allowed, Checksum, Object key, Retention, Sensitivity, Version ו-Ingestion status.

**CodeSymbol:** Snapshot, file path, symbol name, qualified name, kind, line range, language, doc summary ו-content hash.

**SymbolRelation:** קשר `CALLS`, `IMPORTS`, `DEFINES`, `TESTS` או `HANDLES_EXCEPTION` בין Symbols, עם Confidence של ה-Static parser.

**DocumentChunk / ChunkEmbedding:** Chunk ברמת Symbol/Section ו-Embedding בממד הקבוע של ה-Index הפעיל. החלפת מודל יוצרת Index version נפרד.

**EvidenceItem:** שכבת Retrieval מנורמלת עם Provenance מלא, Source span, Commit, Service, Environment, Timestamp, Trace ID, Sensitivity, Redaction state ו-Authorization scope.

**Incident:** סימפטום, Environment, Severity, Time range, Suspicious services, Error identifiers, `business_impact_started_at`, RepositorySnapshot, Readiness band ו-Readiness missing items.

**IncidentAttachment:** Stack Trace, Log, Screenshot metadata או Evidence Bundle item, עם Content type, Checksum, Scan status ו-Redaction report.

**InvestigationRun:** Pipeline versions, Snapshot, AI mode, Progress state, Sufficiency iteration, Stop reason, Context size, Tokens, Cost, Latency ו-Result state.

**InvestigationStep:** Query/Result metadata לכל שלב, ללא Payload רגיש מיותר.

**ContextSnapshot:** רשימת Evidence IDs, spans, Redaction state ו-Approval שהועברו ל-Generation. זהו בסיס Reproducibility ו-Citation validation.

**Hypothesis / Claim / HypothesisEvidence:** Hypothesis מכיל Claims אטומיים; כל Claim מצביע ל-Evidence supporting/contradicting/contextual ומקבל Validation status.

**Recommendation:** פעולה מוצעת, Reason, Risk, Evidence, Status ותוצאת משתמש; ללא Tool execution.

**LogEvent / TraceSpan / Deployment / CodeChange:** נתוני Runtime ו-Delivery עם Service, Environment, Timestamp, Trace/Commit correlation ו-Provenance.

**Resolution:** Root Cause אנושי, Verification method, Responsible component, Fix reference ו-Resolved time, נפרד מפלט המודל.

**EvaluationCase / EvaluationRun / EvaluationResult:** Ground Truth כולל Snapshot, Root cause, File, Symbol, Required evidence, Expected abstention ו-Security assertions.

**AuditEvent:** פעולה, actor, object, Request ID, Timestamp, Outcome ו-Metadata מסונן; External AI approval שומר Evidence identifiers בלבד.

### 5.3 ממשקי API (תחת `/api/v1`)

`/auth/csrf`, `/auth/login`, `/auth/logout`, `/auth/me`, `/auth/sessions`, `/auth/change-password` — התחברות, ניהול Session ואבטחת חשבון. אין `/auth/refresh` ב־MVP משום שאימות Web מבוסס Session בצד השרת.

`/collector-tokens` — יצירה, Rotation וביטול של Machine tokens מצומצמי Workspace/Scope; ה־Secret מוחזר פעם אחת בלבד.

`/organizations`, `/users`, `/teams`, `/services` — ניהול Domain והרשאות.

`/workspaces` — רשימת Workspaces שאושרו מקומית, Policy, Active snapshot ו-AI mode. יצירת path חדש נעשית דרך Collector מקומי ולא באמצעות path חופשי ב-Web.

`/workspaces/{id}/snapshots` — Scan/Re-index של Commit, סטטוס, Parser/Index version ו-Redaction summary.

`/sources`, `/documents` — ניהול מקורות ו-Artifacts.

`/evidence-bundles` — העלאת Bundle עם Size/type validation, Scan ו-Preview של מה שנכלל.

`/incidents` — פתיחה, עדכון וסגירה.

`/incidents/{id}/readiness` — מצב מוכנות, ראיות זמינות ורשימת מידע חסר; אינו מפעיל LLM.

`/incidents/{id}/investigations` — פתיחה, ביטול והרצה מחדש על Snapshot קבוע.

`/investigations/{id}/events` — SSE progress; `/investigations/{id}` משמש Polling fallback.

`/investigations/{id}/context-preview` — רשימת מקורות ו-spans המועמדים לשליחה חיצונית, Redactions ואישור/דחייה.

`/incidents/{id}/questions`, `/investigations/{id}/hypotheses`, `/evidence/{id}`, `/recommendations/{id}` — זרימת החקירה והמשוב.

`/search` — Debug UI לחיפוש Exact/FTS/Vector/Temporal/Structural תחת אותו Scope והרשאות.

`/evaluations` — הרצת והשוואת Pipeline versions.

`/incidents/{id}/report` — ייצוא Markdown; PDF הוא Polish לאחר יציבות התוכן.

`/health` ו-`/readiness` — Liveness/Readiness תשתיתי, נפרד מ-Incident Evidence Readiness.

כל API יקר תומך Idempotency key, Rate limit ו-Request ID. API אינו מחזיר host paths מלאים למשתמש שאינו מורשה.

## 6. תוספות נוספות שהוחלט לכלול

- **Seed demo מלא:** Repository Python סינתטי, שלושה שירותים, Git history, Deployments, Logs, Traces, Runbooks ותרחישי Ground Truth. `docker compose up` טוען Dataset, אך אינו מפעיל תקלה אקראית שאינה ניתנת לשחזור.
- **שני מסלולי Onboarding:** Workspace מקומי לקריאה בלבד ו-Evidence Bundle. שניהם מגיעים לאותו Evidence model אך מציגים Coverage שונה.
- **Evidence Readiness screen:** מסך חובה לפני חקירה, עם Code version, Error localization, Runtime evidence, Config/Deployment coverage ומידע חסר.
- **Privacy Center:** Ignore rules, Redaction report, AI mode, Data retention ו-Context Preview. זהו מסך מרכזי בדמו ולא הערת אבטחה נסתרת.
- **Search debugger:** הצגת תוצאות כל ערוץ, RRF contribution, Reranker score וסיבת הבחירה; מועיל ל-Evaluation ולראיון טכני.
- **Result state UI:** הפרדה ברורה בין Verified, Probable ו-Insufficient evidence; עובדות, Inferences ו-Missing evidence מוצגים בנפרד.
- **README demo path:** תרחיש אחד פתור, תרחיש אחד Probable ותרחיש אחד שחייב Abstention, כדי להוכיח אמינות ולא רק Happy path.
- **CI:** Lint, Type check, Unit/Integration tests, Migration check, Build, Dependency/secret scan ו-Evaluation smoke test ב-MOCK mode.
- **Security test artifacts:** Prompt injection, cross-workspace access, secret redaction, malicious archive ו-Wrong commit.
- **Load test artifact:** Locust או k6 למדדי API/Retrieval; תוצאות מתועדות לפי חומרה ו-Dataset.
- **Architecture Decision Records:** Local-first, No code execution in MVP, Single active embedding model, Postgres+pgvector, Django control plane ו-External AI gateway.

## 7. נספח — סדר בנייה מומלץ (רצף מימוש, לא צמצום היקף)

כל היעדים נשארים ב-Roadmap, אך ה-MVP המוגדר מסתיים ב-M6 וכולל אבחון סטטי מבוסס ראיות ללא הרצת קוד משתמש. Cloud connectors, TypeScript parity ו-Sandbox verification אינם תנאי להשקת גרסת Portfolio.

| שלב | תכולה |
|---|---|
| M0 — יסודות Local-first | Django+DRF, Next.js, Postgres+pgvector, Docker Compose, Workspace/User בסיסיים, localhost-only, OpenAPI, health checks, AI modes skeleton |
| M1 — Secure Intake | Local Collector, read-only repository mount, Evidence Bundle, allowlist/ignore rules, checksum, secret redaction, MinIO/volume adapter, Audit בסיסי |
| M2 — Code Intelligence | Python AST, Stack Trace parser, RepositorySnapshot/Commit validation, CodeSymbol/SymbolRelation, symbol-level chunks, Git diff, incremental indexing |
| M3 — חיפוש היברידי | Exact + FTS + Vector + Temporal + Structural expansion, RRF, Dedup/diversity, local reranker fallback, `/search`, retrieval evaluation |
| M4 — Evidence Readiness | Incident intake, minimum evidence contract, readiness bands, wrong-commit detection, Timeline, missing-evidence recommendations |
| M5 — ליבת חקירה | `rag_core`, planning, parallel retrieval, sufficiency, ContextSnapshot, Hypotheses/Claims, Confidence bands, Citation validation, SSE/polling |
| M6 — Trust & Evaluation — גבול MVP | AI Gateway, LOCAL/MOCK/controlled external flow, Context Preview, injection tests, security assertions, Golden Dataset, evaluation dashboard, Verified/Probable/Insufficient UI |
| M7 — Workflow & Polish | Follow-up retrieval, Recommendations status, Resolution/Feedback, report export, i18n/RTL, Admin, OTel profile, CI badges, load test |
| M8 — Roadmap מתקדם | GitHub/GitLab read-only connector, OpenTelemetry live connector, TypeScript analyzer parity, Self-hosted team mode, isolated verification sandbox, regression-test suggestions |

קריטריון סיום ה-MVP אינו "המודל נתן תשובה", אלא תהליך מלא הניתן לשחזור:

```text
Repository snapshot + Incident evidence
→ Secure scan and readiness
→ Code-aware retrieval
→ Evidence-grounded hypotheses
→ Citation/policy validation
→ Correct result state
→ Measured evaluation result
```
