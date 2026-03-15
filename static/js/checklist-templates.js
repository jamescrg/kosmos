// SortableJS integration for checklist template item ordering
// Supports two-level sorting: sections (outer) and items within sections (inner)

function getCSRFToken() {
    var bodyElement = document.querySelector('body');
    var hxHeaders = bodyElement.getAttribute('hx-headers');
    if (hxHeaders) {
        try {
            return JSON.parse(hxHeaders)['X-CSRFToken'] || '';
        } catch (e) { /* ignore */ }
    }
    return '';
}

function getItemDepth(li) {
    if (li.classList.contains('checklist-depth-2')) return 2;
    if (li.classList.contains('checklist-depth-1')) return 1;
    return 0;
}

function getChildItems(item) {
    var depth = getItemDepth(item);
    var children = [];
    var next = item.nextElementSibling;
    while (next && next.dataset.itemId) {
        if (getItemDepth(next) > depth) {
            children.push(next);
            next = next.nextElementSibling;
        } else {
            break;
        }
    }
    return children;
}

function updateItemNumbers() {
    var container = document.getElementById('template-sections-sortable');
    if (!container) return;

    var groups = container.querySelectorAll('.template-group');
    groups.forEach(function(group) {
        var items = group.querySelectorAll('.template-group-items > li[data-item-id]');
        var counters = [0, 0, 0];

        items.forEach(function(li) {
            // Determine depth from class
            var depth = 0;
            if (li.classList.contains('checklist-depth-1')) depth = 1;
            if (li.classList.contains('checklist-depth-2')) depth = 2;

            counters[depth]++;
            // Reset deeper counters
            for (var i = depth + 1; i < 3; i++) counters[i] = 0;

            // Build number string
            var parts = [];
            for (var i = 0; i <= depth; i++) parts.push(counters[i]);
            var numberStr = parts.join('.') + '.';

            var numberSpan = li.querySelector('.template-item-number');
            if (numberSpan) numberSpan.textContent = numberStr;
        });
    });
}

function saveOrder() {
    var container = document.getElementById('template-sections-sortable');
    if (!container) return;

    var templateId = container.dataset.templateId;
    var itemIds = [];

    // Walk all groups in DOM order, collecting section + item IDs
    var groups = container.querySelectorAll('.template-group');
    groups.forEach(function(group) {
        // Add section header ID if present
        var sectionHeader = group.querySelector('.template-section-header[data-item-id]');
        if (sectionHeader) {
            itemIds.push(sectionHeader.dataset.itemId);
        }
        // Add item IDs in order
        var items = group.querySelectorAll('.template-group-items > li[data-item-id]');
        items.forEach(function(li) {
            itemIds.push(li.dataset.itemId);
        });
    });

    fetch('/checklists/' + templateId + '/items/reorder/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({ item_ids: itemIds })
    });
}

function initializeTemplateItemsSortable() {
    var container = document.getElementById('template-sections-sortable');
    if (!container) return;

    // Outer sortable: drag whole sections
    Sortable.create(container, {
        handle: '.template-section-handle',
        animation: 150,
        ghostClass: 'sortable-ghost',
        dragClass: 'sortable-drag',
        draggable: '.template-group:not([data-section-id="root"])',
        onEnd: function() {
            updateItemNumbers();
            saveOrder();
        }
    });

    // Inner sortables: drag items within and between sections
    var itemLists = container.querySelectorAll('.template-group-items');
    itemLists.forEach(function(list) {
        Sortable.create(list, {
            handle: '.template-item-handle',
            animation: 150,
            ghostClass: 'sortable-ghost',
            dragClass: 'sortable-drag',
            group: 'checklist-items',
            onStart: function(evt) {
                // Collect children (subsequent items with greater depth)
                var children = getChildItems(evt.item);
                evt.item._dragChildren = children;
                // Hide children during drag so they don't appear orphaned
                children.forEach(function(child) {
                    child.style.display = 'none';
                });
            },
            onEnd: function(evt) {
                var children = evt.item._dragChildren || [];
                // Move children to follow the dragged item in its new location
                var insertAfter = evt.item;
                children.forEach(function(child) {
                    child.style.display = '';
                    insertAfter.parentNode.insertBefore(child, insertAfter.nextSibling);
                    insertAfter = child;
                });
                delete evt.item._dragChildren;
                updateItemNumbers();
                saveOrder();
            }
        });
    });
}

function editTemplateItem(button, url) {
    var container = button.closest('.template-item, .template-section-header');
    var span = container.querySelector('.template-item-description, .template-section-title');
    if (!span) return;

    var currentText = span.textContent;
    var input = document.createElement('input');
    input.type = 'text';
    input.value = currentText;
    input.maxLength = 200;
    input.className = 'template-item-edit-input';

    span.replaceWith(input);
    input.focus();
    input.select();

    function submit() {
        var newText = input.value.trim();
        if (!newText || newText === currentText) {
            var newSpan = document.createElement('span');
            newSpan.className = span.className;
            newSpan.textContent = currentText;
            input.replaceWith(newSpan);
            return;
        }
        htmx.ajax('POST', url, {
            target: '#template-items',
            swap: 'innerHTML',
            values: { description: newText }
        });
    }

    input.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            submit();
        } else if (e.key === 'Escape') {
            var newSpan = document.createElement('span');
            newSpan.className = span.className;
            newSpan.textContent = currentText;
            input.replaceWith(newSpan);
        }
    });

    input.addEventListener('blur', submit);
}

document.addEventListener('DOMContentLoaded', initializeTemplateItemsSortable);
document.body.addEventListener('htmx:afterSwap', function(event) {
    if (event.target.id === 'template-items' || event.target.id === 'htmx-modal-container') {
        initializeTemplateItemsSortable();
    }
});
