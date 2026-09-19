import { expect, test, type Page } from "@playwright/test";
import { fresh } from "./helpers";

/* The fitness trainer, in the only tier that can run it: it is the plugin's own
   JavaScript, served by cora at its field's path, and nothing in the Python or the
   shell tiers executes a line of it. Its pure functions are called in the page itself
   rather than lifted out of the file, so what is asserted is what the browser loaded. */

const TRAINER = "/pages/fitness/";

/* The page asks its sheet for the plan on load. No spec here wants that answer — one
   asserts what happens without it, and the rest are about what the trainer does with
   whatever plan it has — so the suite never reaches Google, on a train or otherwise. */
test.beforeEach(async ({ page }) => {
  await page.route("**/docs.google.com/**", (asked) => asked.abort());
});

test("the trainer writes a workout in the session grammar", async ({
  page,
}) => {
  await page.goto(TRAINER);

  const written = await page.evaluate(() => {
    type Logged = {
      n: string;
      w: number;
      done: number;
      r: number;
      reps: number[];
    };
    const draw = (
      window as unknown as { sessionText: (ex: Logged[]) => string }
    ).sessionText;
    return {
      equal: draw([{ n: "Snatch", w: 24, done: 3, r: 10, reps: [10, 10, 10] }]),
      uneven: draw([{ n: "Snatch", w: 24, done: 3, r: 10, reps: [10, 10, 8] }]),
      bodyweight: draw([
        { n: "Push-up", w: 0, done: 2, r: 12, reps: [12, 12] },
      ]),
      /* Two exercises are two headings, separated by a blank line. */
      both: draw([
        { n: "Snatch", w: 24, done: 1, r: 10, reps: [10] },
        { n: "Halo", w: 12, done: 2, r: 8, reps: [8, 8] },
      ]),
    };
  });

  expect(written.equal).toBe("# Snatch 24 kg\n3 sets of 10\n");
  expect(written.uneven).toBe("# Snatch 24 kg\nsets of 10 / 10 / 8\n");
  expect(written.bodyweight).toBe("# Push-up bw\n2 sets of 12\n");
  expect(written.both).toBe(
    "# Snatch 24 kg\n1 sets of 10\n\n# Halo 12 kg\n2 sets of 8\n",
  );
});

test("a workout finished in the trainer becomes a document of the fitness field", async ({
  page,
}) => {
  const named = new Date();
  const two = (n: number) => String(n).padStart(2, "0");
  const today = `${named.getFullYear()}-${two(named.getMonth() + 1)}-${two(named.getDate())}`;
  // named for its moment: the day, then the time it was saved at
  const saved = new RegExp(`^${today}-\\d{2}-\\d{2}-\\d{2}\\.md$`);

  await page.goto(TRAINER);
  /* One set of the first exercise: the control carries the rep count, and pressing it
     is how a set is logged. Which field it is saved into is the path it was opened
     under — the plugin never writes its own name into the page — and the strip below
     says which one took it. */
  await page.locator(".set").first().click();
  await expect(page.locator(".set.on")).toHaveCount(1);

  page.once("dialog", (asked) => asked.accept());
  await page.getByRole("button", { name: /FINISH/i }).click();

  await expect(page.getByRole("button", { name: /^saved$/i })).toBeVisible({
    timeout: 15_000,
  });

  /* And it is a document of that field, which is the whole point of writing it: the
     shell lists it, and cora can be asked about it. */
  await fresh(page);
  await page
    .getByRole("group", { name: "Answer in" })
    .getByRole("button", { name: "Plugin" })
    .click();
  await page.getByRole("button", { name: "fitness", exact: true }).click();
  await expect(page.getByRole("button", { name: saved })).toBeVisible();
});

/** A workout into the field, as the finish writes one — so a spec can say what the
 *  field already holds before the trainer is opened. */
async function held(
  page: import("@playwright/test").Page,
  name: string,
  text: string,
) {
  const put = await page.request.post("/api/documents", {
    multipart: {
      file: { name, mimeType: "text/markdown", buffer: Buffer.from(text) },
      scope: "fitness",
    },
  });
  expect(put.ok(), await put.text()).toBeTruthy();
}

