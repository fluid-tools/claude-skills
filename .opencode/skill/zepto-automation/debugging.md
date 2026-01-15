# Zepto Debugging Playbook

## Debug Empty Cart

Use when cart shows empty but items should be there.

```javascript
async function debugEmptyCart(page) {
  console.log("=== DEBUGGING EMPTY CART ===");

  // 1. Check URL
  console.log("URL:", page.url());

  // 2. Check cart badge
  const badge = await page
    .locator('[data-testid="cart-items-number"]')
    .textContent()
    .catch(() => "NOT_FOUND");
  console.log("Cart badge:", badge);

  // 3. Check for cart tooltip
  const tooltip = await page
    .locator('[role="tooltip"]')
    .textContent()
    .catch(() => "NOT_FOUND");
  console.log("Tooltip:", tooltip);

  // 4. Check cookies/storage
  const cookies = await page.context().cookies();
  console.log("Cookies count:", cookies.length);
  console.log(
    "Has session cookie:",
    cookies.some((c) => c.name.includes("session"))
  );

  // 5. Check if logged in
  const address = await page
    .locator('[data-testid="user-address"]')
    .textContent()
    .catch(() => "NOT_FOUND");
  console.log("Address:", address);

  return {
    url: page.url(),
    cartBadge: badge,
    tooltip,
    cookiesCount: cookies.length,
    address,
  };
}
```

**Common causes:**
- Session expired
- Address not selected
- Different browser profile
- Cookies cleared

## Debug Product Search

Use when products aren't loading or search returns wrong results.

```javascript
async function debugProductSearch(page, query) {
  console.log("=== DEBUGGING PRODUCT SEARCH ===");

  // 1. Check current URL
  console.log("URL:", page.url());
  console.log(
    "Expected query in URL:",
    page.url().includes(encodeURIComponent(query))
  );

  // 2. Check if address is set (required for products)
  const locationBtn = await page
    .locator('button:has-text("Select Location")')
    .count();
  console.log("Needs location:", locationBtn > 0);

  // 3. Check for loading states
  const loading = await page
    .locator('[class*="loading"], [class*="skeleton"]')
    .count();
  console.log("Loading elements:", loading);

  // 4. Check for products
  const products = await page.locator('a[href*="/pn/"]').count();
  console.log("Products found:", products);

  // 5. Check for "no results"
  const noResults = await page.locator("text=/no results|not found/i").count();
  console.log("No results message:", noResults > 0);

  // 6. Check network
  const errors = await page.evaluate(() => {
    return window.performance
      .getEntriesByType("resource")
      .filter((r) => r.responseStatus >= 400)
      .map((r) => ({ url: r.name, status: r.responseStatus }));
  });
  console.log("Failed requests:", errors);

  return {
    locationNeeded: locationBtn > 0,
    products,
    noResults: noResults > 0,
    errors,
  };
}
```

**Common causes:**
- Address not selected (most common!)
- Query too specific
- Network errors
- Page still loading

## Debug ADD Button

Use when clicking ADD doesn't work.

```javascript
async function debugAddButton(page, productIndex = 0) {
  console.log("=== DEBUGGING ADD BUTTON ===");

  const product = page.locator('a[href*="/pn/"]').nth(productIndex);

  // 1. Check product exists
  const exists = await product.count();
  console.log("Product exists:", exists > 0);
  if (!exists) return { error: "PRODUCT_NOT_FOUND" };

  // 2. Check for ADD button
  const addBtn = product.locator('button:has-text("ADD")');
  const addBtnCount = await addBtn.count();
  console.log("ADD button exists:", addBtnCount > 0);

  // 3. If no ADD, check for quantity controls (already in cart)
  if (!addBtnCount) {
    const qtyControls = await product
      .locator('[aria-label*="Decrease"]')
      .count();
    console.log("Already in cart:", qtyControls > 0);
    if (qtyControls) return { status: "ALREADY_IN_CART" };
  }

  // 4. Check button visibility
  const isVisible = await addBtn.isVisible().catch(() => false);
  console.log("Button visible:", isVisible);

  // 5. Check if button is disabled
  const isDisabled = await addBtn.isDisabled().catch(() => false);
  console.log("Button disabled:", isDisabled);

  // 6. Check for out of stock
  const outOfStock = await product
    .locator("text=/out of stock|unavailable/i")
    .count();
  console.log("Out of stock:", outOfStock > 0);

  // 7. Try clicking with force
  if (addBtnCount && isVisible && !isDisabled) {
    await addBtn.click({ force: true });
    await page.waitForTimeout(1000);
    const newCount = await page
      .locator('[data-testid="cart-items-number"]')
      .textContent()
      .catch(() => "0");
    console.log("Cart count after click:", newCount);
  }

  return {
    addBtnExists: addBtnCount > 0,
    isVisible,
    isDisabled,
    outOfStock: outOfStock > 0,
  };
}
```

