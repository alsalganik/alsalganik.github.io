import json
from collections import Counter, defaultdict
from html import escape
from pathlib import Path

from site_data import (
    AWARDS,
    EDUCATION,
    EXPERIENCE,
    GRANTS,
    OBSERVING_PROGRAMS,
    PRESS,
    PUBLICATIONS,
    SERVICE,
    SITE,
    TALKS,
    TOPICS,
)


ROOT = Path(__file__).resolve().parents[1]
BUILD_DATE = SITE["updated"]
TOPIC_BY_SLUG = {topic["slug"]: topic for topic in TOPICS}
PUBLICATION_BY_SLUG = {publication["slug"]: publication for publication in PUBLICATIONS}
NAV_ITEMS = [
    ("/", "Home"),
    ("/publications/", "Publications"),
    ("/cv/", "CV"),
    ("/contact/", "Contact"),
]


def page_url(path):
    if path == "/":
        return SITE["domain"] + "/"
    return SITE["domain"] + path


def write_page(path, content):
    destination = ROOT / path.lstrip("/")
    if path.endswith("/"):
        destination = destination / "index.html"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")


def attrs(**kwargs):
    bits = []
    for key, value in kwargs.items():
        if value is None:
            continue
        bits.append(f'{key}="{escape(str(value), quote=True)}"')
    return " ".join(bits)


def external_link(url, label):
    return (
        f'<a href="{escape(url, quote=True)}" target="_blank" '
        f'rel="noopener noreferrer">{escape(label)}</a>'
    )


def paragraph(text):
    return f"<p>{escape(text)}</p>"


def format_authors(authors):
    return ", ".join(authors)


def breadcrumb_html(items):
    crumbs = []
    for label, path in items[:-1]:
        crumbs.append(f'<a href="{escape(path, quote=True)}">{escape(label)}</a>')
    crumbs.append(escape(items[-1][0]))
    return " / ".join(crumbs)


def person_json_ld():
    return {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": SITE["name"],
        "givenName": "Alexander",
        "familyName": "Salganik",
        "jobTitle": SITE["job_title"],
        "description": SITE["description"],
        "url": page_url("/"),
        "image": page_url("/photo.jpg"),
        "email": [f"mailto:{entry['address']}" for entry in SITE["emails"]],
        "affiliation": {
            "@type": "CollegeOrUniversity",
            "name": SITE["institution"],
            "url": SITE["institution_url"],
        },
        "alumniOf": {"@type": "CollegeOrUniversity", "name": SITE["alumni_of"]},
        "sameAs": [SITE["orcid"], SITE["university_profile"]],
        "knowsAbout": [topic["name"] for topic in TOPICS],
    }


def breadcrumb_json_ld(items):
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": index + 1,
                "name": label,
                "item": page_url(path),
            }
            for index, (label, path) in enumerate(items)
        ],
    }


def website_json_ld():
    return {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": SITE["name"],
        "url": page_url("/"),
        "description": SITE["description"],
    }


def collection_json_ld(name, path, urls):
    return {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": name,
        "url": page_url(path),
        "isPartOf": website_json_ld(),
        "mainEntity": {
            "@type": "ItemList",
            "itemListElement": [
                {"@type": "ListItem", "position": index + 1, "url": page_url(url)}
                for index, url in enumerate(urls)
            ],
        },
    }


def publication_json_ld(publication, path):
    return {
        "@context": "https://schema.org",
        "@type": "ScholarlyArticle",
        "headline": publication["title"],
        "name": publication["title"],
        "url": page_url(path),
        "datePublished": str(publication["year"]),
        "isPartOf": {
            "@type": "Periodical",
            "name": publication["journal"],
        },
        "author": [{"@type": "Person", "name": author} for author in publication["authors"]],
        "identifier": publication["doi"],
        "sameAs": publication["url"],
        "about": [TOPIC_BY_SLUG[slug]["name"] for slug in publication["topics"] if slug in TOPIC_BY_SLUG],
        "description": publication["summary"],
        "image": page_url("/photo.jpg"),
    }


def sorted_publications():
    return sorted(PUBLICATIONS, key=lambda item: (item["year"], item["title"]), reverse=True)


def sorted_talks():
    return sorted(TALKS, key=lambda item: item["sort_date"], reverse=True)


def programs_by_facility():
    grouped = defaultdict(list)
    for program in sorted(OBSERVING_PROGRAMS, key=lambda item: (item["year"], item["title"]), reverse=True):
        grouped[program["facility"]].append(program)
    return grouped


def related_publications(topic_slug):
    return [
        publication
        for publication in sorted_publications()
        if topic_slug in publication["topics"]
    ]


