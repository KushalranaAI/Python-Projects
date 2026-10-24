"""Site-wide checks: every project has complete metadata, every page renders, every live app starts."""

import pytest

from hub import catalog, create_app

PROJECTS = catalog.projects()
REQUIRED = ("title", "summary", "time", "python_skills", "oop_concepts", "clean_code", "features", "architecture", "steps", "exercises")


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    import os

    os.environ["PP_DATA_DIR"] = str(tmp_path_factory.mktemp("data"))
    app = create_app()
    app.testing = True
    return app.test_client()


def test_there_are_twenty_projects_in_three_levels():
    counts = {level: len(items) for level, items in catalog.by_level().items()}
    assert counts == {"beginner": 10, "intermediate": 5, "advanced": 5}
    assert sorted(p.order for p in catalog.by_level()["beginner"]) == list(range(1, 11))


@pytest.mark.parametrize("project", PROJECTS, ids=lambda p: p.slug)
def test_project_metadata_is_complete(project):
    for key in REQUIRED:
        assert getattr(project, key), f"{project.slug}: missing {key}"
    for key in ("python_skills", "oop_concepts", "clean_code", "features", "exercises"):
        bad = [item for item in getattr(project, key) if not isinstance(item, str)]
        assert not bad, f"{project.slug}: {key} items must be strings (quote YAML lines containing ': '): {bad}"
    for step in project.steps:
        assert isinstance(step.body, str) and isinstance(step.title, str)
        for file in step.files:
            assert (project.path / file).exists(), f"{project.slug}: step file {file} not found"
    for part in ("__init__.py", "__main__.py", "cli.py", "web.py", "tests"):
        assert (project.path / part).exists(), f"{project.slug}: missing {part}"


@pytest.mark.parametrize("url", ["/", "/guides/"] + [f"/guides/{g.slug}" for g in catalog.guides()])
def test_site_pages(client, url):
    assert client.get(url).status_code == 200


@pytest.mark.parametrize("project", PROJECTS, ids=lambda p: p.slug)
def test_project_page_and_live_app(client, project):
    page = client.get(f"/projects/{project.slug}")
    assert page.status_code == 200 and project.title.encode() in page.data
    app_page = client.get(f"/play/{project.slug}/")
    assert app_page.status_code == 200 and b"Live app" in app_page.data


def test_unknown_pages_404(client):
    assert client.get("/projects/nope").status_code == 404


def test_test_runner_rejects_other_origins(client):
    slug = PROJECTS[0].slug
    assert client.post(f"/api/projects/{slug}/tests", json={}, headers={"Origin": "https://evil.example"}).status_code == 403
    assert client.post(f"/api/projects/{slug}/tests", data="x", headers={"Content-Type": "text/plain"}).status_code == 403
