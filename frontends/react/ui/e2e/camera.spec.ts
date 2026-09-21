import { expect, test, type Page } from "@playwright/test";
import { fixed, folded, noSheet, TRAINER } from "./helpers";

/* The one spec that needs a camera. Chromium is handed a fake one and told to answer
   its own prompt, so the trainer's camera goes live the way it does on a phone, with a
   test pattern for a picture. Everything asserted is geometry the lifter sees: what
   fills the page, and what is drawn on top of it. */
test.use({
  launchOptions: {
    args: ["--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream"],
  },
});

test.beforeEach(({ page }) => noSheet(page));

type Box = { x: number; y: number; width: number; height: number };

async function box(page: Page, selector: string): Promise<Box> {
  const found = await page.locator(selector).boundingBox();
  expect(found, `${selector} is drawn`).not.toBeNull();
  return found as Box;
}

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

  /* And the controls are on it, not under it: a tap in the middle of one from each
     group lands on that group rather than on the picture. */
  const groups: [string, string][] = [
    ["header", "header button"],
    [".head", ".nav button"],
    [".sets", ".set .log"],
    [".wt", ".wt button"],
  ];
  const tapped = await page.evaluate(
    (asked) =>
      asked.map(([group, control]) => {
        const at = document.querySelector(control)!.getBoundingClientRect();
        const hit = document.elementFromPoint(at.x + at.width / 2, at.y + at.height / 2);
        return hit !== null && hit.closest(group) !== null;
      }),
    groups,
  );
  for (const [i, [group]] of groups.entries()) {
    expect(tapped[i], `${group} is above the picture`).toBe(true);
  }

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

/* In the shell, with both rails folded, the picture is the whole screen — the folded
   rails under it — and closing the camera gives them their place back. */
test("in the shell with both rails folded, the camera is the whole screen", async ({
  page,
}) => {
  const frame = await fixed(page, "fitness");
  await folded(page, /Documents/);
  await folded(page, /Plan & memory/);
  const framed = frame.contentFrame();
  const before = await box(page, 'iframe[title="fitness"]');
  const size = page.viewportSize();
  expect(size).not.toBeNull();
  const whole = { x: 0, y: 0, width: size!.width, height: size!.height };
  expect(before, "the folded rails leave the frame short of the screen").not.toEqual(
    whole,
  );

  await framed.locator("[data-cam]").click();
  await expect(framed.locator("body")).toHaveClass(/cam-live/);
  await expect
    .poll(() => frame.boundingBox(), { message: "the frame is the whole screen" })
    .toEqual(whole);
  /* An element in a frame reports where it is on the page, so the picture is measured
     against the same screen. */
  expect(
    await framed.locator("#camview").boundingBox(),
    "the picture is the whole screen",
  ).toEqual(whole);

  /* The picture taken away underneath — another app, a sleeping tab — closes the camera
     from the page's side, and the shell hears it let go. */
  await framed
    .locator("body")
    .evaluate('camStream.getVideoTracks()[0].dispatchEvent(new Event("ended"))');
  await expect(framed.locator("body")).not.toHaveClass(/cam-live/);
  await expect
    .poll(() => frame.boundingBox(), { message: "the shell hears it let go" })
    .toEqual(before);

  /* Opened again, Escape is the shell's own way back, whatever the page does — pressed
     where the reader is, which is inside the frame. The camera keeps filming: what is
     taken back is the screen, not the picture. */
  await framed.locator("[data-cam]").click();
  await expect(framed.locator("body")).toHaveClass(/cam-live/);
  await framed.locator("#camflip").press("Escape");
  await expect
    .poll(() => frame.boundingBox(), { message: "Escape gives the rails their place back" })
    .toEqual(before);
  await expect(framed.locator("body"), "and the camera films on").toHaveClass(
    /cam-live/,
  );

  /* And closing the camera by hand leaves them there. */
  await framed.locator("[data-cam]").click();
  await expect
    .poll(() => frame.boundingBox(), {
      message: "closing the camera gives the rails their place back",
    })
    .toEqual(before);
});

/* The prompt is the one moment the camera is open with no picture, and a tap during it
   is a camera closed, or closed and opened again, before it ever showed. Chromium's fake
   camera answers at once, so its answers are held back here and let go by hand. */