def related_talks(topic_slug=None, publication_slug=None):
    items = []
    for talk in sorted_talks():
        if publication_slug and talk.get("publication_slug") == publication_slug:
            items.append(talk)
        elif topic_slug and topic_slug in talk.get("topics", []):
            items.append(talk)
    return items


def related_programs(topic_slug):
    return [
        program
        for program in sorted(OBSERVING_PROGRAMS, key=lambda item: (item["year"], item["title"]), reverse=True)
        if topic_slug in program["topics"]
    ]


def topic_link(slug):
    topic = TOPIC_BY_SLUG[slug]
    return f'<a href="/research/{escape(slug, quote=True)}/">{escape(topic["name"])}</a>'


def publication_path(publication):
    return f"/publications/{publication['slug']}/"


def render_head(title, description, path, *, keywords=None, json_ld=None, og_type="website"):
    metadata_keywords = list(SITE["keywords"])
    if keywords:
        metadata_keywords.extend(keywords)
    metadata_keywords = sorted(dict.fromkeys(metadata_keywords))
    structured_data = "\n".join(
        f'<script type="application/ld+json">{json.dumps(item, ensure_ascii=False)}</script>'
        for item in (json_ld or [])
    )
    canonical = page_url(path)
    return f"""<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{escape(title)}</title>
<meta name="description" content="{escape(description, quote=True)}" />
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1" />
<meta name="author" content="{escape(SITE['name'], quote=True)}" />
<meta name="keywords" content="{escape(', '.join(metadata_keywords), quote=True)}" />
<link rel="canonical" href="{escape(canonical, quote=True)}" />
<link rel="alternate" hreflang="en" href="{escape(canonical, quote=True)}" />
<link rel="preload" as="image" href="/photo.jpg" />
<link rel="sitemap" type="application/xml" href="{escape(page_url('/sitemap.xml'), quote=True)}" />
<meta name="theme-color" content="#f8fafc" />
<meta property="og:locale" content="en_US" />
<meta property="og:title" content="{escape(title, quote=True)}" />
<meta property="og:description" content="{escape(description, quote=True)}" />
<meta property="og:type" content="{escape(og_type, quote=True)}" />
<meta property="og:url" content="{escape(canonical, quote=True)}" />
<meta property="og:image" content="{escape(page_url('/photo.jpg'), quote=True)}" />
<meta property="og:image:alt" content="Portrait of Alexander Salganik, astrophysicist" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{escape(title, quote=True)}" />
<meta name="twitter:description" content="{escape(description, quote=True)}" />
<meta name="twitter:image" content="{escape(page_url('/photo.jpg'), quote=True)}" />
<meta name="twitter:image:alt" content="Portrait of Alexander Salganik, astrophysicist" />
<link rel="icon" type="image/svg+xml" href="/assets/favicon.svg" />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
<link rel="stylesheet" href="/assets/style.css" />
{structured_data}
</head>"""


def render_header(active_path, hero=False):
    nav_items = []
    for path, label in NAV_ITEMS:
        current_attr = " aria-current='page'" if path == active_path else ""
        nav_items.append(
            f'<a href="{escape(path, quote=True)}"{current_attr}>{escape(label)}</a>'
        )
    nav = "".join(nav_items)
    hero_markup = ""
    if hero:
        hero_markup = f"""
<section class="hero">
  <img src="/photo.jpg" alt="Alexander Salganik, PhD researcher in astrophysics" width="188" height="188" fetchpriority="high" />
  <div>
    <h1>{escape(SITE['name'])}</h1>
    <p class="subtitle">{escape(SITE['job_title'])} — {escape(SITE['institution'])}, {escape(SITE['location'])}</p>
    <address class="actions" style="font-style:normal">
      <a class="btn primary" href="/cv/Alexander_Salganik_CV.pdf" type="application/pdf" download>Download CV (PDF)</a>
      <a class="btn" href="mailto:{escape(SITE['emails'][0]['address'], quote=True)}">{escape(SITE['emails'][0]['address'])}</a>
      <a class="btn" href="{escape(SITE['orcid'], quote=True)}" rel="me noopener noreferrer" target="_blank">ORCID</a>
    </address>
  </div>
</section>"""
    return f"""
<a class="skip-link" href="#content">Skip to content</a>
<header class="site-header">
  <div class="container">
    <div class="topbar">
      <nav class="nav" aria-label="Primary navigation">{nav}</nav>
    </div>
    {hero_markup}
  </div>
</header>"""


def render_footer():
    return f"""
<footer class="site-footer">
  <div class="container">
    <div class="small">© 2026 {escape(SITE['name'])}. All rights reserved.</div>
  </div>
</footer>"""


def render_layout(title, description, path, body, *, keywords=None, json_ld=None, og_type="website", active_path="/", hero=False):
    return f"""<!doctype html>
<html lang="en" prefix="og: https://ogp.me/ns#">
{render_head(title, description, path, keywords=keywords, json_ld=json_ld, og_type=og_type)}
<body>
{render_header(active_path, hero=hero)}
{body}
{render_footer()}
</body>
</html>
"""


