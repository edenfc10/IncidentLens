# אפיון מערכת: IncidentLens – פלטפורמה חכמה לחקירת תקלות במערכות מבוזרות

**הסבר קצר:** מערכת חקירה ותמיכה בקבלת החלטות (Incident Investigation Orchestration Layer), המיועדת למהנדסי תוכנה, DevOps ו-SRE. המערכת מרכזת לוגים, Traces, Deployments, שינויי קוד, Runbooks ותקלות קודמות, ומפיקה השערות מדורגות לסיבת השורש של התקלה — עם ראיות ניתנות לאימות, ציטוטים, רמת ביטחון והמלצות לבדיקות המשך.

## 1. רקע

### 1.1 חזון הפרויקט

יצירת נקודת חקירה מרכזית (Single Point of Investigation) המאפשרת לצוותי פיתוח ותפעול להבין במהירות מדוע תקלה התרחשה, אילו שירותים הושפעו, איזה שינוי קדם לה ומה יש לבדוק כדי לאמת את סיבת השורש.

המערכת נועדה להפוך תהליך חקירה ידני ומפוזר לתהליך סדור, שקוף ומבוסס ראיות. במקום לעבור ידנית בין מערכות לוגים, כלי Tracing, היסטוריית Deployments, מאגרי קוד ומסמכי Runbook, המשתמש מקבל סביבת עבודה אחת שמאגדת את כל המידע הרלוונטי ומציגה כיצד כל מסקנה נגזרה ממנו.

IncidentLens אינה מיועדת להחליף מהנדס או לבצע פעולות אוטונומיות בסביבת Production. היא משמשת מערכת תומכת החלטה: אוספת ראיות, מדרגת השערות, מציגה מידע חסר ומציעה פעולות בדיקה בטוחות. כל פעולה משנה מערכת, כגון Rollback, Restart או שינוי קונפיגורציה, תדרוש אישור אנושי מפורש ולא תיכלל בגרסה הראשונה.

### 1.2 מצב קיים

חקירת תקלות במערכות מבוזרות דורשת כיום מעבר בין מקורות רבים שאינם מחוברים בהכרח זה לזה. הלוגים עשויים להצביע על סימפטום בשירות אחד, בעוד שסיבת השורש נמצאת בשירות תלוי, בשינוי קוד, במשתנה סביבה או ב-Deployment שבוצע דקות קודם לכן.

במצב הקיים קיימים מספר קשיים מרכזיים:

- המידע מפוזר בין Logs, Traces, Metrics, Git, מערכות CI/CD, Runbooks ו-Incident history.
- קישור בין אירועים משירותים שונים מתבצע ידנית באמצעות זמן, `trace_id`, שמות שירותים וקודי שגיאה.
- הודעת השגיאה שהמשתמש רואה היא לעיתים סימפטום ולא סיבת השורש.
- ידע מתקלות קודמות נשמר ב-Postmortems או בזיכרון של אנשי צוות ואינו נגיש בזמן אמת.
- כלי חיפוש רגילים מתקשים למצוא תקלות דומות שנוסחו במילים שונות.
- מערכות AI כלליות עלולות להציע פתרונות ללא בסיס במידע הארגוני או להציג השערה כעובדה.
- קשה למדוד באופן שיטתי האם מערכת החקירה מצאה את המקור הנכון והאם הציטוטים תומכים במסקנה.

### 1.3 הפתרון המוצע

פלטפורמת IncidentLens משמשת כשכבת חקירה מעל מקורות המידע התפעוליים, בארכיטקטורת Evidence-First: מקורות המידע המקוריים נשארים מקור האמת, ומסד הנתונים של IncidentLens משמש שכבת אינדוקס, הרשאות, קורלציה, חקירה ו-Audit.

הפתרון כולל:

- ממשק Web ב-Next.js ו-TypeScript לפתיחת Incidents, צפייה ב-Timeline, השערות, ראיות והמלצות.
- שרת Backend ב-Django וב-Django REST Framework לניהול משתמשים, צוותים, הרשאות, Incidents, מקורות מידע ותוצאות חקירה.
- מנוע RAG עצמאי ב-Python המבצע חיפוש מדויק, חיפוש טקסטואלי, חיפוש וקטורי, סינון לפי זמן והרשאות, איחוד תוצאות ו-Reranking.
- מנוע חקירה המייצר מספר השערות מובנות, מקשר כל טענה לראיות ומציג גם ראיות סותרות ומידע חסר.
- PostgreSQL עם pgvector עבור המידע העסקי, האינדקס הווקטורי והחיפוש ההיברידי.
- Celery ו-Redis להפעלת תהליכים ארוכים כגון Ingestion, יצירת Embeddings, חקירה ו-Evaluation.
- MinIO עבור שמירת קבצים מקוריים ו-Artifacts גדולים.
- סביבת Microservices סינתטית המייצרת תקלות ידועות מראש, Logs, Traces ו-Deployments לצורך הדגמה ומדידה.

### 1.4 מדדי הצלחה

**איכות אחזור:** לפחות 90% מהתרחישים ב-Golden Dataset יחזירו את הראיה הנדרשת בתוך חמש התוצאות הראשונות (`Recall@5 ≥ 0.90`).

**דיוק חקירה:** זיהוי נכון של השירות וסיבת השורש בלפחות 80% מתרחישי התקלה המוגדרים מראש.

**אמינות ציטוטים:** לפחות 95% מהציטוטים בתשובה יפנו למקור שתומך בפועל בטענה שאליה הוא משויך.

**מניעת טענות לא נתמכות:** שיעור טענות מהותיות ללא ראיה יהיה נמוך מ-5% בסט הבדיקות.

**ביצועים:** זמן תגובה של API עסקי רגיל יהיה נמוך מ-300ms ב-p95, לא כולל משימות AI ותהליכים אסינכרוניים. חקירה מלאה של תרחיש דמו תסתיים בתוך 30 שניות ב-p95, בהתאם לספק המודל.

**שימושיות:** משתמש יוכל לפתוח Incident, להריץ חקירה, לבדוק את המקורות ולאשר או לדחות את ההשערה המובילה ללא מעבר לממשק ניהול אחר בתרחישי הדמו.

