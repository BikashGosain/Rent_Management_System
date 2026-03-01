(function () {
    function attachToggle(input) {
        if (input.dataset.pwToggle) return; // prevent double attach
        input.dataset.pwToggle = '1';

        var wrapper = document.createElement('div');
        wrapper.style.cssText = 'position:relative; display:block;';
        input.parentNode.insertBefore(wrapper, input);
        wrapper.appendChild(input);
        input.style.paddingRight = '42px';
        input.style.boxSizing    = 'border-box';

        var btn = document.createElement('button');
        btn.type      = 'button';
        btn.setAttribute('aria-label', 'Toggle password visibility');
        btn.innerHTML = '<span class="material-symbols-rounded" style="font-size:18px; pointer-events:none;">visibility</span>';
        btn.style.cssText = [
            'position:absolute',
            'right:10px',
            'top:50%',
            'transform:translateY(-50%)',
            'background:none',
            'border:none',
            'cursor:pointer',
            'color:#9ca3af',
            'padding:4px',
            'display:flex',
            'align-items:center',
            'justify-content:center',
            'transition:color 0.2s',
        ].join(';');

        btn.addEventListener('mousedown', function (e) {
            // prevent input blur on click
            e.preventDefault();
        });

        btn.addEventListener('click', function () {
            var icon = btn.querySelector('span');
            if (input.type === 'password') {
                input.type       = 'text';
                icon.textContent = 'visibility_off';
                btn.style.color  = '#6366f1';
            } else {
                input.type       = 'password';
                icon.textContent = 'visibility';
                btn.style.color  = '#9ca3af';
            }
            input.focus();
        });

        wrapper.appendChild(btn);
    }

    // Attach to all existing password fields
    function init() {
        document.querySelectorAll('input[type="password"]').forEach(attachToggle);
    }

    // Also watch for dynamically added inputs
    var observer = new MutationObserver(function () {
        document.querySelectorAll('input[type="password"]').forEach(attachToggle);
    });

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () {
            init();
            observer.observe(document.body, { childList: true, subtree: true });
        });
    } else {
        init();
        observer.observe(document.body, { childList: true, subtree: true });
    }
})();