def publication_cards(publications, heading_level=3):
    cards = []
    for publication in publications:
        topics = "".join(topic_link(slug) for slug in publication["topics"] if slug in TOPIC_BY_SLUG)
        cards.append(
            f"""
<a class="card feature-link publication-card" href="{escape(publication_path(publication), quote=True)}">
  <div class="eyebrow">{escape(publication['date_label'])} · {escape(publication['journal_short'])}</div>
  <h{heading_level}>{escape(publication['title'])}</h{heading_level}>
  <p>{escape(publication['summary'])}</p>
  <div class="topic-row">{topics}</div>
</a>"""
        )
    return "".join(cards)


def topic_cards(topics, heading_level=3):
    cards = []
    for topic in topics:
        publication_count = len(related_publications(topic["slug"]))
        talk_count = len(related_talks(topic_slug=topic["slug"]))
        cards.append(
            f"""
<a class="card feature-link topic-card" href="/research/{escape(topic['slug'], quote=True)}/">
  <div class="eyebrow">Research area</div>
  <h{heading_level}>{escape(topic['name'])}</h{heading_level}>
  <p>{escape(topic['short_description'])}</p>
  <div class="muted small">{publication_count} publications · {talk_count} talks</div>
</a>"""
        )
    return "".join(cards)


def talk_items(talks, show_publication=True):
    rows = []
    for talk in talks:
        meta = ""
        if show_publication and talk.get("publication_slug"):
            publication = PUBLICATION_BY_SLUG[talk["publication_slug"]]
            meta = (
                f'<p class="muted small">Related publication: '
                f'<a href="{escape(publication_path(publication), quote=True)}">{escape(publication["title"])}</a></p>'
            )
        rows.append(
            f"""
<div class="card stacked-card">
  <div class="row">
    <div class="item-main">
      <b>{escape(talk['title'])}</b>
      <div class="muted">{escape(talk['event'])}</div>
      {meta}
    </div>
    <div class="item-meta"><span class="date-badge">{escape(talk['date_label'])}</span></div>
  </div>
</div>"""
        )
    return "".join(rows)


def program_items(programs):
    rows = []
    for program in programs:
        topic_bits = "".join(topic_link(slug) for slug in program["topics"] if slug in TOPIC_BY_SLUG)
        program_meta = " · ".join(
            escape(part)
            for part in [program["role"], program.get("program_type", "Observing program")]
            if part
        )
        rows.append(
            f"""
<div class="card stacked-card">
  <div class="row">
    <div class="item-main">
      <b>{escape(program['facility'])}</b>
      <div>{escape(program['title'])}</div>
      <div class="muted small">{program_meta}</div>
      <div class="topic-row">{topic_bits}</div>
    </div>
    <div class="item-meta"><span class="date-badge">{escape(program['date_label'])}</span></div>
  </div>
</div>"""
        )
    return "".join(rows)


