# Design System Quick Reference Guide

A comprehensive guide for using the Face Attendance modern SaaS design system.

---

## 🎨 1. Buttons

### Primary Button (Main Actions)
```html
<button class="btn btn-primary rounded-pill px-4 fw-semibold shadow-sm">
    <i class="mdi mdi-plus"></i>
    <span>Add New</span>
</button>
```

### Secondary Button (Outline)
```html
<button class="btn btn-outline-primary rounded-pill px-3">
    <i class="mdi mdi-pencil"></i>
    <span>Edit</span>
</button>
```

### Success Button
```html
<button class="btn btn-success rounded-pill px-4 fw-semibold shadow-sm">
    <i class="mdi mdi-check"></i>
    <span>Confirm</span>
</button>
```

### Danger Button
```html
<button class="btn btn-danger rounded-pill px-3">
    <i class="mdi mdi-delete"></i>
    <span>Delete</span>
</button>
```

### Small Button
```html
<button class="btn btn-primary btn-sm rounded-pill px-3">
    <i class="mdi mdi-eye"></i>
    <span>View</span>
</button>
```

**Rules:**
- Always use `rounded-pill` for modern look
- Add `fw-semibold` for better readability
- Use `shadow-sm` on primary actions
- Include icon + text (not just icon)
- Padding: `px-4` (default), `px-3` (small)

---

## 📦 2. Cards

### Basic Card
```html
<div class="card border-0 shadow-sm rounded-3">
    <div class="card-body p-4">
        <!-- Content -->
    </div>
</div>
```

### Card with Header
```html
<div class="card border-0 shadow-sm rounded-3">
    <div class="card-header bg-white border-0 p-4">
        <div class="d-flex align-items-center gap-3">
            <div class="bg-primary bg-opacity-10 rounded-3" style="width: 48px; height: 48px; display: flex; align-items: center; justify-content: center;">
                <i class="mdi mdi-icon text-primary fs-4"></i>
            </div>
            <div>
                <h2 class="h5 mb-0 fw-bold">Card Title</h2>
                <p class="text-muted small mb-0">Card subtitle or description</p>
            </div>
        </div>
    </div>
    <div class="card-body p-4">
        <!-- Content -->
    </div>
</div>
```

### Notification Card Item
```html
<div class="border rounded-3 p-4 mb-3" style="background: #fafbfc; border-color: #e2e8f0 !important;">
    <div class="d-flex align-items-start gap-3">
        <div class="bg-primary bg-opacity-10 rounded-circle" style="width: 40px; height: 40px; display: flex; align-items: center; justify-content: center;">
            <i class="mdi mdi-information text-primary"></i>
        </div>
        <div class="flex-grow-1">
            <h4 class="h6 fw-bold text-dark mb-2">Title</h4>
            <div class="text-muted">Content goes here...</div>
            <div class="mt-3 d-flex align-items-center gap-3 text-muted small">
                <span><i class="mdi mdi-account-circle"></i> Author</span>
                <span>•</span>
                <span><i class="mdi mdi-clock-outline"></i> Date</span>
            </div>
        </div>
    </div>
</div>
```

**Rules:**
- Always use `border-0 shadow-sm rounded-3`
- Card body padding: `p-4`
- Card header: `bg-white border-0 p-4`

---

## 📏 3. Layout

### Page Structure
```html
{% extends "admin/base_admin_dashboard.html" %}

{% block content %}
<div class="container-fluid py-4">
    <!-- Page Header -->
    <div class="row mb-4">
        <div class="col-12">
            <div class="d-flex justify-content-between align-items-center flex-wrap gap-3">
                <div>
                    <h1 class="h3 fw-bold mb-1">Page Title</h1>
                    <p class="text-muted mb-0">Page description</p>
                </div>
                <a href="#" class="btn btn-primary rounded-pill px-4 fw-semibold shadow-sm">
                    <i class="mdi mdi-plus"></i>
                    <span>Action</span>
                </a>
            </div>
        </div>
    </div>

    <!-- Main Content -->
    <div class="row g-4">
        <div class="col-12">
            <!-- Cards go here -->
        </div>
    </div>
</div>
{% endblock %}
```

