# Zepto Selector Reference

## Selector Priority

Use selectors in this order. Fall back to the next tier only when the previous fails.

## Primary Selectors (Most Reliable)

These use `data-testid` attributes - least likely to break:

| Element       | Selector                             | Notes                         |
| ------------- | ------------------------------------ | ----------------------------- |
| Cart Button   | `[data-testid="cart-btn"]`           | Header cart icon              |
| Cart Count    | `[data-testid="cart-items-number"]`  | Badge showing item count      |
| User Address  | `[data-testid="user-address"]`       | Current delivery address text |
| Delivery Time | `[data-testid="delivery-time"]`      | ETA in header                 |
| Address Item  | `[data-testid="address-item"]`       | Saved address in modal        |
| Address Modal | `[data-testid="address-modal"]`      | Location selection popup      |
| Address List  | `[data-testid="saved-address-list"]` | Container for addresses       |
| Search Input  | `[data-testid="search-bar-icon"]`    | Search bar link               |
| My Account    | `[data-testid="my-account"]`         | Profile text                  |

## Secondary Selectors (Slot-Based)

These use `data-slot-id` - stable within product cards:

| Element         | Selector                               | Notes                        |
| --------------- | -------------------------------------- | ---------------------------- |
| Product Image   | `[data-slot-id="ProductImageWrapper"]` | Contains img and ADD button  |
| Price Container | `[data-slot-id="EdlpPrice"]`           | Has current + original price |
| Product Name    | `[data-slot-id="ProductName"]`         | Product title text           |
| Pack Size       | `[data-slot-id="PackSize"]`            | Quantity/weight info         |
| ETA             | `[data-slot-id="EtaInformation"]`      | Delivery time estimate       |
| Sponsor Tag     | `[data-slot-id="SponsorTag"]`          | "Ad" indicator               |

## Tertiary Selectors (Text/Attribute Based)

Fallbacks when data-* selectors fail:

| Element      | Selector                             | Notes                     |
| ------------ | ------------------------------------ | ------------------------- |
| Product Link | `a[href*="/pn/"]`                    | All product cards         |
| ADD Button   | `button:has-text("ADD")`             | Add to cart (not in cart) |
| Decrease Qty | `[aria-label*="Decrease"]`           | Item IS in cart           |
| Increase Qty | `[aria-label*="Increase"]`           | Item IS in cart           |
| Location Btn | `button:has-text("Select Location")` | No address set            |
| Home Address | `button:has-text("home")`            | Address is set            |
| Cart (text)  | `button:has-text("Cart")`            | Fallback cart button      |

## Emergency Selectors (Last Resort)

When everything else fails, use structural patterns:

```javascript
// Find any clickable product card
'div[data-variant="edlp"]';

// Find price by currency symbol
'span:has-text("₹")';

// Find buttons in product area
'a[href*="/pn/"] button';

// Find cart drawer
'aside, [role="dialog"], [class*="Drawer"], [class*="cart"]';
```

## Product Card DOM Structure

Understanding the DOM hierarchy helps when building custom selectors:

```
a[href*="/pn/"]                              // Product card link
├── div[data-variant="edlp"]                 // Card container
│   ├── div[data-slot-id="ProductImageWrapper"]
│   │   ├── img[alt="Product Name"]          // Product image
│   │   └── button (ADD or quantity control) // Action button
│   ├── div[data-slot-id="EdlpPrice"]
│   │   ├── span (current price)             // e.g., "₹88"
│   │   └── span (original price)            // e.g., "₹125" (strikethrough)
│   ├── div[data-slot-id="ProductName"]
│   │   └── span (product name text)
│   ├── div[data-slot-id="PackSize"]
│   │   └── span (size info)                 // e.g., "1 pc (350 ml)"
│   └── div[data-slot-id="EtaInformation"]   // e.g., "7 mins"
```

## Detecting Cart State

**Item NOT in cart** (shows ADD button):
```javascript
const addBtn = product.locator('button:has-text("ADD")');
const notInCart = await addBtn.count() > 0;
```

**Item IS in cart** (shows quantity controls):
```javascript
const qtyControls = product.locator('[aria-label*="Decrease"]');
const inCart = await qtyControls.count() > 0;
```

## Chaining Selectors

For precision, chain selectors:

```javascript
// Find ADD button within specific product
const product = page.locator('a[href*="/pn/"]').nth(0);
const addBtn = product.locator('button:has-text("ADD")');

// Find price within product card
const price = product.locator('[data-slot-id="EdlpPrice"] span:first-child');

// Find product name from image alt
const name = await product.locator('img[alt]').getAttribute('alt');
```