def build_home():
    publications = sorted_publications()
    talks = sorted_talks()
    latest = publications[0]
    body = f"""
<main id="content" class="container">
  <section class="section">
    <div class="home-overview">
      <div class="overview-copy">
        <div class="eyebrow">Academic profile</div>
        <h2 class="section-title">Research overview</h2>
        {paragraph(SITE['hero_summary'])}
        {paragraph(SITE['research_summary'])}
        <div class="topic-row">
          {''.join(topic_link(slug) for slug in ['x-ray-pulsars', 'accreting-neutron-stars', 'x-ray-timing', 'x-ray-spectroscopy', 'x-ray-polarimetry'])}
        </div>
        <div class="profile-note">
          <p class="muted small">Site updated: <time datetime="{escape(SITE['updated'], quote=True)}">{escape(SITE['updated'])}</time></p>
          {paragraph(SITE['collaboration_summary'])}
          <nav class="quick-links" aria-label="More information">
            <a href="/publications/">Publications</a>
            <a href="/cv/">CV</a>
            <a href="/contact/">Contact</a>
          </nav>
        </div>
      </div>
      <aside class="latest-card" aria-labelledby="latest-publication-title">
        <div class="eyebrow">Latest publication</div>
        <h2 id="latest-publication-title">{escape(latest['title'])}</h2>
        <p class="muted"><i>{escape(latest['journal'])}</i> {escape(latest['volume'])}, {escape(latest['page'])} · {escape(latest['date_label'])}</p>
        <p>{escape(latest['summary'])}</p>
        <div class="actions">
          <a class="btn primary" href="{escape(publication_path(latest), quote=True)}">Read publication page</a>
          <a class="btn" href="{escape(latest['url'], quote=True)}" rel="noopener noreferrer" target="_blank">DOI</a>
        </div>
      </aside>
    </div>
  </section>

  <section class="stats-grid" aria-label="Site highlights">
    <a class="stat-card" href="/publications/">
      <strong>{len(publications)}</strong>
      <span>First-author papers</span>
      <small>Research papers in Astronomy &amp; Astrophysics and MNRAS.</small>
    </a>
    <a class="stat-card" href="/observing-programs/">
      <strong>{len(OBSERVING_PROGRAMS)}</strong>
      <span>PI observing programs</span>
      <small>NuSTAR, IXPE, Insight-HXMT, and Swift programs.</small>
    </a>
    <a class="stat-card" href="/talks/">
      <strong>{len(talks)}</strong>
      <span>Talks and invited presentations</span>
      <small>Conference and workshop material connected to the publication record.</small>
    </a>
  </section>

  <section class="section" id="featured-publications">
    <h2 class="section-title">Featured publications</h2>
    <p class="lead">Recent first-author papers on X-ray pulsars and accreting neutron stars.</p>
    <div class="grid three">
      {publication_cards(publications[:3])}
    </div>
  </section>

  <section class="section" id="activity">
    <div class="grid two">
      <div>
        <h2 class="section-title">Selected observing programs</h2>
        <p class="lead">PI programs across NuSTAR, IXPE, Insight-HXMT, and Swift.</p>
        <div class="stacked-list">
          {program_items(sorted(OBSERVING_PROGRAMS, key=lambda item: (item['year'], item['title']), reverse=True)[:4])}
        </div>
        <p><a href="/observing-programs/">All observing programs</a></p>
      </div>
      <div>
        <h2 class="section-title">Recent talks</h2>
        <p class="lead">Talks tied directly to publication outcomes and current methods work.</p>
        <div class="stacked-list">
          {talk_items(talks[:4])}
        </div>
        <p><a href="/talks/">All talks</a></p>
      </div>
    </div>
  </section>
</main>"""
    json_ld = [person_json_ld(), website_json_ld()]
    return render_layout(
        f"{SITE['name']} — {SITE['headline']}",
        (
            f"{SITE['name']} is a high-energy astrophysicist at the "
            f"{SITE['institution']} working on X-ray pulsars, accreting neutron "
            "stars, timing, spectroscopy, and X-ray polarimetry."
        ),
        "/",
        body,
        keywords=["research overview", "academic profile", "observing programs", "publications"],
        json_ld=json_ld,
        og_type="profile",
        active_path="/",
        hero=True,
    )


def build_research_index():
    path = "/research/"
    body = f"""
<main id="content" class="container">
  <div class="page-title">
    <div class="breadcrumbs">{breadcrumb_html([('Home', '/'), ('Research', '/research/')])}</div>
    <h1>Research</h1>
    <p class="lead">Topic pages for X-ray pulsars, accretion, timing, spectroscopy, polarimetry, and high-mass X-ray binaries.</p>
  </div>

  <section class="section">
    <p>{escape(SITE['research_summary'])}</p>
    <div class="grid three">
      {topic_cards(TOPICS)}
    </div>
  </section>
</main>"""
    json_ld = [
        person_json_ld(),
        breadcrumb_json_ld([("Home", "/"), ("Research", path)]),
        collection_json_ld("Research topics", path, [f"/research/{topic['slug']}/" for topic in TOPICS]),
    ]
    return render_layout(
        "Research | Alexander Salganik",
        "Research topics covered on salganik.me, including X-ray pulsars, accreting neutron stars, timing, spectroscopy, polarimetry, and high-mass X-ray binaries.",
        path,
        body,
        keywords=["research topics", "X-ray pulsars", "neutron stars"],
        json_ld=json_ld,
        active_path="/research/",
    )


