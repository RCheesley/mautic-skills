#!/usr/bin/env python3
"""Bucket harvested merged PRs by product area (from touched file paths, then title/labels), and write
compact per-bucket markdown corpora that analysis agents can read. Also writes a stats summary."""
import json, re, sys, os, collections
SRC, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)

PATH_RULES = [  # (regex on path, bucket)
    (r'app/bundles/LeadBundle/(Segment|Entity/LeadList|Entity/ListLead|Model/ListModel|Command/UpdateLeadListsCommand|Tests/.*Segment|Tests/.*ListModel|Tests/.*LeadList|Form/Type/(Filter|ListType|SegmentFilter))', 'segments'),
    (r'app/bundles/LeadBundle/', 'contacts'),
    (r'app/bundles/CampaignBundle/', 'campaigns'),
    (r'app/bundles/EmailBundle/', 'emails'),
    (r'app/bundles/FormBundle/', 'forms'),
    (r'app/bundles/(PageBundle|DynamicContentBundle)/', 'pages-tracking-dwc'),
    (r'app/bundles/(AssetBundle|CategoryBundle|ProjectBundle)/', 'assets-categories-projects'),
    (r'app/bundles/(PointBundle|StageBundle)/', 'points-stages'),
    (r'app/bundles/(ReportBundle|DashboardBundle|StatsBundle)/', 'reports-dashboard-stats'),
    (r'app/bundles/(ApiBundle|WebhookBundle)/', 'api-webhooks'),
    (r'app/bundles/UserBundle/', 'users-roles-auth'),
    (r'app/bundles/(ConfigBundle|InstallBundle)/|app/config/|config/', 'configuration-install'),
    (r'app/bundles/(ChannelBundle|SmsBundle|NotificationBundle)/|plugins/(MauticFocusBundle|MauticSocialBundle)/', 'channels'),
    (r'app/bundles/(IntegrationsBundle|PluginBundle|MarketplaceBundle)/', 'integrations-plugins-marketplace'),
    (r'app/bundles/(MessengerBundle|QueueBundle|CacheBundle)/', 'messenger-queue-cache'),
    (r'plugins/(GrapesJsBuilderBundle)/|themes/|templates/', 'builders-themes'),
    (r'plugins/', 'bundled-plugins'),
    (r'app/migrations/|UPGRADE-|app/release_metadata|app/bundles/CoreBundle/(Update|Release)/|SECURITY|MAINTAINERS|RELEASE_LEADS|patches/', 'migrations-upgrades-releases'),
    (r'app/bundles/CoreBundle/(Security|Command|Console|EventListener|Event|CoreEvents|IpLookup|Translation|Service|Shortener|Session|Monolog|ErrorHandler|ProcessSignal|Predis|Config)', 'core-platform'),
    (r'app/bundles/CoreBundle/Test/|\.github/|composer\.json|composer\.lock|package\.json|webpack|phpstan|rector|ecs\.php|codeception|tests/|\.ddev/|build/|bin/|Makefile|\.editorconfig|\.gitignore|utils/', 'dev-tooling-testing'),
    (r'app/bundles/CoreBundle/', 'core-foundation'),
    (r'translations/|Translations/', 'translations'),
    (r'\.md$|\.all-contributorsrc|\.github/ISSUE|README', 'docs-and-community'),
]
TITLE_RULES = [
    (r'segment|lead ?list|filter', 'segments'), (r'contact|lead|compan|custom field|import|dnc|do not contact', 'contacts'),
    (r'campaign', 'campaigns'), (r'email|mail|smtp|bounce|unsubscri', 'emails'), (r'\bform', 'forms'),
    (r'landing|page|track|cookie|mtc\.js|dwc|dynamic content', 'pages-tracking-dwc'), (r'asset|categor|project', 'assets-categories-projects'),
    (r'point|stage', 'points-stages'), (r'report|dashboard|widget|chart', 'reports-dashboard-stats'), (r'\bapi\b|webhook|oauth', 'api-webhooks'),
    (r'user|role|permission|login|password|saml|sso', 'users-roles-auth'), (r'config|install|setting', 'configuration-install'),
    (r'sms|notification|push|focus|social|twitter|channel|marketing message', 'channels'), (r'integration|plugin|marketplace|sync|salesforce|hubspot', 'integrations-plugins-marketplace'),
    (r'messenger|queue|cache|redis|rabbit', 'messenger-queue-cache'), (r'theme|builder|grapes|mjml|template', 'builders-themes'),
    (r'migration|upgrade|update|release|version|bump', 'migrations-upgrades-releases'), (r'test|phpstan|rector|ci\b|github action|workflow|cs\b|coding standard|deprecat|symfony|php 8|php8|composer|dependenc', 'dev-tooling-testing'),
    (r'translat|language|i18n', 'translations'), (r'contributor|readme|docs|documentation', 'docs-and-community'),
]
def clip(s, n):
    s = (s or '').strip()
    return s if len(s) <= n else s[:n] + f'\n…[truncated {len(s)-n} chars]'
def buckets_for(pr):
    counts = collections.Counter()
    for f in pr.get('files', {}).get('nodes', []) or []:
        p = f['path']; w = 1 + (f.get('additions',0)+f.get('deletions',0))**0.5
        for rx, b in PATH_RULES:
            if re.search(rx, p): counts[b] += w; break
    if not counts:
        t = pr['title'].lower()
        for rx, b in TITLE_RULES:
            if re.search(rx, t): counts[b] += 1; break
    if not counts: counts['uncategorised'] += 1
    top = counts.most_common(2)
    total = sum(counts.values())
    return [b for b, c in top if c/total >= 0.25] or [top[0][0]]
