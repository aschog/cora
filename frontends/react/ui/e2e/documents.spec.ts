import { expect, test } from "@playwright/test";
import { confirm, fresh } from "./helpers";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));

const NOTE = resolve(HERE, "../../../../tests/e2e/documents/second.md");

/* Two controls add a document now — the rail's, over the list it changes, and the
   composer's, beside the question being typed. Each spec says which one it used. */
const RAIL = "Add a document";
const BESIDE = "Add a file or photo";

test("a document is uploaded, listed, and deleted only once i have said so", async ({
  page,
}) => {
  await fresh(page);

  await page.getByLabel(RAIL).setInputFiles(NOTE);

  /* Indexing is seconds of real work — the embeddings are written before the request
     answers — so the row stands under the control while it runs, and goes when the
     document arrives in the list. The list is what says it worked; the page says
     nothing else about an upload that did. */
  await expect(page.getByRole("status", { name: "Indexing" })).toContainText(
    "second.md",
  );
  await expect(
    page.getByRole("button", { name: "second.md", exact: true }),
  ).toBeVisible();
  await expect(page.getByRole("status", { name: "Indexing" })).toHaveText("");
  /* Read out, not drawn: the list says it to anyone who can see the list, and this is
     the same news for a reader who cannot. */
  await expect(page.getByRole("status", { name: "Last upload" })).toContainText(
    "second.md",
  );

  await page.getByLabel("Delete second.md").click();
  const asked = page.getByRole("dialog", { name: "DELETE DOCUMENT" });
  await expect(asked).toContainText("second.md");
  await asked.getByRole("button", { name: "Keep it" }).click();
  await expect(
    page.getByRole("button", { name: "second.md", exact: true }),
  ).toBeVisible();

  await page.getByLabel("Delete second.md").click();
  await confirm(page, "DELETE DOCUMENT", "Delete document");

  await expect(
    page.getByRole("button", { name: "second.md", exact: true }),
  ).toHaveCount(0);
});

test("a file added beside the question is a document of the same field", async ({
  page,
}) => {
  await fresh(page);

  await page.getByLabel(BESIDE).setInputFiles(NOTE);

  await expect(
    page.getByRole("button", { name: "second.md", exact: true }),
  ).toBeVisible();
  await expect(page.getByRole("status", { name: "Last upload" })).toContainText(
    "second.md",
  );

  await page.getByLabel("Delete second.md").click();
  await confirm(page, "DELETE DOCUMENT", "Delete document");
  await expect(
    page.getByRole("button", { name: "second.md", exact: true }),
  ).toHaveCount(0);
});

test("a file cora refuses is refused the same way from either control", async ({
  page,
}) => {
  await fresh(page);

  /* The refusal is cora's, and what it costs the reader is where they are told: the
     control beside the question adds through the rail's own path, so the rail's own
     notice is what says no. */
  await page.route("**/api/documents", (asked) =>
    asked.request().method() === "POST"
      ? asked.fulfill({
          status: 400,
          json: { error: "That upload is not one cora reads." },
        })
      : asked.continue(),
  );

  await page.getByLabel(BESIDE).setInputFiles(NOTE);

  await expect(
    page.getByText("That upload is not one cora reads."),
  ).toBeVisible();
  await expect(page.getByLabel(BESIDE)).toBeEnabled();
});