def build_topic_page(topic):
    path = f"/research/{topic['slug']}/"
    publications = related_publications(topic["slug"])
    talks = related_talks(topic_slug=topic["slug"])
    programs = related_programs(topic["slug"])
    body = f"""
<main id="content" class="container">
  <div class="page-title">
    <div class="breadcrumbs">{breadcrumb_html([('Home', '/'), ('Research', '/research/'), (topic['name'], path)])}</div>
    <h1>{escape(topic['name'])}</h1>
    <p class="lead">{escape(topic['short_description'])}</p>
  </div>

  <section class="section">
    <div class="grid two article-layout">
      <div>
        <p>{escape(topic['overview'])}</p>
        <h2 class="section-title">Focus on this site</h2>
        <ul class="feature-list">
          {''.join(f'<li>{escape(point)}</li>' for point in topic['focus_points'])}
        </ul>
      </div>
      <aside class="card article-aside">
        <h2>At a glance</h2>
        <ul class="compact-list">
          <li>{len(publications)} related publications</li>
          <li>{len(talks)} related talks</li>
          <li>{len(programs)} related observing programs</li>
        </ul>
      </aside>
    </div>
  </section>

  <section class="section">
    <h2 class="section-title">Related publications</h2>
    <div class="grid two">
      {publication_cards(publications, heading_level=3)}
    </div>
  </section>

  <section class="section">
    <div class="grid two">
      <div>
        <h2 class="section-title">Related talks</h2>
        <div class="stacked-list">
          {talk_items(talks[:6], show_publication=False) if talks else '<p class="muted">No talks connected to this topic are listed yet.</p>'}
        </div>
      </div>
      <div>
        <h2 class="section-title">Related observing programs</h2>
        <div class="stacked-list">
          {program_items(programs[:6]) if programs else '<p class="muted">No observing programs connected to this topic are listed yet.</p>'}
        </div>
      </div>
    </div>
  </section>
</main>"""
    json_ld = [
        person_json_ld(),
        breadcrumb_json_ld([("Home", "/"), ("Research", "/research/"), (topic["name"], path)]),
        collection_json_ld(topic["name"], path, [publication_path(publication) for publication in publications]),
    ]
    return render_layout(
        f"{topic['name']} | Alexander Salganik",
        f"{topic['name']} research by Alexander Salganik, with related publications, talks, and observing programs.",
        path,
        body,
        keywords=[topic["name"], "research", "publications"],
        json_ld=json_ld,
        active_path="/research/",
    )


def build_publications_index():
    path = "/publications/"
    publications = sorted_publications()
    list_items = []
    for publication in publications:
        topic_bits = "".join(topic_link(slug) for slug in publication["topics"] if slug in TOPIC_BY_SLUG)
        list_items.append(
            f"""
<li id="{escape(publication['slug'], quote=True)}" class="list-row">
  <div class="item-main">
    <b><a href="{escape(publication_path(publication), quote=True)}">{escape(publication['title'])}</a></b><br />
    <span class="muted">{escape(format_authors(publication['authors']))}</span><br />
    <i>{escape(publication['journal_short'])}</i> {escape(publication['volume'])}, {escape(publication['page'])}. 
    <a href="{escape(publication['url'], quote=True)}" rel="noopener noreferrer" target="_blank">DOI</a>
    <p>{escape(publication['summary'])}</p>
    <div class="topic-row">{topic_bits}</div>
  </div>
  <div class="item-meta"><span class="date-badge">{escape(publication['date_label'])}</span></div>
</li>"""
        )
    body = f"""
<main id="content" class="container">
  <div class="page-title">
    <div class="breadcrumbs">{breadcrumb_html([('Home', '/'), ('Publications', path)])}</div>
    <h1>Publications</h1>
    <p class="lead">First-author publications on X-ray pulsars, high-mass X-ray binaries, timing transitions, and X-ray polarization.</p>
  </div>

  <section class="section">
    <div class="grid three">
      {publication_cards(publications[:3])}
    </div>
  </section>

  <section class="section" id="publications-list">
    <h2 class="section-title">All first-author papers</h2>
    <ol class="pub">
      {''.join(list_items)}
    </ol>
  </section>
</main>"""
    json_ld = [
        person_json_ld(),
        breadcrumb_json_ld([("Home", "/"), ("Publications", path)]),
        collection_json_ld("First-author publications", path, [publication_path(publication) for publication in publications]),
    ]
    return render_layout(
        "Publications | Alexander Salganik",
        "First-author publications by Alexander Salganik on X-ray pulsars, accreting neutron stars, high-mass X-ray binaries, timing transitions, and X-ray polarization.",
        path,
        body,
        keywords=["publications", "first-author papers", "DOI"],
        json_ld=json_ld,
        active_path="/publications/",
    )