const TODAY = (() => {
  const now = new Date();
  const two = (n: number) => String(n).padStart(2, "0");
  return `${now.getFullYear()}-${two(now.getMonth() + 1)}-${two(now.getDate())}`;
})();

test("the History is the log the field holds", async ({ page }) => {
  /* Late in the day, so this save is the newest whatever else the run has written. */
  await held(
    page,
    `${TODAY}-23-59-58-Snatch day.md`,
    "Snatch day\n\n# One-arm kettlebell snatch 24 kg\n3 sets of 10\n",
  );

  await page.goto(TRAINER);
  await page.getByRole("button", { name: /history/i }).click();

  const first = page.locator(".ses").first();
  await expect(first).toContainText("Snatch day");
  await expect(first).toContainText("One-arm kettlebell snatch");
  await expect(first).toContainText("24 kg");
  await expect(first).toContainText("3×10");
  /* And none of it is the page's: what it shows, it read. */
  expect(
    await page.evaluate(() => globalThis.localStorage.getItem("kb.hist")),
  ).toBeNull();
});

test("a save whose name is only in its filename is named all the same", async ({
  page,
}) => {
  /* The name reaches a save two ways: written above the headings by the finish, and
     carried by the filename. A save that has only the second is still that workout. */
  await held(
    page,
    `${TODAY}-23-59-57-Jerk day.md`,
    "# One-arm kettlebell jerk 20 kg\n2 sets of 6\n",
  );

  await page.goto(TRAINER);
  await page.getByRole("button", { name: /history/i }).click();

  await expect(
    page.locator(".ses").filter({ hasText: "Jerk day" }),
  ).toHaveCount(1);
});

test("a fresh workout opens on the weight the field last saw", async ({
  page,
}) => {
  /* The plan's first exercise, saved heavier and shorter than the plan asks for. */
  await held(
    page,
    `${TODAY}-23-59-59-Heavy pass.md`,
    "# Kettlebell around-the-body pass 28 kg\nsets of 7 / 7 / 7\n",
  );

  await page.goto(TRAINER);

  await expect(page.locator(".wt .val")).toContainText("28");
  await expect(page.locator(".sets .log").first()).toHaveText("7");
});

/** The field's listing, held until a spec lets it go — so a spec can say what the page
 *  does in the window before its first read of the field lands. */
function slowly(page: import("@playwright/test").Page) {
  let release: () => void;
  const gate = new Promise<void>((r) => {
    release = r;
  });
  const routed = page.route(
    (url) => url.pathname === "/api/documents" && url.search.includes("scope="),
    async (asked) => {
      await gate;
      await asked.continue();
    },
  );
  return routed.then(() => release);
}

test("a weight dialled before the field is read is the lifter's own", async ({
  page,
}) => {
  await held(
    page,
    `${TODAY}-23-59-56-Light pass.md`,
    "# Kettlebell around-the-body pass 12 kg\n3 sets of 10\n",
  );
  const release = await slowly(page);

  await page.goto(TRAINER);
  /* Dialled, and nothing logged — which is exactly the workout the read would take
     for untouched and overwrite with the field's own weights. */
  const shown = await page.locator(".wt .val").textContent();
  await page.locator(".wt button").last().click();
  const dialled = String(Number(shown?.replace(/\D/g, "")) + 1);
  await expect(page.locator(".wt .val")).toContainText(dialled);

  release();

  await page.getByRole("button", { name: /history/i }).click();
  await expect(
    page.locator(".ses").filter({ hasText: "Light pass" }),
  ).toHaveCount(1);
  await page.getByRole("button", { name: /close/i }).click();
  await expect(page.locator(".wt .val")).toContainText(dialled);
});

test("one exercise dialled leaves the rest to the field", async ({ page }) => {
  /* Two of the plan's exercises, both saved heavier than the plan asks for. */
  await held(
    page,
    `${TODAY}-23-59-51-Two heavy.md`,
    "# Kettlebell around-the-body pass 26 kg\n3 sets of 10\n\n" +
      "# Around-the-body pass with a stop 30 kg\n3 sets of 10\n",
  );
  const release = await slowly(page);

  await page.goto(TRAINER);
  /* The first exercise is dialled before the read lands. It is the lifter's. */
  await page.locator(".wt button").last().click();
  const dialled = await page.locator(".wt .val").textContent();

  release();
  await expect(page.locator(".wt .val")).toContainText(
    String(dialled?.replace(/\D/g, "")),
  );

  /* The second was not touched, so it is still the field's to say. */
  await page.getByRole("button", { name: "›" }).click();
  await expect(page.locator(".wt .val")).toContainText("30");
});

