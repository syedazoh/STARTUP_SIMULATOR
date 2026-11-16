// Disposable native-auth business, real Vite UI/API and fixture model only.
const { chromium } = require("playwright");
const assert = require("node:assert/strict");
(async () => {
  const browser = await chromium.launch({ headless: true });
  const api = await browser.newContext();
  const request = api.request;
  const email = `review-${Date.now()}@example.com`,
    password = "fixture-password";
  let response = await request.post("http://127.0.0.1:8001/api/auth/register", {
    data: { email, password },
  });
  assert.equal(response.status(), 201);
  response = await request.post("http://127.0.0.1:8001/api/auth/login", {
    data: { email, password },
  });
  assert.equal(response.status(), 200);
  const token = (await response.json()).access_token,
    headers = { Authorization: "Bearer " + token };
  response = await request.post("http://127.0.0.1:8001/api/businesses", {
    headers,
    data: {
      company_name: "Polling and revision acceptance",
      industry: "Software",
    },
  });
  assert.equal(response.status(), 201);
  const business = (await response.json()).id;
  response = await request.post(
    `http://127.0.0.1:8001/api/businesses/${business}/agents/finance/actions/budget-request`,
    { headers, data: { amount: 1000 } },
  );
  assert.equal(response.status(), 200);
  const task = (await response.json()).id;
  // Vite is started immediately before this step.
  for (let i = 0; i < 60; i++) {
    try {
      const r = await request.get("http://127.0.0.1:5173/login");
      if (r.ok()) break;
    } catch {}
    await new Promise((r) => setTimeout(r, 500));
  }
  await api.clearCookies();
  const page = await api.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("http://127.0.0.1:5173/login");
  await page.getByLabel("Email", { exact: true }).fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await page.waitForURL(`**/b/${business}/dashboard`);
  await page.goto(`http://127.0.0.1:5173/b/${business}/dashboard`);
  const agentCount = page.locator(".hq-kpi").nth(1).locator("strong");
  await page.waitForFunction(() =>
    document.querySelectorAll(".hq-kpi strong")[1]?.textContent.includes("5"),
  );
  await page.waitForFunction(
    () =>
      !document
        .querySelectorAll(".hq-kpi strong")[3]
        ?.textContent.includes("—"),
  );
  await page.evaluate(() => {
    window.counterSamples = [];
    for (const index of [1, 3]) {
      const node = document.querySelectorAll(".hq-kpi strong")[index];
      new MutationObserver(() =>
        window.counterSamples.push(node.textContent),
      ).observe(node, { subtree: true, childList: true, characterData: true });
    }
  });
  // Observe several actual 1.8-second dashboard polls, not just the initial render.
  await page.waitForTimeout(6500);
  assert.match(await agentCount.textContent(), /5/);
  assert.equal(
    (await page.evaluate(() => window.counterSamples)).some((value) =>
      value.includes("—"),
    ),
    false,
  );
  console.log(
    "Agent/event counters stay visible across repeated HTTP refreshes",
  );
  await page
    .getByLabel("Requested changes or rejection reason")
    .fill("Lower to 400");
  await page
    .getByRole("button", { name: "Request changes", exact: true })
    .click();
  await page
    .getByText(/amount: 400/)
    .first()
    .waitFor();
  response = await request.get(`http://127.0.0.1:8001/api/tasks/${task}`, {
    headers,
  });
  let saved = await response.json();
  assert.equal(saved.payload.amount, 400);
  assert.equal(saved.previous_payload.amount, 1000);
  assert.equal(saved.status, "pending_approval");
  assert.equal(saved.result, null);
  await page.getByRole("button", { name: "Approve", exact: true }).click();
  for (let i = 0; i < 30; i++) {
    saved = await (
      await request.get(`http://127.0.0.1:8001/api/tasks/${task}`, { headers })
    ).json();
    if (saved.status === "executed") break;
    await page.waitForTimeout(300);
  }
  assert.equal(saved.status, "executed");
  assert.equal(saved.payload.amount, 400);
  assert.deepEqual(errors, []);
  await page.screenshot({
    path:
      (process.env.WORKSPACE_SCREENSHOT_DIR || "/tmp/workspace-screenshots") +
      "/legacy-review.png",
    fullPage: true,
  });
  console.log(
    "Feedback changes 1000 to 400, keeps the proposal pending, and executes only after a new owner approval",
  );
  await browser.close();
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