def build_publication_page(publication):
    path = publication_path(publication)
    talks = related_talks(publication_slug=publication["slug"])
    related_topics_markup = "".join(topic_link(slug) for slug in publication["topics"] if slug in TOPIC_BY_SLUG)
    facility_markup = "".join(f"<li>{escape(facility)}</li>" for facility in publication["facilities"])
    highlights_markup = "".join(f"<li>{escape(item)}</li>" for item in publication["highlights"])
    body = f"""
<main id="content" class="container">
  <div class="page-title">
    <div class="breadcrumbs">{breadcrumb_html([('Home', '/'), ('Publications', '/publications/'), (publication['title'], path)])}</div>
    <h1>{escape(publication['title'])}</h1>
    <p class="lead">{escape(publication['summary'])}</p>
  </div>

  <section class="section">
    <div class="grid two article-layout">
      <div>
        <h2 class="section-title">Citation</h2>
        <p><b>{escape(format_authors(publication['authors']))}</b></p>
        <p><i>{escape(publication['journal'])}</i> {escape(publication['volume'])}, {escape(publication['page'])} ({escape(publication['date_label'])}).</p>
        <p><a href="{escape(publication['url'], quote=True)}" rel="noopener noreferrer" target="_blank">View DOI record</a></p>

        <h2 class="section-title">Summary</h2>
        <p>{escape(publication['summary'])}</p>
        <ul class="feature-list">{highlights_markup}</ul>
      </div>
      <aside class="card article-aside">
        <h2>At a glance</h2>
        <p><b>Journal:</b> {escape(publication['journal_short'])}</p>
        <p><b>Year:</b> {escape(publication['date_label'])}</p>
        <p><b>Facilities:</b></p>
        <ul>{facility_markup}</ul>
        <p><b>Research areas:</b></p>
        <div class="topic-row">{related_topics_markup}</div>
      </aside>
    </div>
  </section>

  <section class="section">
    <div class="grid two">
      <div>
        <h2 class="section-title">Related talks</h2>
        <div class="stacked-list">
          {talk_items(talks, show_publication=False) if talks else '<p class="muted">No talks connected to this publication are listed yet.</p>'}
        </div>
      </div>
      <div>
        <h2 class="section-title">Related research areas</h2>
        <div class="grid">
          {topic_cards([TOPIC_BY_SLUG[slug] for slug in publication['topics'] if slug in TOPIC_BY_SLUG], heading_level=3)}
        </div>
      </div>
    </div>
  </section>
</main>"""
    json_ld = [
        person_json_ld(),
        breadcrumb_json_ld([("Home", "/"), ("Publications", "/publications/"), (publication["title"], path)]),
        publication_json_ld(publication, path),
    ]
    return render_layout(
        f"{publication['title']} | Alexander Salganik",
        publication["summary"],
        path,
        body,
        keywords=[
            *(TOPIC_BY_SLUG[slug]["name"] for slug in publication["topics"] if slug in TOPIC_BY_SLUG),
            *publication["facilities"],
        ],
        json_ld=json_ld,
        og_type="article",
        active_path="/publications/",
    )


def build_observing_programs_page():
    path = "/observing-programs/"
    grouped = programs_by_facility()
    facility_counts = Counter(program["facility"] for program in OBSERVING_PROGRAMS)
    facility_slugs = {
        facility: facility.lower().replace(" ", "-")
        for facility in grouped
    }
    facility_cards = "".join(
        f"""
<div class="card">
  <h2>{escape(facility)}</h2>
  <p class="muted">{count} PI programs</p>
</div>"""
        for facility, count in facility_counts.items()
    )
    facility_sections = []
    for facility, programs in grouped.items():
        facility_sections.append(
            f"""
<section class="section" id="{escape(facility_slugs[facility], quote=True)}">
  <h2 class="section-title">{escape(facility)}</h2>
  <div class="stacked-list">
    {program_items(programs)}
  </div>
</section>"""
        )
    body = f"""
<main id="content" class="container">
  <div class="page-title">
    <div class="breadcrumbs">{breadcrumb_html([('Home', '/'), ('Observing Programs', path)])}</div>
    <h1>Observing Programs</h1>
    <p class="lead">Accepted PI observing proposals across NuSTAR, IXPE, Insight-HXMT, and Swift.</p>
  </div>

  <section class="section">
    <div class="grid three">{facility_cards}</div>
  </section>

  {''.join(facility_sections)}
</main>"""
    json_ld = [
        person_json_ld(),
        breadcrumb_json_ld([("Home", "/"), ("Observing Programs", path)]),
        collection_json_ld(
            "Observing programs",
            path,
            [f"/observing-programs/#{slug}" for slug in facility_slugs.values()],
        ),
    ]
    return render_layout(
        "Observing Programs | Alexander Salganik",
        "PI observing programs by Alexander Salganik across NuSTAR, IXPE, Insight-HXMT, and Swift.",
        path,
        body,
        keywords=["observing programs", "NuSTAR", "IXPE", "Insight-HXMT", "Swift"],
        json_ld=json_ld,
        active_path="/observing-programs/",
    )