test("a workout stored before the page knew about ownership is not wiped", async ({
  page,
}) => {
  await held(
    page,
    `${TODAY}-23-59-50-Was here.md`,
    "# Kettlebell around-the-body pass 22 kg\n3 sets of 10\n",
  );
  /* A session as the previous page wrote one: sets logged, and no word about who
     touched it — which a read must not read as "nobody". */
  await page.addInitScript(() => {
    globalThis.localStorage.setItem(
      "kb.ses",
      JSON.stringify({
        start: Date.now(),
        v: 2,
        ex: { vragir: { done: 2, w: 18, reps: [10, 10, 10] } },
      }),
    );
  });

  await page.goto(TRAINER);

  await expect(page.locator(".set.on")).toHaveCount(2);
  await expect(page.locator(".wt .val")).toContainText("18");
});

test("a History opened before the field is read fills when it lands", async ({
  page,
}) => {
  await held(
    page,
    `${TODAY}-23-59-53-Late read.md`,
    "# Halo 10 kg\n1 sets of 5\n",
  );
  const release = await slowly(page);

  await page.goto(TRAINER);
  await page.getByRole("button", { name: /history/i }).click();
  await expect(page.locator(".empty")).toBeVisible();

  release();

  await expect(
    page.locator(".ses").filter({ hasText: "Late read" }),
  ).toHaveCount(1);
});

test("a finish tapped while its save is out uploads the workout once", async ({
  page,
}) => {
  await page.goto(TRAINER);
  let uploads = 0;
  let release: () => void;
  const gate = new Promise<void>((r) => {
    release = r;
  });
  await page.route("**/api/documents", async (asked) => {
    if (asked.request().method() !== "POST") return asked.continue();
    uploads += 1;
    await gate;
    return asked.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        document: "saved.md",
        chunks: 1,
        scope: "fitness",
      }),
    });
  });
  await page.locator(".set").first().click();

  page.once("dialog", (asked) => asked.accept());
  await page.getByRole("button", { name: /^finish$/i }).click();

  /* The session is cleared only once cora has answered, so the control has to say the
     save is out — otherwise a second tap sends the same workout again. */
  const saving = page.getByRole("button", { name: /saving/i });
  await expect(saving).toBeVisible();
  await expect(saving).toBeDisabled();
  release!();
  await expect(page.getByRole("button", { name: /^saved$/i })).toBeVisible();
  expect(uploads, "the workout went to cora once").toBe(1);
});

test("the finish is never offered again for a workout cora already took", async ({
  page,
}) => {
  await held(
    page,
    `${TODAY}-23-59-52-Already in.md`,
    "# Halo 10 kg\n1 sets of 5\n",
  );
  await page.goto(TRAINER);

  /* The save lands at once and the read of the field behind it does not. Between the
     two the workout is cora's, and the page must not offer to send it again. */
  let uploads = 0;
  await page.route("**/api/documents", async (asked) => {
    if (asked.request().method() !== "POST") return asked.continue();
    uploads += 1;
    return asked.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        document: "saved.md",
        chunks: 1,
        scope: "fitness",
      }),
    });
  });
  const release = await slowly(page);
  await page.locator(".set").first().click();

  page.once("dialog", (asked) => asked.accept());
  await page.getByRole("button", { name: /^finish$/i }).click();

  /* The send is over — and cora took it. Whatever the control says from here, it is
     not an enabled finish, and a tap on it sends nothing: the workout is in the field
     already, and the read that follows it is the page catching up, not the save. */
  await expect(page.getByRole("button", { name: /saving/i })).toHaveCount(0);
  await expect(page.getByRole("button", { name: /^finish$/i })).toHaveCount(0);
  await page.locator("#finish").click({ force: true });
  release();

  await expect(page.getByRole("button", { name: /^saved$/i })).toBeVisible();
  expect(uploads, "the workout went to cora once").toBe(1);
});