**שקיפות:** כל תוצאת חקירה תכלול Timeline, השערות, ראיות תומכות, ראיות סותרות, מידע חסר וגרסת Pipeline/מודל ששימשה להפקתה.

## 2. פערים ואתגרים

### 2.1 פערים ואתגרים

**מקורות הטרוגניים:** Logs, Traces, Deployments, Code Changes, Runbooks ו-Postmortems מגיעים במבנים שונים. נדרשת שכבת Normalization הממירה אותם למודל ראיות אחיד תוך שמירת המקור והמטא-דאטה המקוריים.

**קורלציה בזמן:** קרבה בזמן בין Deployment לתקלה היא ראיה חשובה אך אינה הוכחה סיבתית. המערכת צריכה לשלב קורלציה בזמן עם קודי שגיאה, קשרי שירותים, שינויי קוד וראיות היסטוריות.

**זיהוי סימפטום מול סיבת שורש:** שגיאת `503` ב-Checkout עשויה לנבוע משגיאת Authentication בשירות אחר. מנגנון החקירה נדרש להרחיב את החיפוש בהתאם לגרף התלויות ול-Trace הרלוונטי.

**איכות RAG:** חלוקה לא נכונה לקטעים, Embeddings לא מתאימים או שאילתת חיפוש כללית מדי עלולים לגרום לאחזור שגוי. נדרש למדוד בנפרד את שלב האחזור ואת שלב יצירת התשובה.

**הזיות מודל:** מודל השפה עלול להציג הסבר סביר שאינו נתמך בנתונים. לכן כל טענה מהותית תחויב בהפניה ל-`evidence_id`, ותעבור בדיקת Citation Validation לפני הצגה.

**סתירות בין מקורות:** Runbook ישן, Incident קודם ו-Deployment נוכחי עלולים להצביע על מסקנות שונות. המערכת תציג סתירות בגלוי ותתחשב בעדכניות ובסמכות המקור.

**הרשאות:** אסור שמשתמש יקבל מידע ממקור שאינו מורשה לצפות בו. סינון לפי Organization, Team, Environment ו-Sensitivity יתבצע לפני האחזור ולפני שליחת ההקשר למודל.

**נפח Telemetry:** לוגים ו-Traces יכולים לגדול במהירות. בגרסת תיק העבודות הנתונים יישמרו ב-PostgreSQL עם Partitioning לפי זמן; מעבר ל-ClickHouse או OpenSearch יישקל רק כאשר Benchmarks יצביעו על צורך ממשי.

**תלות בספק מודל:** שינוי מודל עשוי לשנות איכות, זמן ועלות. הגישה למודלים תתבצע דרך Provider Interface פנימי, ותוצאות Evaluation יישמרו לפי ספק, שם מודל וגרסת Prompt.

### 2.2 דרישות רגולטוריות

עמידה בעקרונות אבטחת מידע התואמים ISO 27001, כולל Least Privilege, ניהול סודות, Audit Trail והפרדת סביבות.

תמיכה בעקרונות פרטיות של GDPR: צמצום מידע, מדיניות שמירה ומחיקה, יכולת איתור נתונים רגישים ואי-העברת מידע לא מורשה לספק מודל חיצוני.

דרישת נגישות בתקן WCAG 2.2 AA עבור המסכים המרכזיים, לרבות ניווט מקלדת, Focus ברור, ניגודיות, תוויות נגישות והצגה שאינה תלויה בצבע בלבד.

ניהול Audit Trail מלא: תיעוד פעולות יצירה, שינוי ומחיקה; פתיחת חקירה; צפייה במקור רגיש; שינוי הרשאות; הפעלת Evaluation; ואישור או דחיית Root Cause. הרשומה תכלול משתמש, זמן, כתובת IP, סוג פעולה, אובייקט יעד, סטטוס ומזהה בקשה.

## 3. דרישות פונקציונליות

### 3.1 יכולות עיקריות

**ניהול משתמשים ותפקידים:** תמיכה בחמש רמות עיקריות: Super Admin, Organization Admin, Incident Commander, Engineer ו-Viewer. ההרשאות ישולבו עם חברות בצוות וגישה לסביבות כגון Development, Staging ו-Production.

**ניהול שירותים ותלויות:** יצירה וניהול של קטלוג שירותים, Owners, Repositories, Environments וקשרים בין שירותים. קשרים אלה ישמשו להרחבת חיפוש בזמן חקירה.

**ניהול מקורות מידע:** רישום, הפעלה, השהיה ומעקב אחר מקורות מסוג מסמכים, Runbooks, Postmortems, Logs, Traces, Deployments ושינויי קוד.

**Ingestion ואינדוקס:** קליטת מקור, שמירת Artifact מקורי, חישוב Checksum, נרמול, חלוקה לקטעים, הסרת סודות, יצירת Embeddings ושמירה באינדקס. התהליך יהיה אידמפוטנטי ויתמוך ב-Retry.

**פתיחת Incident:** יצירת אירוע עם כותרת, תיאור, חומרה, סביבה, טווח זמן, שירותים חשודים, קודי שגיאה, `trace_id` וראיות ראשוניות.

**בניית Timeline:** הצגה כרונולוגית מאוחדת של Deployments, שינויים, Errors, Spans, פעולות משתמש והתחלת ההשפעה העסקית.

**חיפוש היברידי:** שילוב Exact Match, PostgreSQL Full-Text Search, Vector Search וחיפוש Temporal. התוצאות יאוחדו באמצעות Reciprocal Rank Fusion ויעברו Deduplication ו-Reranking.

**חקירה רב-שלבית:** פירוק Incident לתת-שאלות, חיפוש ממוקד בכל ערוץ, הרחבה לפי תלויות והערכת sufficiency לפני הפקת דוח.

**יצירת השערות:** יצירת מספר Hypotheses ולא מסקנה יחידה. לכל השערה יישמרו הסבר, ראיות תומכות, ראיות סותרות, מידע חסר, פעולות אימות ורמת ביטחון מחושבת.