def build_talks_page():
    path = "/talks/"
    talks = sorted_talks()
    grouped = defaultdict(list)
    for talk in talks:
        grouped[talk["title"]].append(talk)
    sections = []
    for title, items in grouped.items():
        related = None
        if items[0].get("publication_slug"):
            related = PUBLICATION_BY_SLUG[items[0]["publication_slug"]]
        related_markup = ""
        if related:
            related_markup = (
                f'<p class="muted">Related publication: '
                f'<a href="{escape(publication_path(related), quote=True)}">{escape(related["title"])}</a></p>'
            )
        entries = "".join(
            f"""
<li class="list-row">
  <div class="item-main">{escape(item['event'])}</div>
  <div class="item-meta"><span class="date-badge">{escape(item['date_label'])}</span></div>
</li>"""
            for item in items
        )
        sections.append(
            f"""
<section class="section">
  <h2 class="section-title">{escape(title)}</h2>
  {related_markup}
  <ul class="compact-list">{entries}</ul>
</section>"""
        )
    body = f"""
<main id="content" class="container">
  <div class="page-title">
    <div class="breadcrumbs">{breadcrumb_html([('Home', '/'), ('Talks', path)])}</div>
    <h1>Talks</h1>
    <p class="lead">Conference presentations and invited talks connected to the publication and method-development record.</p>
  </div>

  {''.join(sections)}
</main>"""
    json_ld = [
        person_json_ld(),
        breadcrumb_json_ld([("Home", "/"), ("Talks", path)]),
        collection_json_ld("Talks", path, ["/publications/"]),
    ]
    return render_layout(
        "Talks | Alexander Salganik",
        "Conference talks and invited talks by Alexander Salganik on X-ray pulsars, timing transitions, accretion regimes, and X-ray polarimetry.",
        path,
        body,
        keywords=["talks", "conference presentations", "invited talks"],
        json_ld=json_ld,
        active_path="/talks/",
    )


def render_timeline_cards(items, label_key="date_label", title_key="title"):
    cards = []
    for item in items:
        details = [item[key] for key in ("description", "amount") if item.get(key)]
        detail_html = ""
        if details:
            detail_html = f'<div class="muted small">{escape(" · ".join(details))}</div>'
        cards.append(
            f"""
<div class="card">
  <div class="row">
    <div class="item-main">{escape(item[title_key])}{detail_html}</div>
    <div class="item-meta"><span class="date-badge">{escape(item.get(label_key, ''))}</span></div>
  </div>
</div>"""
        )
    return "".join(cards)


def build_cv_page():
    path = "/cv/"
    awards_markup = []
    for award in AWARDS:
        label = escape(award["title"])
        if award.get("url"):
            label = (
                f'{label} '
                f'(<a href="{escape(award["url"], quote=True)}" target="_blank" rel="noopener noreferrer">{escape(award["link_label"])}</a>)'
            )
        awards_markup.append(
            f"""
<div class="card">
  <div class="row">
    <div class="item-main">{label}</div>
    <div class="item-meta"><span class="date-badge">{escape(award['date_label'])}</span></div>
  </div>
</div>"""
        )
    education_markup = "".join(
        f"""
<div class="card">
  <div class="row">
    <div class="item-main"><b>{escape(item['institution'])}</b><div class="muted">{escape(item['detail'])}</div></div>
    <div class="item-meta"><span class="date-badge">{escape(item['date_label'])}</span></div>
  </div>
</div>"""
        for item in EDUCATION
    )
    experience_markup = "".join(
        f"""
<div class="card">
  <div class="row">
    <div class="item-main"><b>{escape(item['institution'])}</b><div class="muted">{escape(item['detail'])}</div></div>
    <div class="item-meta"><span class="date-badge">{escape(item['date_label'])}</span></div>
  </div>
</div>"""
        for item in EXPERIENCE
    )
    service_markup = "".join(
        f"""
<div class="card">
  <div class="row">
    <div class="item-main">{escape(item['title'])}</div>
    <div class="item-meta">{f'<span class="date-badge">{escape(item["date_label"])}</span>' if item.get('date_label') else ''}</div>
  </div>
</div>"""
        for item in SERVICE
    )
    press_markup = "".join(
        f"""
<div class="card">
  <div class="row">
    <div class="item-main"><a href="{escape(item['url'], quote=True)}" target="_blank" rel="noopener noreferrer">{escape(item['title'])}</a></div>
    <div class="item-meta"><span class="date-badge">{escape(item['date_label'])}</span></div>
  </div>
</div>"""
        for item in PRESS
    )
    body = f"""
<main id="content" class="container">
  <div class="page-title">
    <div class="breadcrumbs">{breadcrumb_html([('Home', '/'), ('CV', path)])}</div>
    <h1>CV</h1>
    <p class="lead">Education, grants with amounts, awards, service, work experience, and research press references.</p>
  </div>

  <div class="cta-strip">
    <div>
      <b>Download the complete CV</b>
      <div class="muted small">PDF version for applications and sharing.</div>
    </div>
    <a class="btn primary" href="/cv/Alexander_Salganik_CV.pdf" type="application/pdf" download>Download CV (PDF)</a>
  </div>

  <section class="section">
    <h2 class="section-title">Grants</h2>
    <div class="stacked-list">{render_timeline_cards(GRANTS)}</div>
  </section>

  <section class="section">
    <h2 class="section-title">Awards and honors</h2>
    <div class="stacked-list">{''.join(awards_markup)}</div>
  </section>

  <section class="section">
    <h2 class="section-title">Education</h2>
    <div class="stacked-list">{education_markup}</div>
  </section>

  <section class="section">
    <h2 class="section-title">Work experience</h2>
    <div class="stacked-list">{experience_markup}</div>
  </section>

  <section class="section">
    <h2 class="section-title">Professional service</h2>
    <div class="stacked-list">{service_markup}</div>
  </section>

  <section class="section">
    <h2 class="section-title">Research press releases</h2>
    <div class="stacked-list">{press_markup}</div>
  </section>
</main>"""
    json_ld = [
        person_json_ld(),
        breadcrumb_json_ld([("Home", "/"), ("CV", path)]),
    ]
    return render_layout(
        "CV | Alexander Salganik",
        "Curriculum vitae of Alexander Salganik, including education, grants with amounts, awards, professional service, work experience, and a downloadable PDF.",
        path,
        body,
        keywords=["CV", "curriculum vitae", "grants", "awards"],
        json_ld=json_ld,
        active_path="/cv/",
    )