test("a document that carries markup is read as text", async ({ page }) => {
  /* A field takes documents from anyone who can upload into it, and the trainer now
     draws their headings. They are text. */
  await held(
    page,
    `${TODAY}-23-59-55-Marked up.md`,
    "# <b>Swing</b> 10 kg\n1 sets of 5\n",
  );

  await page.goto(TRAINER);
  await page.getByRole("button", { name: /history/i }).click();

  const line = page
    .locator(".ses")
    .filter({ hasText: "Marked up" })
    .locator("li");
  await expect(line).toContainText("<b>Swing</b>");
  /* One bold: the reps the page writes, and not the one the document asked for. */
  await expect(line.locator("b")).toHaveCount(1);
});

test("a save is read back in the grammar the finish wrote it in", async ({
  page,
}) => {
  await page.goto(TRAINER);

  /* Read in the page rather than through the field, because what the field holds is
     what every other spec in this file has been saving into it — an assertion that
     depends on which of them ran is an assertion about nothing. */
  const read = await page.evaluate(() => {
    type Save = {
      name: string;
      ex: { n: string; w: number; reps: number[] }[];
    };
    const parse = (window as unknown as { readSession: (t: string) => Save })
      .readSession;
    return {
      named: parse("Snatch day\n\n# Swing 24 kg\n3 sets of 10\n"),
      uneven: parse("# Swing 24 kg\nsets of 10 / 10 / 8\n").ex[0],
      bodyweight: parse("# Push-up bw\n2 sets of 12\n").ex[0],
      /* A document of the field is anyone's to write, so neither of these is trusted:
         a load that is not a number, and a set count no screen could draw. */
      odd: parse("# Swing 1.2.3 kg\n1 sets of 5\n").ex[0],
      vast: parse("# Swing 20 kg\n999999999 sets of 5\n").ex[0],
    };
  });

  expect(read.named.name).toBe("Snatch day");
  expect(read.named.ex).toEqual([{ n: "Swing", w: 24, reps: [10, 10, 10] }]);
  expect(read.uneven.reps).toEqual([10, 10, 8]);
  expect(read.bodyweight).toEqual({ n: "Push-up", w: 0, reps: [12, 12] });
  expect(read.odd.w, "a load that is not a number is no load").toBe(0);
  expect(
    read.vast.reps.length,
    "a set count the page cannot draw does not become an array",
  ).toBeLessThanOrEqual(20);
});

test("a read still out when a later one lands does not undo it", async ({
  page,
}) => {
  /* Two reads of the field are in the air whenever a save completes before the read
     the page opened with. The older one must not put the log back as it was. */
  let calls = 0;
  await page.route(
    (url) => url.pathname === "/api/documents" && url.search.includes("scope="),
    async (asked) => {
      calls += 1;
      if (calls === 1) await new Promise((r) => setTimeout(r, 3000));
      await asked.continue();
    },
  );

  await page.goto(TRAINER);
  await page.locator(".set").first().click();
  page.once("dialog", (asked) => asked.accept());
  await page.getByRole("button", { name: /^finish$/i }).click();
  await expect(page.getByRole("button", { name: /^saved$/i })).toBeVisible();

  /* The read the page opened with lands last, carrying a listing taken before the
     save existed. */
  await page.waitForTimeout(3500);
  await page.getByRole("button", { name: /history/i }).click();
  await expect(page.locator(".ses").first()).toContainText(
    "Kettlebell around-the-body pass",
  );
});