### Two Column Layout
```html
<div class="row g-4">
    <div class="col-lg-8">
        <!-- Main content -->
    </div>
    <div class="col-lg-4">
        <!-- Sidebar -->
    </div>
</div>
```

### Three Column Layout
```html
<div class="row g-4">
    <div class="col-lg-4">
        <div class="card border-0 shadow-sm rounded-3">
            <!-- Card 1 -->
        </div>
    </div>
    <div class="col-lg-4">
        <div class="card border-0 shadow-sm rounded-3">
            <!-- Card 2 -->
        </div>
    </div>
    <div class="col-lg-4">
        <div class="card border-0 shadow-sm rounded-3">
            <!-- Card 3 -->
        </div>
    </div>
</div>
```

**Rules:**
- Use `container-fluid py-4` for page wrapper
- Use `row g-4` for grid with gutters
- Page header margin: `mb-4`
- Sections margin: `mb-4` or `mb-3`

---

## 📊 4. Tables

### Modern Table
```html
<div class="table-responsive">
    <table class="table table-hover align-middle mb-0">
        <thead class="bg-light">
            <tr>
                <th class="fw-semibold">Column 1</th>
                <th class="fw-semibold">Column 2</th>
                <th class="text-center fw-semibold">Actions</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Data 1</td>
                <td>Data 2</td>
                <td class="text-center">
                    <div class="d-flex gap-2 justify-content-center">
                        <button class="btn btn-sm btn-outline-primary rounded-pill px-3">
                            <i class="mdi mdi-pencil"></i>
                            <span>Edit</span>
                        </button>
                        <button class="btn btn-sm btn-danger rounded-pill px-3">
                            <i class="mdi mdi-delete"></i>
                            <span>Delete</span>
                        </button>
                    </div>
                </td>
            </tr>
        </tbody>
    </table>
</div>
```

### Table with Badges
```html
<td>
    <span class="badge bg-primary bg-opacity-10 text-primary fw-semibold">ID-001</span>
</td>
```

### Table with Avatar
```html
<td>
    <div class="d-flex align-items-center gap-2">
        <div class="bg-primary bg-opacity-10 rounded-circle" style="width: 32px; height: 32px; display: flex; align-items: center; justify-content: center;">
            <i class="mdi mdi-account text-primary"></i>
        </div>
        <span class="fw-medium">John Doe</span>
    </div>
</td>
```

**Rules:**
- Use `table-hover` for hover effects
- Use `align-middle` for vertical centering
- Header: `bg-light` with `fw-semibold`
- Wrap in `table-responsive` for mobile

---

## 🔢 5. Pagination

### Modern Pagination
```html
<div class="d-flex justify-content-between align-items-center mt-4 pt-3 border-top">
    <div class="text-muted small">
        Page 1 / 10
    </div>
    <nav>
        <ul class="pagination pagination-sm mb-0">
            <li class="page-item">
                <a class="page-link rounded-pill me-1" href="?page=1">
                    <i class="mdi mdi-chevron-double-left"></i>
                </a>
            </li>
            <li class="page-item">
                <a class="page-link rounded-pill mx-1" href="?page=1">1</a>
            </li>
            <li class="page-item active">
                <a class="page-link rounded-pill mx-1" href="?page=2">2</a>
            </li>
            <li class="page-item">
                <a class="page-link rounded-pill mx-1" href="?page=3">3</a>
            </li>
            <li class="page-item">
                <a class="page-link rounded-pill ms-1" href="?page=10">
                    <i class="mdi mdi-chevron-double-right"></i>
                </a>
            </li>
        </ul>
    </nav>
</div>
```

**Rules:**
- Use `rounded-pill` for page links
- Use icon chevrons for navigation
- Show page counter on left
- Add `border-top` separator

---

## 🎯 6. Icons & Badges

### Icon with Background
```html
<div class="bg-primary bg-opacity-10 rounded-3" style="width: 48px; height: 48px; display: flex; align-items: center; justify-content: center;">
    <i class="mdi mdi-icon text-primary fs-4"></i>
</div>
```