def build_contact_page():
    path = "/contact/"
    email_cards = "".join(
        f"<p><a href=\"mailto:{escape(entry['address'], quote=True)}\">{escape(entry['address'])}</a></p>"
        for entry in SITE["emails"]
    )
    body = f"""
<main id="content" class="container">
  <div class="page-title">
    <div class="breadcrumbs">{breadcrumb_html([('Home', '/'), ('Contact', path)])}</div>
    <h1>Contact</h1>
    <p class="lead">Contact information and authoritative external profiles for collaboration, talks, and research inquiries.</p>
  </div>

  <section class="section">
    <div class="grid two">
      <div class="card">
        <h2>Email</h2>
        {email_cards}
      </div>
      <div class="card">
        <h2>Profiles</h2>
        <p>{external_link(SITE['orcid'], 'ORCID')}</p>
        <p>{external_link(SITE['university_profile'], 'University of Turku profile')}</p>
        <p><a href="/publications/">Publication pages</a></p>
      </div>
    </div>
  </section>
</main>"""
    json_ld = [
        person_json_ld(),
        breadcrumb_json_ld([("Home", "/"), ("Contact", path)]),
    ]
    return render_layout(
        "Contact | Alexander Salganik",
        "Contact Alexander Salganik, high-energy astrophysicist at the University of Turku, through email, ORCID, and the university profile.",
        path,
        body,
        keywords=["contact", "ORCID", "University of Turku"],
        json_ld=json_ld,
        active_path="/contact/",
    )


def build_sitemap():
    routes = ["/", "/research/", "/publications/", "/observing-programs/", "/talks/", "/cv/", "/contact/"]
    routes.extend(f"/research/{topic['slug']}/" for topic in TOPICS)
    routes.extend(publication_path(publication) for publication in sorted_publications())
    routes.append("/cv/Alexander_Salganik_CV.pdf")
    urls = "\n".join(
        f"  <url><loc>{escape(page_url(route))}</loc><lastmod>{BUILD_DATE}</lastmod></url>"
        for route in routes
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls}
</urlset>
"""


def build_robots():
    return f"""User-agent: *
Allow: /

Sitemap: {page_url('/sitemap.xml')}
"""


def build_readme():
    return """# salganik.me

Static academic website for Alexander Salganik.

## Rebuild the site

Run:

```bash
python3 scripts/build_site.py
```

This regenerates the HTML pages and `sitemap.xml` from the Python data source in `scripts/site_data.py`.
"""


def build_deploy_readme():
    return """Run `python3 scripts/build_site.py` before uploading the site.

Upload all files and folders from this directory to the root of salganik.me, including `assets/favicon.svg`, `photo.jpg`, and `cv/Alexander_Salganik_CV.pdf`.

After upload, submit `https://salganik.me/sitemap.xml` in Google Search Console and request indexing for the homepage, `/research/`, and new publication detail pages.
"""


def main():
    write_page("/", build_home())
    write_page("/research/", build_research_index())
    for topic in TOPICS:
        write_page(f"/research/{topic['slug']}/", build_topic_page(topic))
    write_page("/publications/", build_publications_index())
    for publication in sorted_publications():
        write_page(publication_path(publication), build_publication_page(publication))
    write_page("/observing-programs/", build_observing_programs_page())
    write_page("/talks/", build_talks_page())
    write_page("/cv/", build_cv_page())
    write_page("/contact/", build_contact_page())
    (ROOT / "sitemap.xml").write_text(build_sitemap(), encoding="utf-8")
    (ROOT / "robots.txt").write_text(build_robots(), encoding="utf-8")
    (ROOT / "README.md").write_text(build_readme(), encoding="utf-8")
    (ROOT / "README_DEPLOY.txt").write_text(build_deploy_readme(), encoding="utf-8")


if __name__ == "__main__":
    main()
