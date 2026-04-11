// custom elements for the blobs used for visualization
class R4Blob extends HTMLElement {
    connectedCallback() {
        this.innerHTML = `<info-></info-><blob-><b-><s-></s-></b-><g-></g-></blob->`;
    }
}

class R5Blob extends HTMLElement {
    connectedCallback() {
        this.innerHTML = `<info-></info-><blob-><b-><s-></s-><sh-></sh-></b-><g-></g-><og-></og-></blob->`;
    }
}

class R6Blob extends HTMLElement {
    connectedCallback() {
        this.innerHTML = `<info-></info-><blob-><b-><s-></s-><sh-></sh-><sp-></sp-></b-><g-></g-><og-></og-></blob->`;
    }
}

window.customElements.define('r-4', R4Blob);
window.customElements.define('r-5', R5Blob);
window.customElements.define('r-6', R6Blob);

// show and populate the tooltip
function onMouseOver(event) {
    if (event.target?.tagName !== 'BLOB-') {
        return;
    }

    const stars = '★★★★★★';
    const tooltip = document.getElementById('tooltip');
    const pullID = Number(event.target.parentNode.dataset.id);
    const pullDomain = event.target.parentNode.dataset.domain;
    const pull = window.pullData[pullDomain].find((p) => p.id === pullID);

    // move the tooltip where it belongs
    const { top, right } = event.target.getBoundingClientRect();
    tooltip.className = '';
    tooltip.classList.add('visible');
    tooltip.style.left = `${right + 6}px`;
    tooltip.style.top = `${top - 6}px`;

    // add the data™
    tooltip.classList.add(`r${pull.rarity}`);
    const h4 = tooltip.querySelector('h4');
    h4.querySelector('.name').textContent = pull.name;
    h4.dataset.name = pull.name;
    h4.querySelector('.stars').textContent = stars.substring(0, pull.rarity);

    const time = tooltip.querySelector('time');
    const instant = Temporal.Instant.fromEpochMilliseconds(pull.timestamp);
    const zdt = instant.toZonedDateTimeISO(Temporal.Now.timeZoneId());
    time.textContent = zdt.toString({ smallestUnit: 'seconds', offset: 'never', timeZoneName: 'never' }).replace('T', ' ');

    if (pull.new) {
        tooltip.classList.add('new');
    }

    if (pull.free) {
        tooltip.classList.add('free');
    }
}

// hide the tooltip
function onMouseOut(event) {
    if (event.target?.tagName !== 'BLOB-') {
        return;
    }

    const tooltip = document.getElementById('tooltip');
    tooltip.classList.remove('visible');
}

// stuff the blobs into the DOM
function BuildVisualization(containerID, data) {
    const domain = containerID.substring(0, 1);
    if (!window.pullData) {
        window.pullData = {};
    }
    window.pullData[domain] = data;

    const fragment = new DocumentFragment();
    let firstPullProcessed = false;
    let pullsHeader = document.createElement('h3');
    let pullsContainer = document.createElement('div');
    pullsContainer.classList.add('pulls');
    pullsContainer.addEventListener('mouseover', onMouseOver, { passive: true });
    pullsContainer.addEventListener('mouseout', onMouseOut, { passive: true });

    for (const pull of data) {
        if (!firstPullProcessed) {
            pullsHeader.textContent = pull.bannerName;
            firstPullProcessed = true;
        }

        const el = document.createElement(`r-${pull.rarity}`);
        el.dataset.id = pull.id;
        el.dataset.domain = domain;

        if (pull.free) {
            el.classList.add('free');
        }

        if (pull.tenPull) {
            el.classList.add('ten-' + pull.tenPull);
        }

        if (pull.bannerChange) {
            fragment.appendChild(pullsHeader);
            fragment.appendChild(pullsContainer);

            pullsHeader = document.createElement('h3');
            pullsHeader.textContent = pull.bannerName;
            pullsContainer = document.createElement('div');
            pullsContainer.classList.add('pulls');
            pullsContainer.addEventListener('mouseover', onMouseOver, { passive: true });
            pullsContainer.addEventListener('mouseout', onMouseOut, { passive: true });
        }

        pullsContainer.appendChild(el);
    }

    if (firstPullProcessed) {
        // averages
        const nonFreePulls = data.filter((pull) => !pull.free);
        const total = nonFreePulls.length;
        const avg5Star = total / nonFreePulls.filter((pull) => pull.rarity === 5).length;
        const avg6Star = total / nonFreePulls.filter((pull) => pull.rarity === 6).length;

        const container = document.querySelector(`#${containerID}`);
        container.querySelector('.total').textContent = total;
        container.querySelector('.avg-5').textContent = avg5Star.toFixed(2);
        container.querySelector('.avg-6').textContent = avg6Star.toFixed(2);

        fragment.appendChild(pullsHeader);
        fragment.appendChild(pullsContainer);
        container.appendChild(fragment);
    }
}

// make background noise pixel perfect :)
if (window.devicePixelRatio) {
    document.body.style.setProperty('--noise-size', `${1 / window.devicePixelRatio * 128}px`);
}