### Circular Icon
```html
<div class="bg-primary bg-opacity-10 rounded-circle" style="width: 40px; height: 40px; display: flex; align-items: center; justify-content: center;">
    <i class="mdi mdi-icon text-primary"></i>
</div>
```

### Status Badges
```html
<!-- Success -->
<span class="badge bg-success">Active</span>

<!-- Warning -->
<span class="badge bg-warning text-dark">Pending</span>

<!-- Danger -->
<span class="badge bg-danger">Inactive</span>

<!-- Primary -->
<span class="badge bg-primary bg-opacity-10 text-primary fw-semibold">ID-001</span>
```

**Rules:**
- Icon backgrounds: `bg-{color} bg-opacity-10`
- Icon colors match background: `text-{color}`
- Sizes: 40px (small), 48px (medium), 80px (large)

---

## 📝 7. Forms

### Form Input with Icon
```html
<div class="mb-4">
    <label for="input-id" class="form-label fw-medium">Label</label>
    <div class="input-group">
        <span class="input-group-text bg-light border-end-0">
            <i class="mdi mdi-icon"></i>
        </span>
        <input type="text" class="form-control border-start-0" id="input-id" placeholder="Enter...">
    </div>
</div>
```

### Search Input
```html
<div class="input-group">
    <span class="input-group-text bg-light border-end-0">
        <i class="mdi mdi-magnify text-muted"></i>
    </span>
    <input type="text" class="form-control border-start-0 ps-0" placeholder="Search...">
</div>
```

**Rules:**
- Labels: `fw-medium`
- Icon container: `bg-light border-end-0`
- Input: `border-start-0` to merge with icon
- Margin bottom: `mb-4`

---

## 🎨 8. Empty States

### Empty State Design
```html
<div class="text-center py-5">
    <div class="mb-4">
        <div class="d-inline-flex align-items-center justify-content-center bg-light rounded-circle" style="width: 80px; height: 80px;">
            <i class="mdi mdi-icon text-muted" style="font-size: 2.5rem;"></i>
        </div>
    </div>
    <h5 class="fw-semibold mb-2">No Items Found</h5>
    <p class="text-muted mb-4">There are no items to display.</p>
    <a href="#" class="btn btn-primary rounded-pill px-4">
        <i class="mdi mdi-plus"></i>
        <span>Add New Item</span>
    </a>
</div>
```

**Rules:**
- Large icon: 80px circle with 2.5rem icon
- Clear heading: `h5 fw-semibold`
- Description: `text-muted`
- Action button below

---

## 🚨 9. Alerts

### Alert Styles
```html
<!-- Danger -->
<div class="alert alert-danger d-flex align-items-center gap-2">
    <i class="mdi mdi-alert-circle"></i>
    <span>Error message here</span>
</div>

<!-- Success -->
<div class="alert alert-success d-flex align-items-center gap-2">
    <i class="mdi mdi-check-circle"></i>
    <span>Success message here</span>
</div>

<!-- Warning -->
<div class="alert alert-warning d-flex align-items-center gap-2">
    <i class="mdi mdi-alert"></i>
    <span>Warning message here</span>
</div>
```

**Rules:**
- Always include icon
- Use `d-flex align-items-center gap-2`
- Keep messages concise

---

## 📐 10. Spacing Scale

### Usage
```html
<!-- Margin Bottom -->
<div class="mb-1">Very small spacing (4px)</div>
<div class="mb-2">Small spacing (8px)</div>
<div class="mb-3">Medium spacing (12px)</div>
<div class="mb-4">Large spacing (16px)</div>
<div class="mb-5">Extra large spacing (24px)</div>

<!-- Padding -->
<div class="p-2">Small padding</div>
<div class="p-3">Medium padding</div>
<div class="p-4">Large padding (standard for cards)</div>

<!-- Gap (Flexbox) -->
<div class="d-flex gap-2">Tight gap</div>
<div class="d-flex gap-3">Normal gap</div>
<div class="d-flex gap-4">Wide gap</div>
```