test("a save cora would not take leaves the workout standing", async ({
  page,
}) => {
  await page.goto(TRAINER);
  /* cora refusing the upload, which is the one failure the reader cannot act on
     themselves: the field is where the workout lives, and it did not get there. */
  await page.route("**/api/documents", (asked) =>
    asked.request().method() === "POST"
      ? asked.fulfill({
          status: 400,
          contentType: "application/json",
          body: JSON.stringify({ error: "that field takes no documents" }),
        })
      : asked.continue(),
  );
  await page.locator(".set").first().click();

  page.once("dialog", (asked) => asked.accept());
  await page.getByRole("button", { name: /FINISH/i }).click();

  await expect(page.locator("#warn")).toContainText("Not saved to cora");
  /* And it is still the reader's to finish again: the set is logged and the control
     that saves it is still the finish, not a fresh workout's "no sets logged yet". */
  await expect(page.locator(".set.on")).toHaveCount(1);
  await expect(page.getByRole("button", { name: /^finish$/i })).toBeEnabled();
  expect(
    await page.evaluate(() => globalThis.localStorage.getItem("kb.hist")),
  ).toBeNull();
});

test("a workout with nothing logged is not saved, and says so", async ({
  page,
}) => {
  await page.goto(TRAINER);
  let asked = 0;
  await page.route("**/api/documents", (call) => {
    asked += 1;
    return call.continue();
  });

  /* No set logged: there is nothing to hand over, so there is nothing to press. */
  await expect(
    page.getByRole("button", { name: /no sets logged yet/i }),
  ).toBeDisabled();
  expect(asked, "nothing was uploaded").toBe(0);
});

test("the workout's name is read off the sheet export's filename", async ({
  page,
}) => {
  await page.goto(TRAINER);

  /* The header as Google really sends it: a plain filename that says nothing, and the
     encoded one that names the document and the tab. The tab is what the save is titled
     with. */
  const named = await page.evaluate(() => {
    const read = (
      window as unknown as { workoutName: (header: string | null) => string }
    ).workoutName;
    const header =
      "attachment; filename=\"-.csv\"; filename*=UTF-8''" +
      "%D0%9F%D1%80%D0%BE%D0%B3%D1%80%D0%B0%D0%BC%D0%BC%D0%B0%20%D0%9E%D0%B1%D1%83%D1%87" +
      "%D0%B5%D0%BD%D0%B8%D0%B5%20%D1%80%D1%8B%D0%B2%D0%BA%D1%83%20%20-%20" +
      "%D0%A0%D1%8B%D0%B2%D0%BE%D0%BA%20%D0%B3%D0%B8%D1%80%D0%B8.csv";
    return [read(header), read('attachment; filename="-.csv"'), read(null)];
  });

  expect(named).toEqual(["Рывок гири", "", ""]);
});

test("the plan is read from the sheet the page is pointed at", async ({
  page,
}) => {
  await page.goto(TRAINER);

  /* The parsing, against the columns the sheet really has — headers in the owner's own
     language, a name column spelled two ways, and a row with no exercise on it. The
     fetch itself is not exercised here: a suite that reached Google would fail on a
     train. */
  const read = await page.evaluate(() => {
    const draw = (
      window as unknown as {
        planFromCSV: (
          csv: string,
        ) => { n: string; s: number; r: number; w: number }[];
      }
    ).planFromCSV;
    return draw(
      [
        "Подходы,Повторы,Вес снаряда,Упрожнение,Длинное видео,Короткое видео",
        "4,12,16,Рывок,https://youtu.be/kEBDdhJNhZc,https://youtu.be/7FJh9pIZirs",
        ",,,,,",
        "3,10,24,Толчок,https://youtu.be/XdQ_DaAYI2k,",
      ].join("\n"),
    );
  });

  expect(read.map((each) => [each.n, each.s, each.r, each.w])).toEqual([
    ["Рывок", 4, 12, 16],
    ["Толчок", 3, 10, 24],
  ]);
});

test("a sheet that cannot be read leaves the plan the page ships with", async ({
  page,
}) => {
  /* The one failure a lifter in a gym actually has: no signal — which is how every
     spec here runs. The plan already in the page is what they train from, and the strip
     says why it is that one. */
  await page.goto(TRAINER);

  await expect(page.locator("#warn")).toContainText("Sheet unavailable");
  /* And the exercises are the shipped ones, named as the coach speaks. */
  await expect(page.locator(".row .nm").first()).toHaveText(
    "Kettlebell around-the-body pass",
  );
});

