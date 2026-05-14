import Link from '@docusaurus/Link';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';
import type {ReactNode} from 'react';
import styles from './index.module.css';

const exampleBefore = `query = """
select user_id, updated_at
from users
qualify row_number() over(partition by user_id order by updated_at desc)=1
"""`;

const exampleAfter = `query = "sql/query.sql"`;

type CodeLanguage = 'python' | 'sql';

const sqlKeywords = new Set([
  'AS',
  'BY',
  'DESC',
  'FROM',
  'GROUP',
  'LIMIT',
  'ORDER',
  'OVER',
  'PARTITION',
  'QUALIFY',
  'ROW_NUMBER',
  'SELECT',
  'SUM',
  'WHERE',
]);

function tokenize(
  line: string,
  pattern: RegExp,
  getClassName: (token: string) => string | undefined,
) {
  const pieces: ReactNode[] = [];
  let lastIndex = 0;

  line.replace(pattern, (token, ...args) => {
    const offset = args[args.length - 2] as number;

    if (offset > lastIndex) {
      pieces.push(line.slice(lastIndex, offset));
    }

    const className = getClassName(token);
    pieces.push(className ? <span className={className} key={`${offset}-${token}`}>{token}</span> : token);
    lastIndex = offset + token.length;
    return token;
  });

  if (lastIndex < line.length) {
    pieces.push(line.slice(lastIndex));
  }

  return pieces;
}

function highlightSqlLine(line: string) {
  return tokenize(
    line,
    /--.*$|'[^']*'|\b[A-Z_]+\b|\b[a-z_]+\b|\b\d+\b/g,
    (token) => {
      if (token.startsWith('--')) return styles.codeComment;
      if (token.startsWith("'")) return styles.codeString;
      if (/^\d+$/.test(token)) return styles.codeNumber;
      if (sqlKeywords.has(token.toUpperCase())) return styles.codeKeyword;
      return undefined;
    },
  );
}

function highlightPythonLine(line: string, inSqlString: boolean) {
  if (inSqlString) {
    return highlightSqlLine(line);
  }

  return tokenize(
    line,
    /#.*$|"""|"[^"]*"|'[^']*'|\bquery\b|[=()]/g,
    (token) => {
      if (token.startsWith('#')) return styles.codeComment;
      if (token === '"""' || token.startsWith('"') || token.startsWith("'")) return styles.codeString;
      if (token === 'query') return styles.codeVariable;
      if (/^[=()]$/.test(token)) return styles.codeOperator;
      return undefined;
    },
  );
}

function PromptLine({children}: {children: ReactNode}) {
  return (
    <div className={styles.promptLine}>
      <span aria-hidden="true">$</span>
      <code>{children}</code>
    </div>
  );
}

function SyntaxBlock({
  language,
  children,
}: {
  language: CodeLanguage;
  children: string;
}) {
  let inSqlString = false;
  const lines = children.split('\n');

  return (
    <div className={styles.syntaxBlock}>
      <pre>
        <code>
          {lines.map((line, index) => {
            const delimiterLine = language === 'python' && line.includes('"""');
            const shouldHighlightAsSql = language === 'sql' || (inSqlString && !delimiterLine);
            const renderedLine = language === 'sql'
              ? highlightSqlLine(line)
              : highlightPythonLine(line, shouldHighlightAsSql);

            if (delimiterLine) {
              inSqlString = !inSqlString;
            }

            return (
              <span className={styles.codeLine} key={`${index}-${line}`}>
                {renderedLine}
                {index < lines.length - 1 ? '\n' : null}
              </span>
            );
          })}
        </code>
      </pre>
    </div>
  );
}

