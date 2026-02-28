import { test, expect } from "@playwright/test";

/**
 * Basic smoke tests – verify the app loads and critical elements exist.
 */

test.describe("Smoke tests", () => {
  test("page loads successfully", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveTitle(/Aquafin/i);
  });

  test("navigation element exists", async ({ page }) => {
    await page.goto("/");
    const nav = page.locator("nav");
    await expect(nav).toBeVisible();
  });

  test("page does not return a server error", async ({ page }) => {
    const response = await page.goto("/");
    expect(response).not.toBeNull();
    expect(response!.status()).toBeLessThan(500);
  });
});
