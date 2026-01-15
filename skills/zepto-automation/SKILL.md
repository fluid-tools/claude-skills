---
name: zepto-automation
description: "Automate Zepto grocery orders via Playwright browser automation. Use when user asks to search products, add items to cart, check cart contents, select delivery address, order groceries, buy food, or debug Zepto automation issues. Triggers on: grocery shopping, Zepto, food delivery, cart management, product search."
allowed-tools:
  - playwriter_execute
  - playwriter_reset
  - Read
  - Bash
---

# Zepto Grocery Automation

Browser automation skill for Zepto grocery delivery. Designed for AI agents using Playwright/Playwriter MCP.

## Quick Start

Minimum viable flow to add an item to cart:

```javascript
// 1. Navigate
await page.goto("https://www.zepto.com/");
await page.waitForTimeout(2000);

// 2. Select address (if needed)
await page.click('button:has-text("Select Location")');
await page.waitForTimeout(1500);
await page.locator('[data-testid="address-item"]').first().click();

// 3. Search & add item
await page.goto("https://www.zepto.com/search?query=monster+energy");
await page.waitForTimeout(2000);
await page
  .locator('a[href*="/pn/"]')
  .first()
  .locator('button:has-text("ADD")')
  .click();

// 4. Verify cart
const count = await page
  .locator('[data-testid="cart-items-number"]')
  .textContent();
console.log("Items in cart:", count);
```

## Critical Facts

| Fact             | Value                                       |
| ---------------- | ------------------------------------------- |
| Base URL         | `https://www.zepto.com`                     |
| Search URL       | `https://www.zepto.com/search?query={TERM}` |
| Cart URL         | `https://www.zepto.com/?cart=open`          |
| **Orders URL**   | `https://www.zepto.com/account/orders`      |
| Paan Corner URL  | `https://www.zepto.com/cn/paan-corner/...`  |
| Typical Delivery | 7-16 minutes (varies by location)           |
| Cart Persistence | Session-based (may persist after order!)    |
| Web/App Sync     | **NO** - separate sessions                  |

## Architecture Overview

```
zepto.com
├── Header (banner)
│   ├── Logo (link to /)
│   ├── Location Button (Select Location / Current Address)
│   ├── Search Bar (link to /search or combobox)
│   ├── Profile Link (/account)
│   └── Cart Button (with badge count)
├── Category Navigation (All, Cafe, Home, Toys, Fresh, etc.)
├── Main Content
│   ├── Search Results (product grid)
│   └── Home Page (carousels, promotions)
└── Cart Drawer (aside/dialog when open)
    ├── Header (Cart title, savings banner)
    ├── Items List (with quantity controls)
    ├── Bill Summary (totals, fees, discounts)
    └── Checkout Section
```

## Core Operations

| Operation | Purpose | Details |
|-----------|---------|---------|
| `isLoggedIn()` | Check authentication state | [operations.md](operations.md#check-login-status) |
| `selectAddress()` | Select delivery address | [operations.md](operations.md#select-address) |
| `searchProducts()` | Search and extract products | [operations.md](operations.md#search-products) |
| `addToCart()` | Add item to cart | [operations.md](operations.md#add-item-to-cart) |
| `getCart()` | Get cart contents | [operations.md](operations.md#get-cart-contents) |
| `orderItems()` | Complete order flow | [operations.md](operations.md#complete-order-flow) |
| `checkoutWithCOD()` | Checkout with Cash on Delivery | [operations.md](operations.md#complete-checkout-with-cod) |
| `verifyOrderPlaced()` | Verify order on Orders page | [operations.md](operations.md#verify-order-placed) |

## Selector Strategy

Use selectors in priority order:

1. **Primary** (`data-testid`) - Most stable, rarely change
2. **Secondary** (`data-slot-id`) - Stable within product cards
3. **Tertiary** (text/attribute) - Fallback when data-* fails
4. **Emergency** (structural) - Last resort

See [selectors.md](selectors.md) for complete reference.

## Critical Lessons

### Order Verification (IMPORTANT!)

> **After placing an order, the cart may still show items.**
> This does NOT mean the order failed! Cart state doesn't always clear immediately.

| ❌ Wrong Way | ✅ Right Way |
|--------------|--------------|
| Check if cart is empty | Navigate to `/account/orders` |
| Assume cart items = order failed | Look for "Order getting packed" |

**Always verify orders on the Orders page:**
```javascript
await page.goto('https://www.zepto.com/account/orders');
// Look for: "Order getting packed", "Order placed", etc.
```

### Smoking Products / Smoothmix

Herbal smoking products (smoothmix, etc.) are NOT searchable directly:
- **Location**: Paan Corner → Smoking Accessories → "Smoking Blend" filter
- **Direct search "smoothmix" returns nothing**
- Must navigate to category and apply filter

## When Things Go Wrong

### Common Issues

| Issue | Quick Fix |
|-------|-----------|
| Cart shows empty | Check session, re-select address |
| Products not loading | Select address first |
| ADD button not working | Check if already in cart (shows +/- controls) |
| Modal not opening | Wait longer (2-3s), try JS click |
| Cart shows items after order | **Normal!** Verify on Orders page instead |
| Smoothmix not found in search | Go to Paan Corner → Smoking Accessories → Smoking Blend filter |

### Debugging

See [debugging.md](debugging.md) for diagnostic functions:
- `debugEmptyCart()` - Diagnose cart issues
- `debugProductSearch()` - Diagnose search issues
- `debugAddButton()` - Diagnose add-to-cart issues
- `debugZepto()` - Master diagnostic

### Fallback Strategies

See [fallbacks.md](fallbacks.md) for recovery patterns when primary approaches fail.

## Workflow Pattern

```
1. Navigate to zepto.com
2. Select address (REQUIRED before product operations)
3. Search for products
4. Add items to cart
5. Verify cart contents
6. Proceed to checkout (Click to Pay)
7. Select payment method (UPI/Card/COD)
8. Confirm order
9. **VERIFY on Orders page** (NOT cart!)
```

**Critical Rules**:
- Always select address FIRST. Products won't display correctly without a delivery location set.
- After checkout, **ALWAYS verify on `/account/orders`** - cart state is unreliable.
- For smoking products, navigate to Paan Corner category instead of searching.
