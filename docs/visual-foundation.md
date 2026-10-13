# CivicOne — Visual Foundation & Design System Guidelines

**Theme:** Authority Navy / Civic Blue / Accessible White  
**Target Release:** Compatible with ServiceNow Next Experience & Workspace UI  
**Accessibility Level:** WCAG 2.1 AA Compliant  

---

## 1. Palette & Token Hierarchy

The visual system is engineered for public sector credibility, high legibility in field environments, and accessibility across diverse citizen user bases.

### 1.1 Brand & Neutral Surfaces
| Token | Hex Value | Usage |
| :--- | :--- | :--- |
| `--civic-navy-dark` | `#081B33` | Executive headers, high-contrast text |
| `--civic-navy-primary` | `#0B2545` | Primary navigation, headers, brand anchors |
| `--civic-navy-light` | `#134074` | Active navigation tabs, secondary headings |
| `--civic-blue-primary` | `#0066CC` | Interactive actions, primary CTA buttons |
| `--civic-blue-hover` | `#0052A3` | Hover / focus state for interactive controls |
| `--civic-blue-subtle` | `#E6F0FA` | Selected table row highlight, banner background |
| `--civic-bg-canvas` | `#F4F7FB` | Base page canvas background |
| `--civic-bg-surface` | `#FFFFFF` | Card surface, table cards, modal dialogs |
| `--civic-border-subtle` | `#D0DBE5` | Default card and divider borders |
| `--civic-border-medium` | `#A0B2C6` | Form input borders and secondary dividers |

### 1.2 Status Color Semantics (High Legibility & WCAG AA)
| Semantic State | Background | Text Color | Border Color | Typical Usage |
| :--- | :--- | :--- | :--- | :--- |
| **Critical** | `#FEE2E2` | `#991B1B` | `#F87171` | Live wire, gas leak, contaminated water, SLA Breach |
| **Warning** | `#FEF3C7` | `#92400E` | `#FBBF24` | SLA 75% warning, duplicate suspect review |
| **In Progress** | `#E0F2FE` | `#075985` | `#38BDF8` | Assigned, under field inspection, work underway |
| **Success** | `#DCFCE7` | `#166534` | `#4ADE80` | Confirmed resolved, SLA met, closed successfully |

---

## 2. Typography Guidelines

- **Base Font Family:** `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`
- **Monospace & Number Font Family:** Tabular Numerals `ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace`
- **Case Numbers:** All grievance case identifiers (`CIV0001001`, `MGR0001001`) use tabular mono numerals for aligned scanning.
- **Hierarchy:**
  - `H1 / Page Title`: 24px (`1.5rem`), Semi-bold (600), Navy Primary
  - `H2 / Section Title`: 20px (`1.25rem`), Semi-bold (600), Navy Primary
  - `Body Text`: 16px (`1rem`), Regular (400), Slate 900 (`#0F172A`)
  - `Metadata / Captions`: 12px (`0.75rem`), Medium (500), Muted Slate (`#64748B`)

---

## 3. Motion & Accessibility

- **Animation Token Scale:** Micro-transitions at `150ms` and `250ms` using cubic-bezier timing `(0.4, 0, 0.2, 1)`.
- **Strict Reduced-Motion Compliance:**
  ```css
  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
      animation-duration: 0.01ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: 0.01ms !important;
      scroll-behavior: auto !important;
    }
  }
  ```
- **Focus Rings:** Mandatory 2px offset focus rings on all interactive components for keyboard accessibility.