test("a sheet that changes under a running workout leaves what was logged", async ({
  page,
}) => {
  await page.goto(TRAINER);
  const clip = [{ l: "Full", v: "kEBDdhJNhZc" }];
  const plan = (ids: string[]) =>
    ids.map((id) => ({
      id,
      s: 3,
      r: 10,
      w: 16,
      n: `Exercise ${id}`,
      vids: clip,
    }));

  /* A plan of this spec's own, so what is asserted is what a changed sheet does to
     progress rather than what the shipped plan happens to be. */
  await page.evaluate(
    (given) =>
      (window as unknown as { adoptPlan: (p: unknown[]) => void }).adoptPlan(
        given,
      ),
    plan(["a", "b"]),
  );
  await page.locator(".set").first().click();
  await expect(page.locator(".set.on")).toHaveCount(1);

  /* The sheet gained an exercise while the lifter was working. What they have already
     done is theirs, and an exercise still in the plan keeps it. */
  await page.evaluate(
    (given) =>
      (window as unknown as { adoptPlan: (p: unknown[]) => void }).adoptPlan(
        given,
      ),
    plan(["c", "a", "b"]),
  );

  await expect(page.locator(".row", { hasText: "Exercise c" })).toBeVisible();
  await expect(page.locator(".set.on")).toHaveCount(1);
});

test("a clip plays in the frame rather than sending the lifter to another tab", async ({
  page,
}) => {
  await page.goto(TRAINER);
  const clip = [{ l: "Full", v: "kEBDdhJNhZc", t: 42 }];
  await page.evaluate(
    (given) =>
      (window as unknown as { adoptPlan: (p: unknown[]) => void }).adoptPlan(
        given,
      ),
    [{ id: "a", s: 3, r: 10, w: 16, n: "Exercise a", vids: clip }],
  );

  await page.locator(".thumb").first().click();

  /* In the frame, not a link out of it: a lifter mid-set is not going to come back from
     another tab, and the clip is the thing they opened the trainer to see. */
  const player = page.locator(".stage iframe");
  await expect(player).toBeVisible();
  const src = await player.getAttribute("src");
  expect(src).toContain("kEBDdhJNhZc");
  expect(src, "it starts where the plan says it does").toContain("start=42");
  expect(src, "and asks the host that sets no cookie").toContain(
    "youtube-nocookie.com",
  );
  await expect(page.locator('.stage a[href*="youtube.com/watch"]')).toHaveCount(
    0,
  );
});

/* ---- the rep counter -------------------------------------------------------------
   The counter is fed one landmark frame a call, the way the pose loop feeds it off the
   camera. These build the frames by hand, so nothing here needs a camera or the model.
   Image y grows downward, so a wrist overhead is a small y and a wrist at the hip a
   large one. */

type Point = { x: number; y: number };
type Frame = Point[] | null;

type Body = {
  wrist: Point;
  cx?: number;
  shoulder?: number;
  hip?: number;
};

/* A pose the counter can read. Only the shoulders, hips and wrists carry anything; the
   rest is filler so the array indexes the way BlazePose's does. */
function pose(of: Body): Point[] {
  const cx = of.cx ?? 0.5;
  const sy = of.shoulder ?? 0.3;
  const hy = of.hip ?? 0.7;
  const lm: Point[] = Array.from({ length: 33 }, () => ({ x: cx, y: 0.5 }));
  lm[11] = { x: cx - 0.1, y: sy };
  lm[12] = { x: cx + 0.1, y: sy };
  lm[23] = { x: cx - 0.08, y: hy };
  lm[24] = { x: cx + 0.08, y: hy };
  lm[15] = of.wrist;
  lm[16] = of.wrist;
  return lm;
}

const PER = 30;

/* `n` cycles of a movement, thirty frames each by default — a second a rep, the pace of
   the plan's slower lifts. Phase nought is the bottom, where a lifter starts. */
function cycles(
  n: number,
  at: (phase: number) => Frame,
  per: number = PER,
): Frame[] {
  return Array.from({ length: n * per }, (_, i) =>
    at(((i % per) / per) * 2 * Math.PI),
  );
}

/* A snatch: the wrist travels from the hip to overhead and back, the torso still. */
const snatch = (phase: number): Frame =>
  pose({ wrist: { x: 0.5, y: 0.45 + 0.3 * Math.cos(phase) } });