**Citation Validation:** בדיקה שכל טענה מהותית מפנה לראיה קיימת, שהראיה הועברה למודל, שהמשתמש מורשה לראותה ושהקטע תומך בטענה.

**המלצות לפעולות:** הצעת בדיקות בטוחות כגון בדיקת Worker, השוואת Environment Variable, בדיקת Metric או שחזור Request. בגרסה הראשונה לא יבוצעו פעולות Production באופן אוטומטי.

**שאלות המשך:** המשתמש יוכל לשאול שאלות נוספות בתוך החקירה. כל שאלה תכלול את הקשר ה-Incident, אך תפעיל Retrieval חדש ולא תסתמך רק על זיכרון השיחה.

**פתרון וסגירת Incident:** הזנת Root Cause מאומת, שירות אחראי, פעולת פתרון, זמן פתרון והערות. הנתונים יהפכו למקור היסטורי עבור חקירות עתידיות.

**משוב:** אישור או דחיית השערה, סימון ראיה כרלוונטית והערכת המלצה. המשוב יישמר לצורך Evaluation ושיפור דירוג, אך לא ישנה מודל אוטומטית ללא תהליך מבוקר.

**Evaluation:** הרצת Golden Dataset והשוואת גרסאות Pipeline, Embedding, Reranker, Prompt ומודל לפי Retrieval Recall, Root Cause Accuracy, Citation Correctness, Unsupported Claims, Latency ועלות.

**ממשק ניהול:** ניהול משתמשים, מקורות, מסמכים, שירותים, תרחישי Evaluation ועבודות שנכשלו באמצעות Django Admin, למשתמשים מורשים בלבד.

### 3.2 אופני שימוש לדוגמה

**תרחיש חקירת Deployment:** לאחר Deployment של `auth-service`, משתמשים מקבלים `503` ב-Checkout. Incident Commander פותח Incident ומגדיר טווח זמן. המערכת מאתרת `AUTH_TOKEN_EXPIRED`, מקשרת את ה-Trace מ-Checkout דרך Payment ל-Auth, מוצאת שינוי ב-`AUTH_REFRESH_TTL`, מאתרת Runbook ו-Incident קודם ומציגה כשל בחידוש טוקנים כהשערה מובילה.

**תרחיש ללא מספיק מידע:** המערכת מזהה עלייה ב-Timeouts אך אין Metrics מהשירות התלוי ואין שינוי Deployment. במקום לקבוע Root Cause, היא מציגה ביטחון נמוך ומבקשת לבדוק זמינות של Dependency מסוים.

**תרחיש הרשאות:** Engineer מצוות Checkout יכול לראות Logs של Checkout ו-Payment אך אינו מורשה לצפות בנתוני Production של Auth. מקורות Auth לא ייכללו ב-Retrieval ולא יישלחו למודל. המערכת תציין שחסר מקור מורשה הדרוש להמשך החקירה.

**תרחיש Evaluation:** מפתח משנה את אסטרטגיית Chunking ומריץ את Golden Dataset. המערכת משווה בין הגרסה הקודמת לחדשה ומציגה שיפור ב-Recall לצד שינוי בעלות ובזמן.

## 4. דרישות לא פונקציונליות

### 4.1 ביצועים

תמיכה ב-100 משתמשים פעילים במקביל בסביבת הדגמה או Staging, עם אפשרות Scale-out ל-Web ול-Workers.

טעינת מסכים מרכזיים ב-Frontend בתוך פחות מ-2 שניות בתנאי רשת רגילים, כאשר מידע כבד נטען באופן הדרגתי.

זמן תגובה p95 נמוך מ-300ms לפעולות CRUD רגילות שאינן מפעילות AI.

זמן חיפוש היברידי p95 נמוך מ-2 שניות על Dataset היעד של גרסת תיק העבודות, לא כולל Reranking חיצוני.

סיום חקירה מלאה בתוך 30 שניות ב-p95 בתרחישי הדמו, עם הצגת Progress לפי שלבים במקום חסימת Request פתוח.

עיבוד Ingestion אסינכרוני עם Backpressure ו-Retry, תוך יעד התחלתי של 10,000 אירועי Log בדקה בסביבת בדיקות מקומית מתאימה.

שימוש ב-Database Indexes על Tenant, Team, Service, Environment, Timestamp, Trace ID, Full-Text Vector ו-Embedding.

Partitioning של טבלאות Telemetry לפי זמן ומדיניות Retention המאפשרת מחיקת מחיצות ישנות בצורה מבוקרת.

### 4.2 אבטחה

אימות משתמשי Web באמצעות Django Session Authentication ו-HTTP-only Secure Cookies תחת Same-Origin, כולל הגנת CSRF. אינטגרציות Machine-to-Machine ישתמשו ב-API Tokens מצומצמי Scope הנשמרים בצורה מגובבת.

מערכת RBAC המבוססת על תפקיד, Organization, Team, Environment ו-Sensitivity. בדיקת ההרשאה תתבצע גם ברמת QuerySet וגם לפני Retrieval.

הפרדה מלאה בין Tenants וארגונים. כל רשומה עסקית וראיה תישא `organization_id`; שאילתות ללא Scope ארגוני ייחסמו כברירת מחדל.

הסרת Secrets ו-PII לפני אינדוקס, לרבות API Keys, Authorization Headers, Tokens, Passwords וערכים המוגדרים במדיניות הארגון.

התייחסות לתוכן מאוחזר כמידע לא אמין ולא כהוראות מערכת, לצורך הפחתת Prompt Injection מתוך מסמכים או Logs.

שימוש ב-HTTPS, Security Headers, CORS מפורש, Rate Limiting, הגבלת גודל העלאה ו-Content Type Allowlist.

Audit logging לכל פעולה רגישה, לרבות צפייה בראיה מוגבלת, שינוי הרשאות והרצת חקירה מול נתוני Production.

ניהול סודות באמצעות Environment/Secret Store ולא בקוד, בקובצי Compose או ב-Repository.

### 4.3 תאימות

תמיכה בדפדפנים מודרניים: Chrome, Edge, Safari ו-Firefox.

