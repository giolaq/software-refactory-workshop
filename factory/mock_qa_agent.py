#!/usr/bin/env python3
"""Deterministic independent QA adapter for credential-free rehearsals."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


TV_TESTS = {
    1: '''def test_ticket_1_tv_mode_acceptance(client):
    assert b'class="tv"' in client.get("/?mode=tv").data
    assert b'class="mobile"' in client.get("/").data
''',
    2: '''from pathlib import Path


def test_ticket_2_tv_theme_acceptance():
    css = (Path(__file__).parents[1] / "static/styles.css").read_text()
    assert "ticket-2-tv-theme" in css
    assert "body.tv" in css
''',
    3: '''from pathlib import Path


def test_ticket_3_focus_engine_acceptance():
    source = (Path(__file__).parents[1] / "static/focus.js").read_text()
    assert "nextFocus" in source
    assert all(key in source for key in ("ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"))
''',
    4: '''from pathlib import Path


def test_ticket_4_dpad_acceptance():
    source = (Path(__file__).parents[1] / "static/tv-nav.js").read_text()
    assert "nextFocus" in source
    assert "Enter" in source
''',
    5: '''from pathlib import Path


def test_ticket_5_rails_acceptance():
    source = (Path(__file__).parents[1] / "static/rails.js").read_text()
    assert "/api/rails" in source
    assert "rail-track" in source
''',
    6: '''from pathlib import Path


def test_ticket_6_tv_detail_acceptance():
    root = Path(__file__).parents[1] / "static"
    source = (root / "tv-detail.js").read_text()
    assert "Escape" in source and "Backspace" in source
    assert (root / "tv-detail.css").is_file()
''',
    7: '''def test_ticket_7_rails_api_acceptance(client):
    response = client.get("/api/rails")
    assert response.status_code == 200
    rails = response.get_json()
    assert [rail["title"] for rail in rails] == [
        "Trending now", "My watchlist", "Science fiction", "Mysteries",
    ]
''',
}


RECIPE_TESTS = {
    1: '''def test_ticket_1_recipe_api_acceptance(client):
    response = client.get("/api/recipes")
    assert response.status_code == 200
    recipes = response.get_json()
    assert len(recipes) >= 12
    required = {
        "id", "title", "description", "category", "dietary_tags",
        "ingredients", "steps", "prep_minutes", "cook_minutes",
    }
    assert all(required <= set(recipe) for recipe in recipes)

    assert {recipe["id"] for recipe in client.get("/api/recipes?q=weeknight").get_json()} == {"tomato-pasta"}
    assert "tomato-pasta" in {recipe["id"] for recipe in client.get("/api/recipes?q=dinner").get_json()}
    assert "miso-noodles" in {recipe["id"] for recipe in client.get("/api/recipes?q=vegan").get_json()}
    assert {recipe["id"] for recipe in client.get("/api/recipes?q=tomatoes").get_json()} == {"tomato-pasta"}

    known_ids = {recipe["id"] for recipe in recipes}
    rails = client.get("/api/rails").get_json()
    assert rails and all(set(rail["recipe_ids"]) <= known_ids for rail in rails)
    assert client.get("/api/recipes/not-a-recipe").status_code == 404


def test_ticket_1_cookbook_acceptance(client):
    assert client.get("/api/cookbook").get_json() == []
    added = client.post("/api/cookbook", json={"id": "tomato-pasta"})
    assert added.status_code == 201
    assert added.get_json()["ids"] == ["tomato-pasta"]
    assert [recipe["id"] for recipe in client.get("/api/cookbook").get_json()] == ["tomato-pasta"]
    assert client.delete("/api/cookbook/tomato-pasta").get_json()["ids"] == []
''',
    2: '''def test_ticket_2_brand_tokens_acceptance(client):
    response = client.get("/static/table-story.css")
    assert response.status_code == 200, "The TableStory stylesheet must be served"
    css = response.get_data(as_text=True).lower()
    assert all(color in css for color in ("#fff8ed", "#c9472d", "#3f6b4f", "#26231f", "#e9b44c"))
    assert ".recipe-grid" in css and "minmax(220px,1fr)" in css
    assert "@media (max-width: 520px)" in css and "grid-template-columns:1fr" in css
    assert ":focus-visible" in css and "outline" in css
    assert '.cookbook[aria-pressed="true"]' in css


def test_ticket_2_visible_brand_acceptance(client):
    home = client.get("/")
    assert home.status_code == 200
    assert b"TableStory" in home.data
    assert b"table-story.css" in home.data
''',
    3: '''from pathlib import Path


def test_ticket_3_mobile_recipe_acceptance(client):
    home = client.get("/")
    assert home.status_code == 200
    assert b"TableStory" in home.data
    assert b"Good food, clearly told." in home.data
    assert b'Search dishes or ingredients' in home.data
    assert b'data-search=' in home.data

    detail = client.get("/recipe/tomato-pasta")
    assert detail.status_code == 200
    assert all(text in detail.data for text in (b"Prep 10 min", b"Cook 20 min", b"Ingredients", b"Method"))
    assert b'aria-pressed="false"' in detail.data

    source = (Path(__file__).parents[1] / "static/app.js").read_text()
    assert "addEventListener('input'" in source and "card.hidden" in source
    assert "No recipes found" in home.data.decode()
    assert "aria-pressed" in source and "/api/cookbook" in source
''',
    4: '''from pathlib import Path


def test_ticket_4_tv_recipe_acceptance(client):
    home = client.get("/?mode=tv")
    assert home.status_code == 200
    assert b'class="tv"' in home.data
    rails = client.get("/api/rails").get_json()
    assert [rail["title"] for rail in rails] == [
        "Popular this week", "Ready in 30 minutes", "Vegetarian favourites", "My Cookbook",
    ]
    assert all(len(rail["recipe_ids"]) >= 2 for rail in rails[:3])
    assert b"recipe-rails.js" in home.data and b"recipe-tv-nav.js" in home.data

    root = Path(__file__).parents[1] / "static"
    browse = (root / "recipe-tv-nav.js").read_text()
    detail = (root / "recipe-tv-detail.js").read_text()
    rails_source = (root / "recipe-rails.js").read_text()
    assert all(key in browse for key in ("ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Enter"))
    assert "scrollIntoView" in browse
    assert "Escape" in detail and "Backspace" in detail
    assert "/api/rails" in rails_source and "recipe_ids" in rails_source
    assert b"/?mode=tv" in client.get("/recipe/tomato-pasta?mode=tv").data
''',
    5: '''from pathlib import Path


def test_ticket_5_documentation_acceptance():
    root = Path(__file__).parents[1]
    assert (root / "README.md").is_file(), "The product must include its TableStory run and verification guide"
    readme = (root / "README.md").read_text()
    assert "TableStory" in readme
    assert "?mode=tv" in readme
    assert "pytest" in readme and "node --test" in readme
    assert not (root / "catalog.json").exists()
    terminology_test = root / "tests/test_terminology.py"
    assert terminology_test.is_file()
    source = terminology_test.read_text().lower()
    assert all(marker in source for marker in ("forbidden", "violations", '"watch" + "list"'))
''',
}


BRAND_REVISION = '''

def test_ticket_2_stylesheet_delivery_acceptance(client):
    response = client.get("/static/table-story.css")
    assert response.status_code == 200
    assert response.mimetype == "text/css"
    home = client.get("/")
    assert b'name="viewport"' in home.data
    assert b'aria-label="TableStory home"' in home.data
'''


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ticket", type=int)
    parser.add_argument("--scenario", choices=["tv", "recipe-rebrand"], default="tv")
    args = parser.parse_args()
    tests = TV_TESTS if args.scenario == "tv" else RECIPE_TESTS
    if args.ticket not in tests:
        print(f"QA rejected ticket #{args.ticket}: acceptance criteria are not objectively testable")
        return 2
    # Rehearsal offers bounded reference revisions, not open-ended generation.
    prompt = sys.stdin.read() if not sys.stdin.isatty() else ""
    feedback = re.search(r"## Human review feedback\n.*?```\n(.*?)\n```", prompt, re.S)
    source = tests[args.ticket]
    if feedback:
        supported = args.scenario == "recipe-rebrand" and args.ticket == 2 and any(
            term in feedback.group(1).lower() for term in ("filenotfounderror", "stylesheet")
        )
        if not supported:
            print("This feedback is not supported by the deterministic Rehearsal adapter. "
                  "Use Live mode for open-ended revisions; no replacement test was generated.")
            return 2
        source += BRAND_REVISION
        print("Reference revision: validate stylesheet delivery and the branded HTML shell. "
              "Browser layout and keyboard focus still require human inspection.")
    destination = Path.cwd() / "demo-app/tests" / f"test_ticket_{args.ticket}_acceptance.py"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(source)
    print(f"Mock QA created {destination.relative_to(Path.cwd())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