function HomepageHeader() {
  return (
    <header className={styles.hero}>
      <div className="container">
        <div className={styles.heroGrid}>
          <div className={styles.heroCopy}>
            <p className={styles.eyebrow}>Redshift-first Python SQL refactoring</p>
            <Heading as="h1" className={styles.heroTitle}>
              pyredsql
            </Heading>
            <p className={styles.heroSubtitle}>
              Format, audit, and extract long triple-quoted Redshift SQL strings
              from Python into readable, reviewable SQL files.
            </p>
            <div className={styles.actions}>
              <Link className="button button--primary button--lg" to="/docs/intro">
                Read the docs
              </Link>
              <Link className="button button--secondary button--lg" to="/docs/getting-started/quick-start">
                Quick start
              </Link>
            </div>
          </div>
          <div className={styles.preview} aria-label="pyredsql example">
            <div className={styles.previewTitle}>
              <span className={styles.previewKicker}>Example workflow</span>
              <strong>Extract embedded SQL from Python</strong>
            </div>
            <div className={styles.previewStep}>
              <span>Before</span>
              <strong>SQL lives inside Python</strong>
              <SyntaxBlock language="python">{exampleBefore}</SyntaxBlock>
            </div>
            <div className={styles.previewStep}>
              <span>Run</span>
              <PromptLine>pyredsql extract jobs/load_users.py --out-dir sql</PromptLine>
            </div>
            <div className={styles.previewStep}>
              <span>After</span>
              <strong>Python points to the SQL file</strong>
              <SyntaxBlock language="python">{exampleAfter}</SyntaxBlock>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}

const listRows = [
  {file: 'jobs/load_users.py:14', name: 'users_query', lines: '18 lines', status: 'safe'},
  {file: 'jobs/load_users.py:42', name: 'events_sql', lines: '24 lines', status: 'safe'},
  {file: 'jobs/sessions.py:11', name: 'sessions_query', lines: '31 lines', status: 'skip', reason: 'f-string'},
  {file: 'jobs/orders.py:67', name: 'orders_sql', lines: '12 lines', status: 'safe'},
  {file: 'jobs/cohorts.py:29', name: 'cohort_query', lines: '44 lines', status: 'skip', reason: 'jinja'},
];

const formatBefore = `query = """
select user_id,sum(amount) as total
from analytics.orders where
status='paid' group by 1
order by 2 desc limit 100
"""`;

const formatAfter = `query = """
SELECT
  user_id,
  SUM(amount) AS total
FROM analytics.orders
WHERE status = 'paid'
GROUP BY 1
ORDER BY 2 DESC
LIMIT 100
"""`;

const formatNotes = [
  'Uppercase keywords',
  'Expanded SELECT list',
  'Normalized WHERE and ORDER BY',
];

const extractBefore = `# jobs/load_users.py
query = """
  select user_id, updated_at
  from analytics.users
  qualify row_number() over(
    partition by user_id
    order by updated_at desc
  ) = 1
"""`;

const extractPythonAfter = `# jobs/load_users.py
query = "sql/load_users.sql"`;

const extractSqlAfter = `-- sql/load_users.sql
SELECT
  user_id,
  updated_at
FROM analytics.users
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY user_id
  ORDER BY updated_at DESC
) = 1`;

const extractNotes = [
  'Python keeps a small reference',
  'SQL moves into a reviewable file',
  'Formatting happens during extraction',
];

function TerminalListPreview() {
  return (
    <div className={styles.terminalPreview}>
      <PromptLine>pyredsql list jobs/</PromptLine>
      <div className={styles.resultTable} role="table" aria-label="pyredsql list output">
        {listRows.map((row) => (
          <div className={styles.resultRow} role="row" key={`${row.file}-${row.name}`}>
            <code className={styles.resultFile}>{row.file}</code>
            <code className={styles.resultName}>{row.name}</code>
            <span className={styles.resultLines}>{row.lines}</span>
            <span className={row.status === 'safe' ? styles.safePill : styles.skipPill}>
              {row.status}
              {row.reason ? <span> · {row.reason}</span> : null}
            </span>
          </div>
        ))}
      </div>
      <div className={styles.resultSummary}>
        <strong>Found 5 blocks</strong>
        <span>3 safe</span>
        <span>2 skipped</span>
      </div>
    </div>
  );
}

function CodePane({
  label,
  filename,
  language,
  children,
}: {
  label: string;
  filename: string;
  language: CodeLanguage;
  children: string;
}) {
  return (
    <div className={styles.codePane}>
      <div className={styles.codePaneHeader}>
        <span>{label}</span>
        <code>{filename}</code>
      </div>
      <SyntaxBlock language={language}>{children}</SyntaxBlock>
    </div>
  );
}

type CodePaneData = {
  label: string;
  filename: string;
  language: CodeLanguage;
  code: string;
};

function BeforeAfterPreview({
  beforeBlock,
  afterBlocks,
  notes,
}: {
  beforeBlock: CodePaneData;
  afterBlocks: CodePaneData[];
  notes: string[];
}) {
  return (
    <div className={styles.beforeAfterPreview}>
      <div className={styles.previewSplit}>
        <CodePane
          label={beforeBlock.label}
          filename={beforeBlock.filename}
          language={beforeBlock.language}>
          {beforeBlock.code}
        </CodePane>
        <div className={styles.previewArrow} aria-hidden="true">→</div>
        <div className={styles.afterStack}>
          {afterBlocks.map((block) => (
            <CodePane
              key={`${block.filename}-${block.label}`}
              label={block.label}
              filename={block.filename}
              language={block.language}>
              {block.code}
            </CodePane>
          ))}
        </div>
      </div>
      <ul className={styles.changeNotes}>
        {notes.map((note) => (
          <li key={note}>{note}</li>
        ))}
      </ul>
    </div>
  );
}

function FeatureList() {
  const items = [
    {
      step: '01',
      title: 'Find embedded SQL',
      body: 'Scan Python files for triple-quoted strings that look like SQL. pyredsql combines SQL-like keywords with common variable names such as query, sql, *_query, and *_sql, and reports which blocks are safe to act on and which are skipped.',
      command: 'pyredsql list jobs/',
      previewLabel: 'Example output',
      preview: (
        <TerminalListPreview />
      ),
    },
    {
      step: '02',
      title: 'Format safely',
      body: 'Re-format Redshift SQL through SQLGlot while keeping runtime-sensitive strings untouched. f-strings and Jinja-like templates are detected, reported, and skipped by default. Use --dry-run to preview, or --check in CI.',
      command: 'pyredsql format jobs/load_users.py --dry-run',
      previewLabel: 'Before → After',
      preview: (
        <BeforeAfterPreview
          beforeBlock={{
            label: 'Before',
            filename: 'jobs/load_users.py',
            language: 'python',
            code: formatBefore,
          }}
          afterBlocks={[
            {
              label: 'After',
              filename: 'preview only',
              language: 'python',
              code: formatAfter,
            },
          ]}
          notes={formatNotes}
        />
      ),
    },
    {
      step: '03',
      title: 'Extract to .sql',
      body: 'Move large embedded queries into external .sql files. The Python side is replaced with a path string (or a Path(...).read_text() call when that fits), and the formatted SQL lives in a real, reviewable file.',
      command: 'pyredsql extract jobs/load_users.py --out-dir sql',
      previewLabel: 'Before → After',
      preview: (
        <BeforeAfterPreview
          beforeBlock={{
            label: 'Before',
            filename: 'jobs/load_users.py',
            language: 'python',
            code: extractBefore,
          }}
          afterBlocks={[
            {
              label: 'After',
              filename: 'jobs/load_users.py',
              language: 'python',
              code: extractPythonAfter,
            },
            {
              label: 'New SQL file',
              filename: 'sql/load_users.sql',
              language: 'sql',
              code: extractSqlAfter,
            },
          ]}
          notes={extractNotes}
        />
      ),
    },
  ];

  return (
    <section className={styles.features}>
      <div className="container">
        <div className={styles.sectionHeader}>
          <Heading as="h2">Built for practical cleanup work</Heading>
          <p>pyredsql is a refactoring tool, not a database client. It never connects to Redshift or executes SQL. Each command shows you exactly what it will change — before it changes anything.</p>
        </div>
        <div className={styles.featureList}>
          {items.map((item) => (
            <article className={styles.featureItem} key={item.title}>
              <div className={styles.featureHeader}>
                <div className={styles.stepBadge}>{item.step}</div>
                <div className={styles.featureBody}>
                  <Heading as="h3">{item.title}</Heading>
                  <p>{item.body}</p>
                </div>
              </div>
              <div className={styles.command}>
                <span>Run</span>
                <PromptLine>{item.command}</PromptLine>
              </div>
              <div className={styles.featurePreview} aria-label={`${item.title} example`}>
                <div className={styles.featurePreviewHeader}>{item.previewLabel}</div>
                <div className={styles.featurePreviewBody}>{item.preview}</div>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

export default function Home(): JSX.Element {
  return (
    <Layout
      title="pyredsql"
      description="Format and extract Redshift SQL embedded in Python files.">
      <HomepageHeader />
      <FeatureList />
    </Layout>
  );
}
