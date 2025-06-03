let cardsAlreadyGenerated = false;
let lastWorkspacePath = location.pathname;

function generateWorkspaceCards() {
    if (cardsAlreadyGenerated) return;
    cardsAlreadyGenerated = true;

    $('#workspace-cards-container').remove();

    const $container = $(`
        <div id="workspace-cards-container" class="row" style="
            margin: 0 -10px;
            padding: 15px;
            width: 100%;
        "></div>
    `);

    if (!$('#workspace-cards-styles').length) {
        $('head').append(`
            <style id="workspace-cards-styles">
                #workspace-cards-container .workspace-card {
                    padding: 10px;
                }
                #workspace-cards-container .card {
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    overflow: hidden;
                    height: 280px;
                    transition: all 0.3s;
                    background: white;
                    display: flex;
                    flex-direction: column;
                }
                #workspace-cards-container .card:hover {
                    transform: translateY(-3px);
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                }
                #workspace-cards-container .card-img-placeholder {
                    height: 200px;
                    background: #f5f7fa;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #8D99A6;
                    font-size: 32px;
                    font-weight: 500;
                }
                #workspace-cards-container .card-img-placeholder img {
                    max-height: 100%;
                    max-width: 100%;
                    object-fit: contain;
                }
                #workspace-cards-container .card-body {
                    padding: 15px;
                    flex-grow: 1;
                }
                #workspace-cards-container .card-title {
                    font-size: 15px;
                    font-weight: 600;
                    margin-bottom: 5px;
                    color: #36414C;
                }
                #workspace-cards-container .card-count {
                    color: #6c7680;
                    font-size: 13px;
                    margin-bottom: 10px;
                }
                #workspace-cards-container .btn-sm {
                    font-size: 12px;
                    padding: 3px 8px;
                }
            </style>
        `);
    }

    $('.shortcut-widget-box').each(function () {
        const $item = $(this);
        const $titleEl = $item.find('.widget-title');
        const title = $titleEl.length ? $titleEl.text().trim() : null;
        if (!title) return;

        const count = $item.find('.indicator-pill').text().trim() || '';
        const rawLink = $item.attr('aria-label') || '';
        const link = rawLink.trim();
        if (!link) return;

        const initials = title.split(' ').map(w => w[0]).join('').toUpperCase();
        const imagePath = `/files/${title.replace(/\s+/g, '_')}.jpeg`;

        $container.append(`
            <div class="col-md-4 workspace-card">
                <div class="card">
                    <div class="card-img-placeholder">
                        <img src="${imagePath}" onerror="this.style.display='none'; this.parentNode.innerText='${initials}'" />
                    </div>
                    <div class="card-body">
                        <h5 class="card-title">${title}</h5>
                        ${count ? `<p class="card-count">${count} items</p>` : ''}
                        <a href="/app/${link.replace(/\s+/g, '-').toLowerCase()}" class="btn btn-primary btn-sm">Open</a>
                    </div>
                </div>
            </div>
        `);
    });

    if (!$('#workspace-cards-wrapper').length) {
        $('.layout-main-section').prepend('<div id="workspace-cards-wrapper"></div>');
    }
    $('#workspace-cards-wrapper').html($container);

    console.log('Generated cards for workspace:', location.pathname);
}

function waitForWidgetsAndGenerate() {
    const maxAttempts = 10;
    let attempts = 0;

    const checkInterval = setInterval(() => {
        const hasWidgets = $('.shortcut-widget-box .widget-title').length > 0;
        if (hasWidgets || attempts >= maxAttempts) {
            clearInterval(checkInterval);
            generateWorkspaceCards();
        }
        attempts++;
    }, 200);
}

function checkWorkspaceChange() {
    if (location.pathname !== lastWorkspacePath) {
        lastWorkspacePath = location.pathname;
        cardsAlreadyGenerated = false;
        $('#workspace-cards-wrapper').remove();
        console.log('Workspace changed, waiting to regenerate cards...');
        setTimeout(() => {
            waitForWidgetsAndGenerate();
        }, 300);
    }
}

setInterval(checkWorkspaceChange, 800);

waitForWidgetsAndGenerate();