ממשק רספונסיבי המותאם בעיקר למסכי Desktop ו-Laptop, עם תמיכה שימושית ב-Tablet. תצוגת Mobile תאפשר צפייה בסיסית אך אינה יעד העבודה הראשי.

תמיכה דו-לשונית בעברית ובאנגלית במסכים המרכזיים, כולל RTL מלא לעברית.

API מתועד באמצעות OpenAPI, עם Versioning מפורש תחת `/api/v1`.

תמיכה בהרצה מקומית ב-Windows, macOS ו-Linux באמצעות Docker Compose.

## 5. ארכיטקטורה

### 5.1 חבילת טכנולוגיות

**Frontend:** TypeScript עם Next.js ב-App Router, React, TanStack Query לניהול Server State, Zod לאימות סכמות, Tailwind CSS לעיצוב, Recharts לגרפים ו-Monaco Editor או רכיב קוד קל יותר להצגת Code Diff ו-Logs. גרסאות Stable יינעלו ב-Lockfile ולא ייכתבו כאילוץ קבוע במסמך האפיון.

**Backend:** Python עם Django ו-Django REST Framework. Django ישמש Control Plane לניהול Domain, Authentication, Permissions, Admin ו-API. הלוגיקה העסקית תיכתב בשכבת Services ולא בתוך Views או Models עבים.

**RAG Core:** חבילת Python עצמאית הכוללת Query Analysis, Retrieval, Rank Fusion, Reranking, Hypothesis Generation, Citation Validation ו-Provider Adapters. סכמות הקלט והפלט יוגדרו באמצעות Pydantic או Typed Dataclasses.

**Background Processing:** Celery עבור Ingestion, Embeddings, חקירות ו-Evaluation; Redis כ-Broker וכ-Cache זמני. מצב המשימה העסקי יישמר ב-PostgreSQL ולא יסתמך על Redis כמקור אמת.

**Database:** PostgreSQL כמסד העסקי והאנליטי לגרסת הפרויקט, עם הרחבת pgvector לחיפוש וקטורי, Full-Text Search לחיפוש מילולי, JSONB למטא-דאטה ו-Partitioning לנתוני Telemetry.

**Object Storage:** MinIO תואם S3 עבור מסמכים מקוריים, קובצי Log גדולים, Trace exports ו-Evaluation artifacts.

**Observability:** OpenTelemetry לאיסוף Traces, Metrics ו-Logs של IncidentLens ושל מערכת הדמו; Grafana לתצוגה, Prometheus ל-Metrics ו-Tempo או Jaeger ל-Traces. רכיבי התצפיות יופעלו באמצעות Profile נפרד ב-Docker Compose כדי לשמור על הרצה בסיסית קלה.

**Infrastructure:** Docker ו-Docker Compose לסביבות פיתוח והדגמה; GitHub Actions עבור Lint, Type Check, Tests, Build, Security checks ויצירת Images.

**AI Integration:** Provider Interface פנימי עבור Embeddings, Reranking ו-Reasoning LLM. ספק ברירת המחדל יוגדר באמצעות Environment, ללא תלות ישירה של Domain layer בספק מסוים.

### 5.2 מודל נתונים

המערכת משתמשת במודלים רלציוניים עם שדות JSONB למטא-דאטה משתנה:

**Organization:** ארגון או Tenant, מדיניות Retention, הגדרות AI ומגבלות שימוש.

**User:** משתמש Django מותאם, פרטי זיהוי, סטטוס, שפה והעדפות.

**TeamMembership:** שיוך משתמש לצוות ולתפקיד, כולל גישה לסביבות ולרמות רגישות.

**Service:** שירות תוכנה, Owner, Repository, שפה, סביבות ותגיות.

**ServiceDependency:** קשר מכוון בין שני שירותים, פרוטוקול, Endpoint, קריטיות וטווח תוקף.

**Incident:** כותרת, תיאור, חומרה, סביבה, סטטוס, טווח זמן, שירותים חשודים, יוצר ו-Root Cause מאומת.

**InvestigationRun:** הרצת חקירה, סטטוס, גרסת Pipeline, מודלים, Prompt version, זמני שלבים, Tokens, עלות ושגיאות.

**InvestigationStep:** Audit טכני של Query Analysis, Retrieval, Reranking, Generation ו-Validation ללא שמירת מידע רגיש שאינו נדרש.

**Hypothesis:** השערה, הסבר, דירוג, Confidence Band, מידע חסר וסטטוס אישור.

**HypothesisEvidence:** קישור Many-to-Many בין השערה לראיה עם סוג קשר: Supporting, Contradicting או Contextual.

**EvidenceItem:** מודל מאוחד לראיה עם Source Type, Timestamp, Service, Environment, Trace ID, מקור, טקסט מוצג, Metadata ו-Sensitivity.

**Source:** הגדרת מקור מידע, סוג Connector, סטטוס, Scope, תדירות סנכרון ו-Checkpoint.

**SourceDocument:** מסמך לוגי, URI, Checksum, גרסה, זמן עדכון, Object Key והרשאות.

**DocumentChunk:** קטע טקסט, סדר, כותרת, טווח שורות או עמודים, Content Hash, Search Vector ומטא-דאטה.

**ChunkEmbedding:** Embedding לפי Chunk ומודל, כולל Dimensions, Vector, זמן יצירה וגרסת Normalization. המפתח הלוגי יהיה `(chunk_id, model_name, model_version)`.

**LogEvent:** Timestamp, Service, Environment, Severity, Message, Trace ID, Span ID ו-Attributes. הטבלה תחולק למחיצות לפי זמן.

**TraceSpan:** Trace ID, Span ID, Parent Span, Service, Operation, Start, Duration, Status ו-Attributes.

**Deployment:** שירות, Environment, Version, Commit SHA, זמן Deployment, תוצאה ו-Artifact reference.

**CodeChange:** Commit, קבצים שהשתנו, Summary, Diff reference, מחבר וזמן.

**Recommendation:** פעולה מומלצת, מקור, Risk level, סטטוס ביצוע ותוצאת אימות.

**EvaluationCase:** Incident סינתטי או אנונימי, Ground Truth, Required Evidence וקריטריונים.

