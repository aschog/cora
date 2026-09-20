import { expect, test } from "@playwright/test";
import { contrast } from "./helpers";

/* The vocabulary page, in the only tier that can run it: it is the plugin's own
   JavaScript, served by cora at its field's path, and nothing in the Python or the
   shell tiers executes a line of it. Its pure functions are called in the page itself
   rather than lifted out of the file, so what is asserted is what the browser loaded. */

const VOCAB = "/pages/vocab/";

type Row = { German: string; learning: string };
type Page = {
  rowsFrom: (text: string) => Row[];
  listText: (language: string, title: string, rows: Row[]) => string;
  listName: (language: { name: string; slug: string }, title: string) => string;
};

/* The reading runtime is fetched on the first screenshot, and no spec here wants it:
   one asserts what a failure to fetch says, and the rest are about what the page does
   with text it already has. So the suite never reaches a CDN. */
test.beforeEach(async ({ page }) => {
  await page.route("**/cdn.jsdelivr.net/**", (asked) => asked.abort());
});

test("a list is written as a heading and a table of pairs", async ({
  page,
}) => {
  await page.goto(VOCAB);

  const written = await page.evaluate(() => {
    const { listText } = window as unknown as Page;
    return {
      pairs: listText("English", "Einheit 3", [
        { German: "Hilfe", learning: "help" },
        { German: "Haus", learning: "house" },
      ]),
      /* A row the reader left half empty is not a pair, so it is not in the list. */
      half: listText("English", "Einheit 3", [
        { German: "Hilfe", learning: "help" },
        { German: "Haus", learning: "" },
      ]),
      /* A word holding a pipe does not break the table it is written into. */
      piped: listText("English", "", [
        { German: "oder|und", learning: "or|and" },
      ]),
      /* Nothing to write is nothing written, which is what stops an empty upload. */
      nothing: listText("English", "Einheit 3", [{ German: "", learning: "" }]),
    };
  });

  expect(written.pairs).toBe(
    "# English — Einheit 3\n\n| Deutsch | English |\n| --- | --- |\n" +
      "| Hilfe | help |\n| Haus | house |\n",
  );
  expect(written.half).toBe(
    "# English — Einheit 3\n\n| Deutsch | English |\n| --- | --- |\n| Hilfe | help |\n",
  );
  expect(written.piped).toBe(
    "# English\n\n| Deutsch | English |\n| --- | --- |\n| oder\\|und | or\\|and |\n",
  );
  expect(written.nothing).toBe("");
});

test("a list is named for the language it is in", async ({ page }) => {
  await page.goto(VOCAB);

  const named = await page.evaluate(() => {
    const { listName } = window as unknown as Page;
    const latina = { name: "Latina", slug: "latina" };
    return {
      titled: listName(latina, "Einheit 3"),
      /* No title names it for the day it was saved. */
      dated: listName(latina, ""),
    };
  });

  expect(named.titled).toBe("latina-einheit-3.md");
  expect(named.dated).toMatch(/^latina-\d{4}-\d{2}-\d{2}\.md$/);
});

test("a reading becomes rows split where the gap is", async ({ page }) => {
  await page.goto(VOCAB);

  const read = await page.evaluate(() => {
    const { rowsFrom } = window as unknown as Page;
    return {
      columns: rowsFrom("Hilfe     help\nHaus\thouse"),
      dashed: rowsFrom("der Hund — the dog"),
      spaced: rowsFrom("Hilfe help"),
      /* A line the reading gave one word of is offered with the other half empty. */
      lonely: rowsFrom("help"),
      blank: rowsFrom("\n  \n"),
    };
  });

  expect(read.columns).toEqual([
    { German: "Hilfe", learning: "help" },
    { German: "Haus", learning: "house" },
  ]);
  expect(read.dashed).toEqual([{ German: "der Hund", learning: "the dog" }]);
  expect(read.spaced).toEqual([{ German: "Hilfe", learning: "help" }]);
  expect(read.lonely).toEqual([{ German: "help", learning: "" }]);
  expect(read.blank).toEqual([]);
});

test("a reading runtime that cannot be fetched says so", async ({ page }) => {
  await page.goto(VOCAB);

  await page
    .locator("#file")
    .setInputFiles({ name: "words.png", mimeType: "image/png", buffer: SHOT });

  await expect(page.locator("#said")).toContainText("could not be run");
  await expect(page.locator("#said")).toHaveClass(/bad/);
});

