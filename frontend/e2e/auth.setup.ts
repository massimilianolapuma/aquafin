import { test as setup } from "@playwright/test";

/**
 * Authentication setup placeholder.
 *
 * In production E2E, this would authenticate via Clerk using
 * `@clerk/testing` or a mock strategy. For now it's a no-op
 * placeholder that can be referenced as a setup project.
 *
 * @see https://playwright.dev/docs/auth
 */

setup("authenticate", async ({ page }) => {
  // TODO: Implement Clerk mock authentication
  // Example using @clerk/testing:
  //   await clerk.signIn({ identifier: "test@example.com", password: "..." });
  //   await page.context().storageState({ path: ".auth/user.json" });
  console.log("Auth setup placeholder – skipping authentication");
});