**EvaluationRun / EvaluationResult:** תוצאות לפי Case, Pipeline version, מדדים, Latency ועלות.

**AuditEvent:** משתמש או Integration, פעולה, אובייקט, IP, Request ID, זמן, סטטוס ו-Metadata מסונן.

### 5.3 ממשקי API

פיתוח REST API תחת `/api/v1` הכולל נתיבים מוגנים:

`/auth`: התחברות, התנתקות, פרטי משתמש נוכחי, CSRF ומצב Session.

`/organizations`: הגדרות ארגון, Retention, מגבלות AI ומדיניות מקורות — Organization Admin ומעלה.

`/users` ו-`/teams`: ניהול משתמשים, צוותים, תפקידים וגישה לסביבות.

`/services`: ניהול קטלוג שירותים, Owners ותלויות.

`/sources`: רישום מקורות, בדיקת חיבור, הפעלה, השהיה, סנכרון וסטטוס Ingestion.

`/documents`: העלאה, גרסאות, סטטוס אינדוקס, צפייה ב-Chunks ומחיקה מבוקרת.

`/incidents`: יצירה, עדכון, סגירה, הוספת שירותים, Timeline ו-Root Cause מאומת.

`/incidents/{id}/investigations`: פתיחת חקירה, קבלת Progress, תוצאה, ביטול והרצה מחדש.

`/incidents/{id}/questions`: שאלות המשך המבצעות Retrieval חדש בהקשר ה-Incident.

`/investigations/{id}/hypotheses`: השערות, אישור, דחייה ומשוב.

`/evidence/{id}`: שליפת ראיה, מקור מלא, Context והרשאות צפייה.

`/recommendations/{id}`: סימון פעולה כמתוכננת, בוצעה, הצליחה או נכשלה; ללא ביצוע Production אוטומטי ב-MVP.

`/evaluations`: יצירת Evaluation Run, סטטוס, השוואה בין ריצות וייצוא תוצאות.

`/audit`: חיפוש Audit Events למשתמשים מורשים.

`/health`: Liveness, Readiness וגרסת Build, ללא חשיפת סודות או מידע תפעולי רגיש.

## 6. אינטגרציות

### 6.1 מערכות חיצוניות

**OpenTelemetry Collector:** קבלת OTLP Logs, Traces ו-Metrics ממערכת הדמו. בשלב מתקדם יתאפשר חיבור ל-Collector ארגוני באמצעות Endpoint ו-Tokens מוגנים.

**Git Provider:** קליטת Repository metadata, Commits ו-Code Diffs. ב-MVP ייעשה שימוש ב-Repository מקומי או Dataset סינתטי; חיבור GitHub או GitLab יתווסף דרך Adapter נפרד.

**CI/CD Provider:** קליטת Deployment Events כולל Service, Environment, Version, Commit, Start Time ו-Result. ב-MVP ייעשה שימוש ב-Webhook סינתטי.

**Object Storage:** שמירה ושליפה של Artifacts באמצעות API תואם S3.

**AI Providers:** שירותי Embedding, Reranking ו-Reasoning דרך Interfaces נפרדים. כל Request יתועד ברמת Metadata, Latency ו-Token usage, ללא שמירת Secret או Payload רגיש מעבר למדיניות.

**Identity Provider:** ב-MVP אימות מקומי באמצעות Django. בעתיד ניתן יהיה לחבר OIDC/SAML עבור ספק ארגוני.

**Observability Backend:** Grafana, Prometheus ו-Tempo/Jaeger לצפייה בביצועי IncidentLens עצמו ובמערכת הדמו.

### 6.2 תהליכי סנכרון

**Push Ingestion:** קבלת Logs, Traces ו-Deployment Events דרך Endpoint או OpenTelemetry Collector. כל Batch יקבל Idempotency Key ו-Checkpoint.

**Pull Synchronization:** משיכה תקופתית של Runbooks, Postmortems ו-Code metadata ממקורות שהוגדרו לכך.

**Incremental Indexing:** אינדוקס רק של מקורות וגרסאות שהשתנו לפי Checksum או Cursor. Chunk שלא השתנה ישמור את ה-Embedding הקיים.

**Version Replacement:** גרסה חדשה של מסמך תסומן כפעילה, אך גרסאות ישנות יישמרו בהתאם למדיניות Retention כדי לאפשר שחזור חקירה היסטורית.

**Deletion Propagation:** מחיקת מקור תבטל אותו מיד מ-Retrieval ותפעיל משימה למחיקת Chunks, Embeddings ו-Artifacts בהתאם למדיניות Audit ו-Retention.

**Investigation Snapshot:** כל חקירה תשמור את מזהי הראיות והגרסאות שבהן השתמשה, כך שהתוצאה תישאר ניתנת לשחזור גם לאחר עדכון האינדקס.

## 7. ממשק המשתמש

### 7.1 עקרונות עיצוב

שימוש ב-Dark Mode וב-Light Mode בהתאם להעדפת המשתמש, עם ניגודיות נגישה.

עקביות ברכיבי הממשק: Buttons, Tables, Filters, Drawers, Modals, Toasts, Status indicators ו-Code blocks.

ממשק Evidence-Centric: כל מסקנה ניתנת לפתיחה למקור, ללא צורך לחפש ידנית את הציטוט.

הפרדה חזותית בין עובדה, השערה, ראיה סותרת ומידע חסר. אין להסתמך על צבע בלבד; ייעשה שימוש גם באייקון ובתווית טקסטואלית.

Progressive Disclosure: הצגת סיכום ברור תחילה ואפשרות לפתוח Logs, Trace, Diff ו-Retrieval details לפי הצורך.

תמיכה דו-לשונית בעברית ובאנגלית, כולל RTL מלא.

ממשק נקי וממוקד חקירה, ללא Dashboard עמוס במדדים שאינם מסייעים לקבלת החלטה.

### 7.2 מסכים עיקריים

**Dashboard:** רשימת Incidents פתוחים, חומרה, סטטוס חקירה, שירותים מושפעים, זמן מתחילת האירוע ו-Incidents אחרונים שנסגרו.

