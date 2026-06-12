//
// utility functions to show and hide elements
//

function show(elementId) {
  const item = document.getElementById(elementId);
  item.style.display = "block";
}

function hide(elementId) {
  const item = document.getElementById(elementId);
  item.style.display = "none";
}

// Attach confirm handler to .confirm links (delegated for dynamic content)
document.addEventListener('click', async function(e) {
  const confirmLink = e.target.closest('.confirm');
  if (!confirmLink) return;

  e.stopPropagation();
  e.preventDefault();

  // Support custom options via data attributes
  const title = confirmLink.dataset.confirmTitle || 'Confirm';
  const message = confirmLink.dataset.confirmMessage || 'Are you sure you want to proceed?';
  const confirmText = confirmLink.dataset.confirmText || 'Confirm';
  const isDangerous = confirmLink.dataset.confirmDangerous !== 'false';

  const confirmed = await showConfirm({
    title: title,
    message: message,
    confirmText: confirmText,
    isDangerous: isDangerous
  });

  if (confirmed) {
    // Navigate to the link's href or data-href (for buttons)
    const href = confirmLink.getAttribute('href') || confirmLink.dataset.href;
    if (href) {
      window.location.href = href;
    }
  }
});

// Handle buttons with data-href attribute (navigate without confirmation)
document.addEventListener('click', function(e) {
  const btn = e.target.closest('button[data-href]');
  if (!btn || btn.classList.contains('confirm')) return;

  e.preventDefault();
  window.location.href = btn.dataset.href;
});

// Modal handling is now in alpine-components.js

// Copy link buttons (delegated for HTMX compatibility)
document.addEventListener('click', function(e) {
  const copyBtn = e.target.closest('.copy-btn');
  const highlightCopyBtn = e.target.closest('.highlight-copy-btn');
  const highlightLinkBtn = e.target.closest('.highlight-link-btn');
  const documentLinkBtn = e.target.closest('.document-link-btn');
  const sourceCopyBtn = e.target.closest('.source-copy-btn');

  if (copyBtn) {
    e.preventDefault();
    let data = copyBtn.getAttribute('data-copy');

    // If data-copy-target is specified, get text from target element
    const targetSelector = copyBtn.getAttribute('data-copy-target');
    if (targetSelector) {
      const targetElement = document.querySelector(targetSelector);
      if (targetElement) {
        data = targetElement.textContent.trim();
      }
    }

    copyToClipboard(copyBtn, data);
  } else if (highlightCopyBtn) {
    const data = highlightCopyBtn.getAttribute('data-copy');
    copyToClipboard(highlightCopyBtn, data);
  } else if (highlightLinkBtn) {
    const url = highlightLinkBtn.getAttribute('data-url');
    const fullUrl = window.location.origin + url;
    copyToClipboard(highlightLinkBtn, fullUrl);
  } else if (documentLinkBtn) {
    const url = documentLinkBtn.getAttribute('data-url');
    const fullUrl = window.location.origin + url;
    copyToClipboard(documentLinkBtn, fullUrl);
  } else if (sourceCopyBtn) {
    e.preventDefault();
    const data = sourceCopyBtn.getAttribute('data-copy');
    copyToClipboard(sourceCopyBtn, data);
  }
});

function copyToClipboard(button, data) {
  navigator.clipboard.writeText(data).then(() => {
    const originalHtml = button.innerHTML;
    button.innerHTML = '<i class="icon-check"></i>';
    button.style.color = 'green';
    setTimeout(() => {
      button.innerHTML = originalHtml;
      button.style.color = '';
    }, 2000);
  }).catch(err => {
    console.error('Failed to copy value: ', err);
  });
}

// Copy value logic
document.addEventListener('DOMContentLoaded', function() {
  const copyButtons = document.querySelectorAll('.copy-btn');

  copyButtons.forEach(button => {
    button.addEventListener('click', function() {
      let data = this.getAttribute('data-copy');

      // If data-copy-target is specified, get text from target element
      const targetSelector = this.getAttribute('data-copy-target');
      if (targetSelector) {
        const targetElement = document.querySelector(targetSelector);
        if (targetElement) {
          data = targetElement.textContent.trim();
        }
      }

      navigator.clipboard.writeText(data).then(() => {
        const originalHtml = this.innerHTML;

        this.innerHTML = '<i class="icon-check"></i>';
        this.style.color = 'green';

        setTimeout(() => {
          this.innerHTML = originalHtml;
          this.style.color = '';
        }, 2000);
      }).catch(err => {
        console.error('Failed to copy value: ', err);
      });
    });
  });
});

// ==========================================================================
//  Search Tab Switcher
// ==========================================================================

function switchSearchTab(tab) {
  const container = tab.closest('.search-tabs');
  container.querySelectorAll('.search-tab').forEach(t => t.classList.remove('active'));
  tab.classList.add('active');

  const scopeInput = document.getElementById('search-scope');
  scopeInput.value = tab.dataset.scope;

  // Trigger search with new scope
  const searchInput = document.getElementById('search-text');
  if (searchInput && searchInput.value.trim()) {
    htmx.trigger(searchInput, 'search');
  }
}

// Autofocus the quick-add task input whenever the tasks list (re)renders, so
// tasks can be typed back-to-back. The #tasks container swaps in a fresh input
// on every tasksListChanged, which is why the autofocus attribute alone isn't
// enough. Skip when focus is already in another field so we don't steal it.
document.body.addEventListener('htmx:afterSwap', function(e) {
  const input = e.target.querySelector && e.target.querySelector('.tasks-add-quick-input');
  if (!input) return;
  const active = document.activeElement;
  if (!active || active === document.body) {
    input.focus();
  }
});

// Autofocus the "Find Matter" search whenever the matters list (re)renders.
// Scoped to the matters list (identified by its #matter-list table) so other
// .toolbar-search inputs aren't affected. Skip if focus is already elsewhere.
document.body.addEventListener('htmx:afterSwap', function(e) {
  const root = e.target;
  if (!root.querySelector || !root.querySelector('#matter-list')) return;
  const input = root.querySelector('.toolbar-search');
  if (!input) return;
  const active = document.activeElement;
  if (!active || active === document.body) {
    input.focus();
  }
});

// Autofocus the AI chat message box when a conversation/chat view is swapped in,
// so you can start typing right away. Unlike the list inputs above, opening a
// conversation often leaves a sidebar link focused (not body), so only skip when
// focus is already in another text field.
document.body.addEventListener('htmx:afterSwap', function(e) {
  const input = e.target.querySelector && e.target.querySelector('#aiMessageInput');
  if (!input) return;
  const active = document.activeElement;
  if (active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA' || active.isContentEditable)) return;
  input.focus();
});