/* Hands the frames to the page one at a time, at the rate the camera delivers them. */
async function feed(page: Page, frames: Frame[]): Promise<void> {
  await page.evaluate((given) => {
    const counter = window as unknown as {
      repReset: () => void;
      repSaw: (lm: unknown, now: number) => void;
    };
    counter.repReset();
    given.forEach((lm, i) => counter.repSaw(lm, (i * 1000) / 30));
  }, frames);
}

test("the camera counts the reps it sees", async ({ page }) => {
  test.fail(); // the counter is not written yet

  await page.goto(TRAINER);
  await feed(page, cycles(3, snatch));

  await expect(page.locator("#repnum")).toHaveText("3");
});

test("the count starts at nought", async ({ page }) => {
  await page.goto(TRAINER);
  await feed(page, []);

  await expect(page.locator("#repnum")).toHaveText("0");
});

test("a wrist swinging up and back counts one a cycle", async ({ page }) => {
  await page.goto(TRAINER);
  await feed(page, cycles(4, snatch));

  await expect(page.locator("#repnum")).toHaveText("4");
});

/* The same snatch filmed from twice as far: every length halves, and the counter
   divides by the torso, so the two sequences are one signal. */
const distant = (phase: number): Frame =>
  pose({
    wrist: { x: 0.5, y: 0.475 + 0.15 * Math.cos(phase) },
    shoulder: 0.4,
    hip: 0.6,
  });

test("the same swing further from the camera counts the same", async ({
  page,
}) => {
  await page.goto(TRAINER);
  await feed(page, cycles(4, distant));

  await expect(page.locator("#repnum")).toHaveText("4");
});

/* A lifter walking back to the bell: the whole body travels, nothing moves within it. */
const walking = (phase: number): Frame => {
  const cx = 0.3 + 0.2 * Math.cos(phase);
  return pose({ wrist: { x: cx, y: 0.6 }, cx });
};

test("a body crossing the frame is not counted", async ({ page }) => {
  await page.goto(TRAINER);
  await feed(page, cycles(4, walking));

  await expect(page.locator("#repnum")).toHaveText("0");
});

/* A push-up: the wrists are planted on the floor and the torso travels to meet them,
   which is the same signal read the other way round. */
const pushUp = (phase: number): Frame => {
  const drop = 0.12 * Math.cos(phase);
  return pose({
    wrist: { x: 0.5, y: 0.92 },
    shoulder: 0.35 + drop,
    hip: 0.65 + drop,
  });
};

test("a torso moving over planted wrists counts one a cycle", async ({
  page,
}) => {
  await page.goto(TRAINER);
  await feed(page, cycles(4, pushUp));

  await expect(page.locator("#repnum")).toHaveText("4");
});

/* Shifting weight between the feet: rhythmic, and nowhere near a repetition. */
const fidget = (phase: number): Frame =>
  pose({ wrist: { x: 0.5, y: 0.6 + 0.02 * Math.cos(phase) } });

test("a swing too small to be a rep is not counted", async ({ page }) => {
  await page.goto(TRAINER);
  await feed(page, cycles(4, fidget));

  await expect(page.locator("#repnum")).toHaveText("0");
});

test("turning points closer together than a rep are counted once", async ({
  page,
}) => {
  await page.goto(TRAINER);
  /* Twelve cycles at six frames each: five a second, which no lifter does and the
     counter will not accept. Four fifths of a second of that is one rep at most. */
  await feed(page, cycles(12, snatch, 6));

  const seen = Number(await page.locator("#repnum").textContent());
  expect(seen, "the movement was seen").toBeGreaterThan(0);
  expect(seen, "but not once a cycle").toBeLessThanOrEqual(
    Math.ceil((12 * 6 * (1000 / 30)) / 350),
  );
});

test("frames the model found nobody in are skipped, not counted", async ({
  page,
}) => {
  await page.goto(TRAINER);
  /* The same snatch with every seventh frame lost — the clock does not stop, so what
     is missing is the pose and not the time. */
  await feed(
    page,
    cycles(4, snatch).map((lm, i) => (i % 7 === 0 ? null : lm)),
  );

  await expect(page.locator("#repnum")).toHaveText("4");
});