**פתיחת Incident:** טופס הכולל כותרת, תיאור, Severity, Environment, טווח זמן, שירותים חשודים, Error codes, Trace ID וקישורים ראשוניים.

**Investigation Workspace:** סביבת החקירה המרכזית הכוללת Timeline, השערה מובילה, השערות חלופיות, Evidence panel, מידע חסר, המלצות ושאלות המשך.

**Timeline:** ציר זמן מאוחד המציג Deployments, Code changes, Errors, Spans ושינויים במדדים, עם סינון לפי שירות וסוג אירוע.

**Evidence Viewer:** הצגת Log, Trace Span, Runbook section, Postmortem או Code Diff עם מקור, זמן, הרשאות והקשר מסביב.

**Service Map:** תרשים תלויות המדגיש שירותים מושפעים ואת מסלול ה-Trace הרלוונטי. המפה אינה מיועדת להיות מערכת Observability מלאה אלא כלי עזר לחקירה.

**Sources:** ניהול מקורות, מצב Connection, Last Sync, מספר פריטים, כשלי Ingestion ופעולת Re-index.

**Evaluation Dashboard:** השוואת Recall@K, Root Cause Accuracy, Citation Correctness, Unsupported Claims, Latency ועלות בין Pipeline versions.

**Administration:** ניהול משתמשים, צוותים, תפקידים, ארגונים ומדיניות באמצעות Django Admin, עם קישורים ממוקדים מהממשק למשתמש מורשה.

## 8. תכנית פיתוח

### 8.1 שלבי פיתוח

**אפיון וארכיטקטורה (בתהליך):** הגדרת מטרות, Scope, Domain model, Stack, מדדי איכות וסיכונים. מסמך זה הוא גרסה ראשונה ויעבור שיפור לפני תחילת המימוש המלא.

**תשתית (מתוכנן):** הקמת Monorepo, Django, Next.js, PostgreSQL + pgvector, Redis, Celery, MinIO, Docker Compose ו-CI בסיסי.

**מערכת דמו (מתוכנן):** פיתוח Checkout, Auth, Payment ו-Inventory Services, הוספת OpenTelemetry ו-Fault Injector עם לפחות חמישה תרחישי תקלה ידועים.

**Ingestion (מתוכנן):** קליטת מסמכי Markdown, Logs, Traces ו-Deployments; Normalization, Chunking, Secret redaction, Embeddings ו-Index status.

**Retrieval (מתוכנן):** Exact Search, Full-Text Search, Vector Search, Temporal filters, RRF, Deduplication ו-Reranking.

**Investigation Engine (מתוכנן):** Query Analysis, Search Plan, Dependency Expansion, Hypothesis Generation, Confidence calculation, Citation Validation ו-Recommendations.

**UI (מתוכנן):** Dashboard, Incident form, Investigation Workspace, Timeline, Evidence Viewer ו-Progress indication.

**Evaluation (מתוכנן):** Golden Dataset של לפחות 20 תרחישים, Metrics, השוואת גרסאות ודוח אוטומטי ב-CI עבור שינויים מהותיים ב-RAG.

**הקשחה והצגה (מתוכנן):** RBAC, Audit, Prompt Injection tests, Load tests, Documentation, Demo video, Architecture Decision Records ופקודת הרצה אחת.

### 8.2 סיכונים ודרכי התמודדות

**היקף גדול מדי:** חלוקה ל-MVP סגור הכולל שלושה שירותי דמו, שלושה עד חמישה תרחישים, מקור מסמכים אחד וחיפוש היברידי בסיסי. יכולות מתקדמות יתווספו רק לאחר תהליך מלא עובד.

**הזיות או ביטחון מזויף:** דרישת `evidence_id` לכל טענה, Citation Validator, הצגת מידע חסר וחישוב Confidence בקוד במקום בקשת אחוז שרירותי מהמודל.

**דליפת מידע:** סינון Authorization לפני Retrieval, Tenant scoping בכל Query, Redaction לפני אינדוקס ובדיקות Negative עבור משתמשים ללא הרשאה.

**Retrieval חלש:** Golden Dataset, מדידת Recall@K, השוואת Chunking ו-Embedding, Hybrid Search ו-Reranking.

**עלויות וזמן מודל:** Caching לתוצרים מתאימים, צמצום Context, הגבלת מספר Candidates, שמירת Token usage ויכולת שימוש במודל מקומי או Mock בבדיקות.

**נפח Logs:** Partitioning ו-Retention ב-PostgreSQL; הגדרת Benchmark ומסלול מעבר ל-ClickHouse רק לאחר הוכחת צורך.

**תלות בשירות חיצוני:** Provider Adapters, Timeouts, Retries, Circuit Breaker, Mock Providers ויכולת להריץ Evaluation ללא ספק חי.

**מורכבות Async:** כל תהליך ארוך ירוץ ב-Celery. Django Request יחזיר `202 Accepted` ומזהה Job; מצב עסקי יישמר ב-PostgreSQL.

**סחיפת סכמה:** שימוש ב-Django Migrations בלבד, בדיקת Migration ב-CI ואיסור יצירת טבלאות אוטומטית מחוץ למנגנון המיגרציות.

## 9. תכנית בדיקות

### 9.1 סוגי בדיקות

**Unit Tests:** בדיקת Domain services, Normalizers, Chunking, Rank Fusion, Confidence calculation, Permission policies, Citation mapping ו-Redaction.

**Integration Tests:** בדיקת Django מול PostgreSQL + pgvector, Celery ו-Redis, MinIO, OpenTelemetry ingestion ו-Mock AI Providers.

**Retrieval Tests:** בדיקת Exact, Full-Text, Vector ו-Hybrid Retrieval על Dataset קבוע, כולל Metadata filters והרשאות.

**RAG Evaluation:** בדיקת Recall@K, Root Cause Accuracy, Citation Correctness, Unsupported Claims, Answer completeness ו-Abstention כאשר אין מספיק מידע.

**E2E Tests:** פתיחת Incident, הרצת חקירה, צפייה בראיה, שאלת המשך, אישור Root Cause וסגירת Incident דרך Next.js.

