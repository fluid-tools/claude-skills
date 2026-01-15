# Zepto Fallback Strategies

## Selector Chain Pattern

Try multiple selectors in order until one works:

```javascript
async function findElement(page, selectorChain) {
  /**
   * Try multiple selectors in order until one works
   * @param {Array} selectorChain - Array of {selector, description} objects
   */
  for (const { selector, description } of selectorChain) {
    try {
      const el = page.locator(selector).first();
      if ((await el.count()) > 0) {
        console.log(`Found via: ${description}`);
        return el;
      }
    } catch (e) {
      continue;
    }
  }
  return null;
}

// Example: Find cart button with fallbacks
const cartBtn = await findElement(page, [
  { selector: '[data-testid="cart-btn"]', description: "data-testid" },
  { selector: 'button:has-text("Cart")', description: "text content" },
  {
    selector: 'button:has([data-testid="cart-items-number"])',
    description: "has badge",
  },
  { selector: "header button:last-child", description: "structural position" },
]);
```

## When DOM Structure Changes

Use multiple strategies to extract data:

```javascript
async function findProductPrice(productEl) {
  // Strategy 1: data-slot-id
  let price = await productEl
    .locator('[data-slot-id="EdlpPrice"] span:first-child')
    .textContent()
    .catch(() => null);
  if (price) return price;

  // Strategy 2: Currency pattern
  price = await productEl.evaluate((el) => {
    const spans = el.querySelectorAll("span");
    for (const span of spans) {
      if (/^₹\d+$/.test(span.textContent.trim())) {
        return span.textContent;
      }
    }
    return null;
  });
  if (price) return price;

  // Strategy 3: Regex on all text
  const allText = await productEl.textContent();
  const match = allText.match(/₹(\d+)/);
  return match ? `₹${match[1]}` : null;
}
```

## When Modals Don't Open

Retry with increasing timeouts and alternative click methods:

```javascript
async function openModal(page, triggerSelector, modalSelector, retries = 3) {
  for (let i = 0; i < retries; i++) {
    // Click trigger
    await page.click(triggerSelector);

    // Wait for modal with increasing timeout
    const timeout = 1500 * (i + 1);
    try {
      await page.waitForSelector(modalSelector, { timeout });
      return true;
    } catch (e) {
      console.log(`Modal attempt ${i + 1} failed, retrying...`);

      // Try alternative: force click via JS
      if (i === 1) {
        await page.evaluate((sel) => {
          const btn = document.querySelector(sel);
          if (btn) btn.click();
        }, triggerSelector);
      }

      await page.waitForTimeout(500);
    }
  }
  return false;
}
```

## When Accessibility Snapshot Misses Modal Content

React portals and dynamic rendering can cause `accessibilitySnapshot()` to miss modal content.

```javascript
// Workaround 1: Use getCleanHTML instead
const html = await getCleanHTML({ locator: page, search: /modal|address/i });

// Workaround 2: Direct DOM access via evaluate
const content = await page.evaluate(() => {
  return document.querySelector('[data-testid="address-modal"]')?.innerHTML;
});

// Workaround 3: Wait longer for React hydration
await page.waitForTimeout(2000);
const snapshot = await accessibilitySnapshot({ page });
```

## Known Issues & Workarounds

### 1. Cart Doesn't Persist

**Symptom**: Cart empties between page loads or sessions

**Cause**: Session-based storage, cookies expire

**Workaround**:
```javascript
// Add all items in single flow, don't navigate away
// Complete checkout immediately after adding items
// Don't refresh page unnecessarily
```

### 2. Web/App Cart Don't Sync

**Symptom**: Items added on web don't appear in mobile app

**Cause**: Separate session storage systems

**Workaround**:
```javascript
// Complete entire checkout flow on web
// Don't expect app to show web cart items
```

### 3. Location Modal Not Opening

**Symptom**: Clicking "Select Location" does nothing

**Cause**: React hydration delay, event handlers not attached

**Workaround**:
```javascript
// Wait longer after page load (2-3 seconds)
await page.waitForTimeout(2500);
await page.click('button:has-text("Select Location")');

// Or try JavaScript click
await page.evaluate(() => {
  document.querySelector('button[aria-label*="Location"]')?.click();
});
```

### 4. Products Show But Can't Add

**Symptom**: Products visible but ADD buttons don't work

**Cause**: No delivery address selected for that location

**Workaround**:
```javascript
// Always select address FIRST before searching
await selectAddress(page, "home");
// Then search
await page.goto("https://www.zepto.com/search?query=...");
```

### 5. Search Returns Wrong Products

**Symptom**: Search for "monster energy" returns unrelated items

**Cause**: Zepto's search includes sponsored/related products

**Workaround**:
```javascript
// Filter by checking product name contains query terms
const products = await page.locator('a[href*="/pn/"]').all();
for (const p of products) {
  const name = await p.locator("img").getAttribute("alt");
  if (name.toLowerCase().includes("monster")) {
    await p.locator('button:has-text("ADD")').click();
    break;
  }
}
```

### 6. Stale Element References

**Symptom**: "Element is not attached to DOM" errors

**Cause**: React re-renders replaced the element

**Workaround**:
```javascript
// Re-query elements after any action that might cause re-render
await page.click('[data-testid="cart-btn"]');
await page.waitForTimeout(500);

// Re-query instead of reusing old reference
const freshElement = page.locator('[data-testid="cart-items-number"]');
const count = await freshElement.textContent();
```

## Recovery Patterns

### Full Page Refresh Recovery

When state is corrupted, start fresh:

```javascript
async function recoverSession(page) {
  // Clear and refresh
  await page.goto("https://www.zepto.com/", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(3000);
  
  // Re-select address
  const needsLocation = await page
    .locator('button:has-text("Select Location")')
    .count() > 0;
  
  if (needsLocation) {
    await selectAddress(page, "home");
  }
  
  return { recovered: true };
}
```

### Retry with Backoff

For flaky operations:

```javascript
async function retryWithBackoff(fn, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (e) {
      if (i === maxRetries - 1) throw e;
      const delay = Math.pow(2, i) * 1000; // 1s, 2s, 4s
      console.log(`Retry ${i + 1}/${maxRetries} after ${delay}ms`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
}

// Usage
const result = await retryWithBackoff(() => addToCart(page, "monster energy"));
```

## Summary: When Things Go Wrong

| Issue | First Try | If That Fails |
|-------|-----------|---------------|
| Element not found | Use selector chain | Wait longer, check visibility |
| Modal won't open | Wait 2-3s, retry | Use JS click |
| Cart empty | Check session | Refresh page, re-login |
| Products not loading | Select address | Check network errors |
| ADD button fails | Check if already in cart | Force click, retry |
| Stale element | Re-query element | Wait for re-render |
