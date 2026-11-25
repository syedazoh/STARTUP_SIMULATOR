// Disposable local provider/database fixture only. No production accounts.
const { chromium } = require("playwright");
const assert = require("node:assert/strict");
(async () => {
  const fs = require("node:fs");
  const screenshots =
    process.env.WORKSPACE_SCREENSHOT_DIR || "/tmp/workspace-screenshots";
  fs.mkdirSync(screenshots, { recursive: true });
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH,
    args: ["--no-sandbox"],
  });
  const page = await browser.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("http://127.0.0.1:3000/login?method=password");
  await page.getByLabel("Email address").fill("demo@example.com");
  await page.getByLabel("Password", { exact: true }).fill("test-password");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await page.waitForURL("**/workspace");
  await page.getByText("Create a business", { exact: true }).click();
  await page.getByLabel("Company name").fill("Browser Acceptance Startup");
  await page.getByLabel("Industry", { exact: true }).fill("Software");
  await page.getByRole("button", { name: "Create workspace" }).click();
  await page.waitForURL(/workspace\/[\w-]+$/);
  await page
    .getByRole("heading", { name: "Browser Acceptance Startup", exact: true })
    .waitFor();
  console.log("Business creation and command center loaded");
  await page.getByRole("button", { name: "Finance", exact: true }).click();
  await page.getByLabel("Requested amount", { exact: true }).fill("25");
  await page.getByRole("button", { name: "Submit proposal" }).click();
  await page
    .getByRole("button", { name: "Review owner decision" })
    .first()
    .waitFor();
  await page
    .getByRole("button", { name: "Review owner decision" })
    .first()
    .click();
  await page.getByRole("button", { name: "Approve and execute" }).click();
  await page.getByText("Approval processed.", { exact: false }).waitFor();
  await page.getByText("executed", { exact: true }).first().waitFor();
  console.log(
    "Finance proposal, explicit approval, saved execution and report passed",
  );
  await page
    .getByLabel("Business goal")
    .fill("Launch our new product with all four departments");
  await page.getByRole("button", { name: "Generate draft plan" }).click();
  await page
    .getByRole("button", { name: "Review activation" })
    .first()
    .waitFor();
  await page.getByRole("button", { name: "Review activation" }).first().click();
  await page.getByRole("button", { name: "Confirm activation" }).click();
  await page
    .getByText("Plan activation processed.", { exact: false })
    .waitFor();
  await page
    .getByRole("button", { name: "All departments", exact: true })
    .click();
  await page.getByText("Prepare supplies", { exact: true }).first().waitFor();
  console.log(
    "CEO draft, reviewed activation and delegated department tasks passed",
  );
  await page.reload();
  await page.getByText("Prepare supplies", { exact: true }).first().waitFor();
  const id = page.url().split("/").pop();
  for (const width of [320, 768, 1440]) {
    await page.setViewportSize({ width, height: 1000 });
    assert.ok(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
      `overflow ${width}`,
    );
    await page.screenshot({
      path: screenshots + `/width-${width}.png`,
      fullPage: true,
    });
  }
  await page.screenshot({ path: screenshots + "/desktop.png", fullPage: true });
  const other = await browser.newContext();
  const second = await other.newPage();
  await second.goto("http://127.0.0.1:3000/login?method=password");
  await second.getByLabel("Email address").fill("other@example.com");
  await second.getByLabel("Password", { exact: true }).fill("test-password");
  await second.getByRole("button", { name: "Sign in", exact: true }).click();
  await second.waitForURL("**/workspace");
  assert.equal(
    await second
      .getByText("Browser Acceptance Startup", { exact: true })
      .count(),
    0,
  );
  await second.goto("http://127.0.0.1:3000/workspace/" + id);
  await second
    .getByText("You do not have access to this business or task.", {
      exact: true,
    })
    .waitFor();
  assert.equal(
    await second.getByRole("button", { name: "Submit proposal" }).count(),
    0,
  );
  console.log(
    "Reload persistence in fixture, responsive overflow and second-user isolation passed",
  );
  assert.deepEqual(errors, []);
  await browser.close();
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