**Common causes:**
- Item already in cart (shows +/- instead of ADD)
- Item out of stock
- Button not yet interactive (hydration)
- Wrong product index

## Master Debug Function

Comprehensive diagnostic for any Zepto issue.

```javascript
async function debugZepto(page) {
  const report = {
    timestamp: new Date().toISOString(),
    url: page.url(),
    checks: {},
  };

  // 1. Page loaded
  report.checks.pageLoaded = (await page.locator("body").count()) > 0;

  // 2. Zepto header present
  report.checks.headerPresent =
    (await page.locator('header, banner, [role="banner"]').count()) > 0;

  // 3. Authentication state
  report.checks.hasAddress =
    (await page.locator('[data-testid="user-address"]').count()) > 0;
  report.checks.needsLocation =
    (await page.locator('button:has-text("Select Location")').count()) > 0;

  // 4. Cart state
  report.checks.cartBadge = await page
    .locator('[data-testid="cart-items-number"]')
    .textContent()
    .catch(() => null);
  report.checks.cartEmpty =
    report.checks.cartBadge === null || report.checks.cartBadge === "0";

  // 5. Products visible (if on search page)
  if (page.url().includes("/search")) {
    report.checks.productsCount = await page.locator('a[href*="/pn/"]').count();
  }

  // 6. Errors on page
  report.checks.consoleErrors = await page.evaluate(() => {
    return (window.__ZEPTO_ERRORS__ || []).slice(-5);
  });

  // 7. Key elements
  report.elements = {
    cartBtn: await page.locator('[data-testid="cart-btn"]').count(),
    searchBar: await page
      .locator('[data-testid="search-bar-icon"], input[role="combobox"]')
      .count(),
    profileLink: await page.locator('a[href="/account"]').count(),
  };

  console.log("=== ZEPTO DEBUG REPORT ===");
  console.log(JSON.stringify(report, null, 2));

  return report;
}
```

## Quick Diagnostic Checklist

Run these checks in order when something isn't working:

```javascript
// Quick health check
async function quickCheck(page) {
  const checks = {
    // Can we see the page?
    pageLoaded: await page.locator('body').count() > 0,
    
    // Is address set?
    addressSet: await page.locator('[data-testid="user-address"]').count() > 0,
    needsLocation: await page.locator('button:has-text("Select Location")').count() > 0,
    
    // What's in cart?
    cartCount: await page.locator('[data-testid="cart-items-number"]')
      .textContent().catch(() => '0'),
    
    // Are we on the right page?
    url: page.url(),
    isSearchPage: page.url().includes('/search'),
    isCartOpen: page.url().includes('cart=open'),
  };
  
  // Diagnose
  if (checks.needsLocation) {
    console.log("ACTION NEEDED: Select address first");
  }
  if (checks.isSearchPage && !checks.addressSet) {
    console.log("WARNING: Products may not load without address");
  }
  
  return checks;
}
```

## Interpreting Results

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `needsLocation: true` | No address selected | Call `selectAddress()` |
| `products: 0` on search page | Address not set | Select address first |
| `addBtnExists: false` | Item already in cart | Check for quantity controls |
| `cartBadge: null` | Session expired | Refresh page, re-login |
| `outOfStock: true` | Item unavailable | Try different product |
| `isVisible: false` | Element off-screen | Scroll or wait longer |