**Security Tests:** בדיקת Tenant isolation, הרשאות אובייקט, CSRF, גישה לראיות מוגבלות, Prompt Injection, Secret redaction ו-Rate limiting.

**Performance Tests:** מדידת API, Ingestion, Retrieval וחקירה על Dataset בגודל היעד, תוך שמירת תוצאות Benchmark.

**Resilience Tests:** נפילת Redis, כשל ספק מודל, Timeout, מסמך פגום, Batch כפול וניתוק Object Storage.

### 9.2 קריטריוני קבלה

כל הנתיבים המוגנים דוחים משתמש שאינו מאומת או אינו מורשה.

משתמש מארגון אחד אינו יכול לאחזר, לצטט או לצפות בראיה מארגון אחר, גם באמצעות שינוי מזהה ידני.

Incident תקין יוצר Investigation Job ומחזיר Progress עד לתוצאה או כשל מוסבר.

בתרחיש הדמו `expired-token`, ההשערה המובילה מזהה את `auth-service` ואת שינוי `AUTH_REFRESH_TTL`, ומצטטת Log, Deployment ו-Code/Config change נדרשים.

כאשר אחת הראיות הקריטיות חסרה, המערכת אינה מציגה ביטחון גבוה ומציינת במפורש את המידע החסר.

כל ציטוט בתשובה נפתח למקור הקיים ונשמר ב-Investigation Snapshot.

הרצת אותו Ingestion Batch פעמיים אינה יוצרת רשומות כפולות.

Golden Dataset עומד ביעדי `Recall@5`, Root Cause Accuracy ו-Citation Correctness המוגדרים בסעיף 1.4.

המערכת ניתנת להרצה מקומית באמצעות פקודת Docker Compose מתועדת, לאחר הגדרת קובץ Environment לדוגמה.

## 10. פריסה ותחזוקה

### 10.1 סביבות

**Development:** הרצה מקומית ב-Docker Compose. Next.js במצב פיתוח, Django API, Celery Worker, PostgreSQL + pgvector, Redis ו-MinIO. מערכת הדמו ו-Observability יופעלו באמצעות Compose Profiles לפי הצורך.

**Test/CI:** שירותים זמניים ב-GitHub Actions עבור PostgreSQL ו-Redis, Mock AI Provider כברירת מחדל וסט קטן ודטרמיניסטי של Evaluation cases. בדיקות התלויות במודל חיצוני ירוצו בנפרד ולא יחסמו כל Pull Request ללא צורך.

**Staging/Demo:** Images בנויים מראש, Dataset סינתטי, Fault Injector ו-Secrets מנוהלים מחוץ ל-Repository. הסביבה תאפשר הדגמה מלאה ללא גישה למידע ארגוני אמיתי.

**Production עתידי:** פריסה מאובטחת מאחורי Reverse Proxy או Load Balancer, שירותי Web ו-Worker נפרדים, PostgreSQL מנוהל, Object Storage תואם S3, Secret Manager, TLS מלא, גיבויים, Retention ו-Observability. Production אינו חלק מחובת ה-MVP אך הארכיטקטורה לא תחסום אותו.

### 10.2 תחזוקה

גיבויים אוטומטיים ל-PostgreSQL ובדיקת שחזור תקופתית; גיבוי ללא בדיקת Restore לא ייחשב תקין.

Versioning ומדיניות Lifecycle ל-MinIO, כולל מחיקה מבוקרת של Artifacts ישנים.

ניטור Queue depth, Worker failures, Ingestion lag, Retrieval latency, LLM latency, Token usage, Citation failures ושגיאות הרשאה.

Health checks נפרדים ל-Liveness ול-Readiness עבור Web, Worker, Database, Redis ו-Object Storage.

מיגרציות Django ירוצו כשלב פריסה מבוקר ולא במקביל מכל Replica.

מדיניות Retention שונה ל-Logs, Traces, מסמכים, Audit ו-Investigation snapshots.

עדכון Dependencies באמצעות Pull Requests אוטומטיים, תוך הרצת Tests ו-Evaluation לפני Merge.

Runbook תפעולי עבור כשל Worker, ספק מודל לא זמין, אינדקס פגום, Queue backlog ושחזור Database.

## 11. סיכום והמלצות

### 11.1 סיכום

IncidentLens מיועדת להיות מערכת חקירת תקלות מבוססת ראיות עבור מערכות מבוזרות. היא מחברת בין Telemetry, Deployments, שינויי קוד וידע תפעולי, ומייצרת חקירה שקופה הכוללת Timeline, השערות מדורגות, ראיות תומכות וסותרות, מידע חסר והמלצות לבדיקות.

המערכת בנויה כ-Modular Monolith ב-Django עם מנוע RAG עצמאי ו-Workers אסינכרוניים. PostgreSQL + pgvector משמשים שכבת הנתונים המרכזית, Redis משמש לתורים ול-Cache, ו-MinIO שומר Artifacts מקוריים. סביבת Microservices סינתטית מספקת תרחישי תקלה עם Ground Truth ומאפשרת להוכיח את איכות המערכת במספרים.

### 11.2 המלצות

להתחיל ב-MVP מצומצם עם תרחיש `expired-token` אחד העובד מקצה לקצה לפני הרחבת מספר השירותים והמקורות.

לממש את מנוע ה-RAG כחבילת Python בלתי תלויה ב-Django, עם Interfaces ברורים ל-Database ולספקי AI.

לשמור את IncidentLens עצמו כ-Modular Monolith ולא לפצל אותו ל-Microservices לפני שקיים צורך מדיד.

לדרוש ציטוטים מובנים כבר בגרסה הראשונה ולא להוסיף אותם בדיעבד.

לבנות Golden Dataset במקביל לפיתוח התרחישים, כך שכל שיפור Retrieval או Prompt יימדד ולא יוערך רק לפי תחושה.

להשתמש ב-PostgreSQL + pgvector כמסד המרכזי ולדחות ClickHouse/OpenSearch לשלב שבו Benchmark יוכיח צורך.

להימנע מביצוע אוטומטי של פעולות Production בגרסה הראשונה ולהתמקד בחקירה ובהמלצות בטוחות.