test("a corrected row is what the vocab field is given", async ({ page }) => {
  await page.goto(VOCAB);

  await page.locator("#title").fill("Einheit 3");
  await page.getByRole("button", { name: "Add a row" }).click();
  const row = page.locator("#rows tr").first();
  await row.locator("input").first().fill("Hilfe");
  await row.locator("input").nth(1).fill("help");

  const posted = page.waitForRequest(
    (asked) =>
      asked.url().includes("/api/documents") && asked.method() === "POST",
  );
  await page.getByRole("button", { name: "Save to cora" }).click();
  await posted;

  await expect(page.locator("#said")).toContainText("english-einheit-3.md");

  const held = await page.request.get(
    "/api/documents/vocab/english-einheit-3.md",
  );
  expect(held.ok()).toBe(true);
  const [upload] = await held.json();
  expect(upload.text).toContain("| Hilfe | help |");
});

test("a list holding no row uploads nothing", async ({ page }) => {
  await page.goto(VOCAB);

  await page.getByRole("button", { name: "Save to cora" }).click();

  await expect(page.locator("#said")).toContainText("nothing to save");
  await expect(page.locator("#said")).toHaveClass(/bad/);
});

test("an upload cora refuses is reported and left to copy", async ({
  page,
}) => {
  await page.goto(VOCAB);

  await page.route("**/api/documents", (asked) =>
    asked.fulfill({ status: 400, json: { error: "no" } }),
  );

  await page.locator("#title").fill("Einheit 4");
  await page.getByRole("button", { name: "Add a row" }).click();
  const row = page.locator("#rows tr").first();
  await row.locator("input").first().fill("Haus");
  await row.locator("input").nth(1).fill("house");
  await page.getByRole("button", { name: "Save to cora" }).click();

  await expect(page.locator("#said")).toContainText("refused");
  await expect(page.locator("#saved")).toContainText("| Haus | house |");
});

/* The smallest thing a browser will take as an image: one transparent pixel. Nothing
   reads text out of it, and no spec here asks anything to try. */
const SHOT = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk" +
    "YPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
  "base64",
);

test("a screenshot read on the page is corrected and saved into the field", async ({
  page,
}) => {
  /* The recognition itself is Tesseract's and not cora's, so the page is given a
     reading rather than a CDN: what is under test is everything the page does with
     one. */
  await page.addInitScript(() => {
    (window as unknown as { Tesseract: unknown }).Tesseract = {
      createWorker: async () => ({
        recognize: async () => ({
          data: { text: "Hilfe  heIp\nHaus  house" },
        }),
        terminate: async () => undefined,
      }),
    };
  });
  await page.goto(VOCAB);

  await page.locator("#title").fill("Einheit 5");
  await page
    .locator("#file")
    .setInputFiles({ name: "words.png", mimeType: "image/png", buffer: SHOT });

  await expect(page.locator("#rows tr")).toHaveCount(2);
  /* The reading misread one word, which is what the correction step is for. */
  await page.locator("#rows tr").first().locator("input").nth(1).fill("help");
  await page.getByRole("button", { name: "Save to cora" }).click();

  await expect(page.locator("#said")).toContainText("english-einheit-5.md");

  const held = await page.request.get(
    "/api/documents/vocab/english-einheit-5.md",
  );
  const [upload] = await held.json();
  /* What cora kept is what the page wrote, less the trailing newline its ingestion
     strips off every document. */
  expect(upload.text).toBe(
    "# English — Einheit 5\n\n| Deutsch | English |\n| --- | --- |\n" +
      "| Hilfe | help |\n| Haus | house |",
  );
});

test("the page is drawn on cora's own ground", async ({ page }) => {
  /* The page is framed in the shell, so it lets the shell's ground through and takes
     the shell's colours over it. Transparent and unreadable are both possible, so the
     text is asserted as a ratio rather than as a name. */
  await page.goto(VOCAB);

  const drawn = await page.evaluate(() => {
    const seen = getComputedStyle(document.body);
    const said = getComputedStyle(document.getElementById("said")!);
    return {
      ground: seen.backgroundColor,
      text: seen.color,
      serif: seen.fontFamily,
      muted: said.color,
      shell: getComputedStyle(document.documentElement)
        .getPropertyValue("--bg")
        .trim(),
    };
  });

  expect(drawn.ground).toBe("rgba(0, 0, 0, 0)");
  expect(drawn.serif).toContain("Source Serif 4");
  expect(contrast(drawn.text, drawn.shell)).toBeGreaterThan(4.5);
  expect(contrast(drawn.muted, drawn.shell)).toBeGreaterThan(3);
});