test("the shell moves once there is a picture, and a camera closed while the browser was asking stays closed", async ({
  page,
}) => {
  await page.addInitScript(() => {
    const devices = navigator.mediaDevices;
    if (!devices) return;
    const answer = devices.getUserMedia.bind(devices);
    const held = window as unknown as {
      grant: () => Promise<void>;
      given: MediaStream[];
      pending: (() => Promise<void>)[];
    };
    held.given = [];
    held.pending = [];
    /* Every request asked so far is answered, in the order it came. */
    held.grant = () =>
      Promise.all(held.pending.splice(0).map((one) => one())).then(() => undefined);
    devices.getUserMedia = (wanted) =>
      new Promise((resolve, reject) => {
        held.pending.push(() =>
          answer(wanted).then((stream) => {
            held.given.push(stream);
            resolve(stream);
          }, reject),
        );
      });
  });
  const frame = await fixed(page, "fitness");
  await folded(page, /Documents/);
  await folded(page, /Plan & memory/);
  const framed = frame.contentFrame();
  const before = await box(page, 'iframe[title="fitness"]');
  const grant = () =>
    framed
      .locator("body")
      .evaluate(() => (window as unknown as { grant: () => Promise<void> }).grant());
  /* Which of the answers given so far still has a live track. */
  const live = () =>
    framed.locator("body").evaluate(() =>
      (window as unknown as { given: MediaStream[] }).given.map((stream) =>
        stream.getTracks().some((track) => track.readyState === "live"),
      ),
    );
  const ground = () =>
    framed.locator(".stage").evaluate((stage) => getComputedStyle(stage).borderTopColor);

  /* Asked, not answered: the camera is the view, the frame keeps its ground, and nothing
     has moved. A message the page should not have sent would land within a frame or
     two, so the check waits a moment before saying nothing came. */
  await framed.locator("[data-cam]").click();
  await expect(framed.locator("body")).toHaveClass(/view-cam/);
  await page.waitForTimeout(300);
  expect(await ground(), "the frame keeps its ground while the prompt is up").not.toBe(
    "rgba(0, 0, 0, 0)",
  );
  expect(await frame.boundingBox(), "nothing moves while the prompt is up").toEqual(
    before,
  );

  /* Closed before the answer, then answered: the stream is let go, and neither the
     page nor the shell shows a camera. */
  await framed.locator("[data-cam]").click();
  await expect(framed.locator("body")).not.toHaveClass(/view-cam/);
  await grant();
  await expect
    .poll(live, { message: "a stream answered after the camera closed is stopped" })
    .toEqual([false]);
  await expect(framed.locator("body")).not.toHaveClass(/cam-live/);
  expect(await frame.boundingBox(), "the shell never moved").toEqual(before);

  /* Closed and opened again while the browser was still asking: two answers arrive for
     one camera, and only the one for the camera that is open is kept. */
  await framed.locator("[data-cam]").click();
  await framed.locator("[data-cam]").click();
  await framed.locator("[data-cam]").click();
  await expect(framed.locator("body")).toHaveClass(/view-cam/);
  await grant();
  await expect(framed.locator("body")).toHaveClass(/cam-live/);
  await expect
    .poll(live, { message: "the answer for the camera that was closed is stopped" })
    .toEqual([false, false, true]);
  const size = page.viewportSize();
  await expect
    .poll(() => frame.boundingBox(), { message: "the frame is the whole screen" })
    .toEqual({ x: 0, y: 0, width: size!.width, height: size!.height });
});

/* A granted camera is not yet a picture: on a real device the first frame lands a beat
   after the permission is given, and pinning on the grant shows a black page for that
   beat. The fake camera has no warm-up, so the picture is held back by hand here. */
test("the screen is taken for the picture, not for the permission", async ({ page }) => {
  const frame = await fixed(page, "fitness");
  await folded(page, /Documents/);
  await folded(page, /Plan & memory/);
  const framed = frame.contentFrame();
  const before = await box(page, 'iframe[title="fitness"]');
  const body = framed.locator("body");

  /* The picture waits on a hand rather than on the camera. */
  await body.evaluate(() => {
    const view = document.getElementById("camview") as HTMLVideoElement;
    const real = Object.getOwnPropertyDescriptor(
      HTMLMediaElement.prototype,
      "srcObject",
    )!;
    Object.defineProperty(view, "srcObject", {
      get: () => real.get!.call(view),
      set: (given: MediaStream | null) => {
        (window as unknown as { show: () => void }).show = () =>
          real.set!.call(view, given);
      },
    });
  });

  await framed.locator("[data-cam]").click();
  await expect(body).toHaveClass(/view-cam/);
  await page.waitForTimeout(300);
  expect(await frame.boundingBox(), "nothing moves for a permission alone").toEqual(
    before,
  );
  await expect(body, "and the page is not live on one either").not.toHaveClass(
    /cam-live/,
  );

  /* The first frame is what the screen is taken for. */
  await body.evaluate(() => (window as unknown as { show: () => void }).show());
  await expect(body).toHaveClass(/cam-live/);
  const size = page.viewportSize();
  await expect
    .poll(() => frame.boundingBox(), { message: "the picture takes the screen" })
    .toEqual({ x: 0, y: 0, width: size!.width, height: size!.height });
});