prs = [json.loads(l) for l in open(SRC)]
prs.sort(key=lambda p: p['number'])
by_bucket = collections.defaultdict(list); stats = collections.Counter(); chars = collections.Counter()
bot_authors = {'allcontributors', 'dependabot', 'github-actions', 'mautibot', 'transifex-integration'}
NOISE_TITLE = re.compile(r'^(bump (?!minimum)|chore\(deps|build\(deps|update dependency)|all.?contributors|^docs: add |coding standards?\b|\bcs[- ]fix|php-?cs-?fixer|\bfix(ed)? cs\b|\btypos?\b|phpstan baseline|^re-?run rector|type.?coverage|return.?array|mixed.?callers|ecs.?blink|\bcodecov\b|\bsonar\b|^ci:', re.I)
BOT_COMMENTERS = {'codecov','sonarcloud','github-actions','mautibot','coderabbitai','allcontributors','dependabot','netlify','stale','mergify'}
excluded = []
def is_noise(pr):
    a = ((pr.get('author') or {}).get('login') or '').lower().replace('[bot]','')
    if a in bot_authors or 'bot' in a and a != 'mautibot-human': return 'bot author'
    t = pr['title']
    branch = pr.get('headRefName') or ''
    if NOISE_TITLE.search(t): return 'mechanical/tooling title'
    if pr['baseRefName'] == '8.x' and a == 'tomasvotruba': return '8.x type-hardening refactor'
    return None
kept = []
for pr in prs:
    why = is_noise(pr)
    if why: excluded.append((pr['number'], why, pr['title'])); continue
    kept.append(pr)
prs = kept
for pr in prs:
    a = (pr.get('author') or {}).get('login') or ''
    if a.lower().replace('[bot]','') in bot_authors or pr['title'].startswith('docs: add ') and 'contributors' in pr['title']:
        by_bucket['bots'].append(pr); continue
    for b in buckets_for(pr): by_bucket[b].append(pr)
def render(pr):
    labels = ', '.join(n['name'] for n in pr['labels']['nodes'])
    files = [f['path'] for f in (pr.get('files',{}).get('nodes') or [])]
    issues = ', '.join(f"#{i['number']} {i['title']}" for i in pr['closingIssuesReferences']['nodes'])
    out = [f"## PR #{pr['number']}: {pr['title']}",
           f"- merged: {pr['mergedAt'][:10]} | base: {pr['baseRefName']} | author: {(pr.get('author') or {}).get('login')} | +{pr['additions']}/-{pr['deletions']} in {pr['changedFiles']} files | labels: {labels or '-'} | milestone: {(pr.get('milestone') or {}).get('title') or '-'}",
           f"- url: {pr['url']}"]
    if issues: out.append(f"- closes: {issues}")
    out.append(f"- files: {', '.join(files[:12])}{' …' if len(files) > 12 else ''}")
    body = re.sub(r'(?s)<!--.*?-->', '', pr.get('body') or '')
    if body.strip(): out.append("\n### Description\n" + clip(body, 2500))
    human = lambda x: ((x.get('author') or {}).get('login') or '').lower().replace('[bot]','') not in BOT_COMMENTERS
    rs = [r for r in pr['reviews']['nodes'] if (r.get('body') or '').strip() and human(r)]
    cs = [c for c in pr['comments']['nodes'] if human(c) and len((c.get('body') or '').strip()) > 15][:15]
    if rs or cs:
        out.append("\n### Discussion")
        for r in rs: out.append(f"- [review {r['state']}] {(r.get('author') or {}).get('login')}: {clip(r['body'], 700)}")
        for c in cs: out.append(f"- [{c['createdAt'][:10]}] {(c.get('author') or {}).get('login')}: {clip(c['body'], 700)}")
        
    return '\n'.join(out) + '\n\n'
MAX = 240_000  # chars per chunk (~110k tokens) so one agent can read a whole chunk
index = []
for b, lst in by_bucket.items():
    rendered = [render(p) for p in lst]
    chunks, cur, size = [], [], 0
    for p, r in zip(lst, rendered):
        if cur and size + len(r) > MAX:
            chunks.append(cur); cur, size = [], 0
        cur.append((p, r)); size += len(r)
    if cur: chunks.append(cur)
    os.makedirs(os.path.join(OUT, b), exist_ok=True)
    for i, ch in enumerate(chunks, 1):
        first, last = ch[0][0], ch[-1][0]
        name = f"{b}/chunk-{i:02d}-of-{len(chunks):02d}_{first['mergedAt'][:7]}_to_{last['mergedAt'][:7]}.md"
        text = f"# Merged PR corpus — bucket: {b}, chunk {i}/{len(chunks)} ({len(ch)} PRs, merged {first['mergedAt'][:10]} to {last['mergedAt'][:10]}, PR #{first['number']}–#{last['number']})\n\n" + ''.join(r for _, r in ch)
        open(os.path.join(OUT, name), 'w').write(text)
        index.append((b, name, len(ch), len(text)))
    stats[b] = len(lst); chars[b] = sum(len(r) for r in rendered)
with open(os.path.join(OUT, 'INDEX.tsv'), 'w') as f:
    for b, name, n, c in index: f.write(f"{b}\t{name}\t{n}\t{c}\n")
print(f"total PRs: {len(prs)}")
for b, n in stats.most_common(): print(f"{b:35s} {n:5d} PRs  {chars[b]/1000:8.0f} kchars ~{chars[b]//4000:5d}k tokens")

with open(os.path.join(OUT, 'EXCLUDED.tsv'), 'w') as f:
    for n, why, t in excluded: f.write(f"{n}\t{why}\t{t}\n")
print(f"excluded as noise: {len(excluded)}; kept: {len(prs)}")