**Standard Spacing:**
- **Cards:** `p-4`
- **Page wrapper:** `py-4`
- **Grid gutter:** `g-4`
- **Section margins:** `mb-4`
- **Item margins:** `mb-3`
- **Icon gaps:** `gap-2` or `gap-3`

---

## 🎨 11. Color Usage

### Text Colors
```html
<p class="text-primary">Primary text</p>
<p class="text-success">Success text</p>
<p class="text-danger">Danger text</p>
<p class="text-warning">Warning text</p>
<p class="text-muted">Muted text</p>
<p class="text-dark">Dark text</p>
```

### Background Colors
```html
<div class="bg-primary text-white">Primary background</div>
<div class="bg-primary bg-opacity-10 text-primary">Light primary background</div>
<div class="bg-light">Light background</div>
<div class="bg-white">White background</div>
```

**Rules:**
- Body text: default color or `text-muted`
- Headings: `text-dark` or default
- Highlights: `text-primary`
- Status: `text-success`, `text-danger`, `text-warning`

---

## ✍️ 12. Typography

### Headings
```html
<h1 class="h3 fw-bold mb-1">Page Title</h1>
<h2 class="h5 mb-0 fw-bold">Section Title</h2>
<h4 class="h6 fw-bold text-dark mb-2">Card Title</h4>
```

### Paragraphs
```html
<p class="text-muted mb-0">Subtitle or description</p>
<p class="text-muted small">Small text</p>
```

**Font Weights:**
- `fw-bold` (700): Page titles, headings
- `fw-semibold` (600): Buttons, labels, sub-headings
- `fw-medium` (500): Form labels, table headers
- Default (400): Body text

---

## 🔧 13. Utilities

### Flexbox
```html
<!-- Center align -->
<div class="d-flex align-items-center justify-content-center">

<!-- Space between -->
<div class="d-flex justify-content-between align-items-center">

<!-- With gap -->
<div class="d-flex align-items-center gap-3">

<!-- Wrap on mobile -->
<div class="d-flex flex-wrap gap-3">
```

### Border Radius
```html
<div class="rounded-3">Standard radius (12px)</div>
<div class="rounded-circle">Circular</div>
<div class="rounded-pill">Pill shape (9999px)</div>
```

### Shadows
```html
<div class="shadow-sm">Soft shadow</div>
<div class="shadow">Medium shadow</div>
```

---

## 📱 14. Responsive Utilities

### Visibility
```html
<div class="d-none d-md-block">Hidden on mobile, visible on tablet+</div>
<div class="d-md-none">Visible on mobile, hidden on tablet+</div>
```

### Spacing
```html
<div class="col-12 col-md-6 col-lg-4">
    <!-- Full width mobile, half tablet, third desktop -->
</div>
```

---

## ✅ Checklist for New Pages

When creating a new page, make sure you:

- [ ] Use `container-fluid py-4` wrapper
- [ ] Add page header with title + description
- [ ] Use `row g-4` for grid layout
- [ ] All cards have `border-0 shadow-sm rounded-3`
- [ ] Card bodies have `p-4` padding
- [ ] Buttons use `rounded-pill px-4 fw-semibold`
- [ ] Primary buttons have `shadow-sm`
- [ ] Icons have colored backgrounds
- [ ] Tables use `table-hover align-middle`
- [ ] Pagination uses rounded pills
- [ ] Empty states have icon + message
- [ ] Consistent spacing (mb-4, mb-3, gap-3)
- [ ] Responsive on mobile

---

## 🎯 Common Patterns

### Data List Page
1. Page header with title + "Add New" button
2. Search bar in card header
3. Table with data
4. Pagination at bottom

### Dashboard Page
1. Page header with welcome message
2. Notification cards list
3. Each card: icon + title + content + metadata
4. Empty state if no items

### Form Page
1. Page header
2. Card with form
3. Input groups with icons
4. Submit button (primary, pill)
5. Cancel button (outline)

---

**Pro Tips:**
- Always preview on mobile
- Use consistent spacing throughout
- Icons should always have backgrounds
- Keep button text short and clear
- Use muted text for less important info
- Group related actions together

---

**Design System Version:** 1.0  
**Last Updated:** April 30, 2026
