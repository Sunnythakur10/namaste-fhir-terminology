// Tiny helper to add/remove a .hovered class for elements that need dynamic hover color changes
// Usage: add data-hover-toggle="true" to an element and call HoverHelper.init() on DOMContentLoaded
const HoverHelper = {
  init() {
    document.querySelectorAll('[data-hover-toggle="true"]').forEach(el => {
      el.addEventListener('mouseover', () => el.classList.add('hovered'));
      el.addEventListener('mouseout', () => el.classList.remove('hovered'));
    });
  }
};

if (typeof window !== 'undefined') {
  window.addEventListener('DOMContentLoaded', () => HoverHelper.init());
}