### 11.3 הצעדים הבאים

אישור Scope ה-MVP והגדרת מה אינו נכלל בו.

בחירת תרחיש התקלה הראשון והגדרת Ground Truth ו-Required Evidence.

יצירת Architecture Decision Records עבור Django, PostgreSQL + pgvector, Celery וגישת Provider abstraction.

תכנון סכמת הנתונים הראשונית והגדרת Django Apps וממשקי Service layer.

הקמת Monorepo, Docker Compose ו-CI בסיסי.

פיתוח מערכת הדמו והפקת Logs, Traces ו-Deployment Events דטרמיניסטיים.

מימוש Ingestion וחיפוש היברידי לפני הוספת Hypothesis Generation.

בניית מסך Investigation Workspace והדגמת תהליך מלא אחד.

## 12. נספחים

### 12.1 תרשימי ארכיטקטורה

#### Development – Docker Compose

```text
Browser
  │
  │ HTTPS/HTTP + Django session cookie + CSRF
  ▼
Next.js Web (:3000)
  │
  │ REST /api/v1
  ▼
Django + DRF API (:8000)
  │
  ├── Django ORM ─────────────► PostgreSQL + pgvector (:5432)
  │                              [users / teams / incidents / evidence /
  │                               chunks / embeddings / evaluations]
  │
  ├── Queue jobs ─────────────► Redis (:6379) ─────► Celery Workers
  │                                                     │
  │                                                     ├── Ingestion
  │                                                     ├── Investigation
  │                                                     └── Evaluation
  │
  └── S3 API ─────────────────► MinIO (:9000)
                                 [documents / raw logs / trace exports]

Demo Microservices
  ├── Checkout Service
  ├── Payment Service
  ├── Auth Service
  └── Inventory Service
          │
          └── OTLP ───────────► OpenTelemetry Collector
                                   │
                                   ├──► IncidentLens Ingestion
                                   └──► Grafana / Prometheus / Tempo
```

#### Production עתידי

```text
Browser
  │
  ▼
Load Balancer / Reverse Proxy
  │
  ├──► Next.js Web replicas
  │
  └──► Django API replicas
          │
          ├──► Managed PostgreSQL + pgvector
          ├──► Managed Redis / Queue
          ├──► S3-compatible Object Storage
          └──► Celery Worker pools

OpenTelemetry Sources ──► Collector / Ingestion Gateway
AI requests ────────────► Approved model provider through Provider Adapter
```

### 12.2 מפרט טכני מפורט

המערכת תתבסס על Python ו-Django עבור Backend ו-Domain, Django REST Framework עבור API, Celery עבור Background jobs, PostgreSQL עם pgvector עבור מידע עסקי וחיפוש וקטורי, Redis עבור Broker ו-Cache, MinIO עבור Object Storage, ו-TypeScript עם Next.js עבור Frontend.

הפרויקט ינוהל כ-Monorepo ויכלול שלושה Deployables מרכזיים של המוצר: Web, API ו-Worker. מערכת הדמו תכלול Microservices נפרדים אך לא תהווה חלק מה-Domain של IncidentLens.

גרסאות Dependencies יינעלו בקובצי Lock ויעודכנו באופן מבוקר. מסמך האפיון לא יקבע מספר גרסה קשיח לספרייה שאינה חלק מחוזה עסקי, כדי למנוע התיישנות מיותרת.

החיפוש ההיברידי יתבסס על ארבעה ערוצים:

1. Exact Search עבור Error codes, Trace IDs, Versions ו-Commit SHAs.
2. PostgreSQL Full-Text Search עבור מילים ומונחים.
3. pgvector Similarity Search עבור משמעות סמנטית.
4. Temporal SQL עבור אירועים בטווח זמן וקרבה ל-Deployment.

התוצאות יאוחדו באמצעות Reciprocal Rank Fusion, יסוננו לפי הרשאות, יעברו Deduplication ויישלחו ל-Reranker. רק הראיות המדורגות ביותר ייכללו בהקשר למודל.

### 12.3 דוגמאות קוד

#### דוגמת מודל Incident ב-Django

```python
import uuid

from django.conf import settings
from django.db import models


class Incident(models.Model):
    class Severity(models.TextChoices):
        SEV1 = "sev1", "SEV 1"
        SEV2 = "sev2", "SEV 2"
        SEV3 = "sev3", "SEV 3"
        SEV4 = "sev4", "SEV 4"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey("accounts.Organization", on_delete=models.PROTECT)
    title = models.CharField(max_length=200)
    description = models.TextField()
    severity = models.CharField(max_length=10, choices=Severity.choices)
    environment = models.CharField(max_length=50)
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

#### דוגמת משימת חקירה ב-Celery

```python
from celery import shared_task

from incidentlens.investigations.services import InvestigationService


@shared_task(bind=True, autoretry_for=(TimeoutError,), retry_backoff=True, max_retries=3)
def run_investigation(self, investigation_id: str) -> None:
    InvestigationService().run(investigation_id=investigation_id)
```

#### דוגמת חיפוש וקטורי ב-PostgreSQL

```sql
SELECT
    dc.id,
    dc.content,
    ce.embedding <=> %(query_embedding)s AS distance
FROM document_chunks AS dc
JOIN chunk_embeddings AS ce ON ce.chunk_id = dc.id
WHERE dc.organization_id = %(organization_id)s
  AND dc.environment IN %(allowed_environments)s
  AND ce.model_name = %(embedding_model)s
ORDER BY ce.embedding <=> %(query_embedding)s
LIMIT 20;
```

#### דוגמת פלט השערה מובנה

```json
{
  "title": "Token refresh failure after auth deployment",
  "summary": "Expired authentication tokens were not refreshed after version 2.4.1 was deployed.",
  "supporting_evidence_ids": ["ev_log_318", "ev_deploy_42", "ev_diff_17"],
  "contradicting_evidence_ids": [],
  "missing_evidence": ["token-refresh-worker health metric"],
  "recommended_checks": [
    "Verify that token-refresh-worker is running",
    "Compare AUTH_REFRESH_TTL with the previous deployment"
  ],
  "confidence_band": "high"
}
```
