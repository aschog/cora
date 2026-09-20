import { expect, test, type Page } from "@playwright/test";

/* The one spec that needs a camera. Chromium is handed a fake one and told to answer
   its own prompt, so the trainer's camera goes live the way it does on a phone, with a
   test pattern for a picture. Everything asserted is geometry the lifter sees: what
   fills the page, and what is drawn on top of it. */
test.use({
  launchOptions: {
    args: ["--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream"],
  },
});

const TRAINER = "/pages/fitness/";

test.beforeEach(async ({ page }) => {
  await page.route("**/docs.google.com/**", (asked) => asked.abort());
});

type Box = { x: number; y: number; width: number; height: number };

async function box(page: Page, selector: string): Promise<Box> {
  const found = await page.locator(selector).boundingBox();
  expect(found, `${selector} is drawn`).not.toBeNull();
  return found as Box;
}

/* Within, to the pixel a browser rounds to. */
const inside = (part: Box, whole: Box) =>
  part.x >= whole.x - 1 &&
  part.y >= whole.y - 1 &&
  part.x + part.width <= whole.x + whole.width + 1 &&
  part.y + part.height <= whole.y + whole.height + 1;

const between = (part: Box, above: Box, below: Box) =>
  part.y >= above.y + above.height && part.y + part.height <= below.y;

test("the opened camera fills the page, with the controls drawn over it", async ({
  page,
}) => {
  await page.goto(TRAINER);
  const size = page.viewportSize();
  expect(size).not.toBeNull();

  await page.locator("[data-cam]").click();
  await expect(page.locator("body")).toHaveClass(/cam-live/);

  /* The picture is the page. */
  const picture = await box(page, "#camview");
  expect(picture, "the picture fills the page").toEqual({
    x: 0,
    y: 0,
    width: size!.width,
    height: size!.height,
  });

  /* And the controls are on it, not beside it: each lies within the picture, and the
     set control takes the tap rather than the picture under it. */
  for (const part of ["header", ".head", ".sets", ".wt"]) {
    expect(inside(await box(page, part), picture), `${part} is on the picture`).toBe(
      true,
    );
  }
  const tapped = await page.evaluate(() => {
    const at = document.querySelector(".set .log")!.getBoundingClientRect();
    const hit = document.elementFromPoint(at.x + at.width / 2, at.y + at.height / 2);
    return hit?.closest(".set") !== null;
  });
  expect(tapped, "a set control is above the picture").toBe(true);

  /* What sat on the frame keeps its band between the row and the sets. */
  const row = await box(page, ".head");
  const sets = await box(page, ".sets");
  for (const part of ["#camflip", "#setcount"]) {
    expect(
      between(await box(page, part), row, sets),
      `${part} sits between the row and the sets`,
    ).toBe(true);
  }

  /* A set logged while filming reads done over the picture, and the rest counts down
     in that same band. */
  await page.locator(".set .log").first().click();
  await expect(page.locator(".set.on")).toHaveCount(1);
  expect(
    between(await box(page, "#restnum"), row, sets),
    "the rest counts down between the row and the sets",
  ).toBe(true);
});
