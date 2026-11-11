'use strict';
const paths = {
    layers: '<path d="m12 3 9 5-9 5-9-5 9-5Z"/><path d="m3 12 9 5 9-5M3 16l9 5 9-5"/>',
    overview: '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
    acquisition: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
    categories: '<path d="M3 7h18v13H3zM3 7l3-4h12l3 4M9 11h6"/>',
    guide: '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7h.01"/>',
    collapse: '<path d="m11 7-5 5 5 5m7-10-5 5 5 5"/>',
    expand: '<path d="m6 7 5 5-5 5m7-10 5 5-5 5"/>',
    download: '<path d="M12 3v12m-5-5 5 5 5-5M4 15v6h16v-6"/>'
};
const icon = (name) => `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name]}</svg>`;
const esc = (s) => String(s).replace(/[&<>"']/g, c => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
} [c]));
const fmt = (n, digits = 0) => Number(n).toLocaleString('en-US', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits
});
const names = {
    organic: 'Organic search',
    paid_search: 'Paid search',
    direct: 'Direct',
    email: 'Email',
    social: 'Social'
};
const sum = (rows, key) => rows.reduce((a, r) => a + Number(r[key]), 0);
const pages = {
    overview: ['Commerce overview', 'Sales, acquisition and customer behavior.'],
    acquisition: ['Acquisition performance', 'Understand which channels bring sessions, conversions and revenue.'],
    categories: ['Category performance', 'Explore paid sales contribution and estimated product margin.'],
    guide: ['Behind the numbers', 'Traceable sources, explicit definitions and honest limitations.']
};
let data, windowDays = 0,
    channelSearch = '';

function linePoints(values, width, height, pad = 2) {
    const lo = Math.min(...values),
        range = Math.max(...values) - lo || 1;
    return values.map((v, i) => `${pad+i*(width-2*pad)/Math.max(values.length-1,1)},${height-pad-(v-lo)*(height-2*pad)/range}`).join(' ');
}

function spark(values, label) {
    return `<svg viewBox="0 0 82 36" role="img" aria-label="${esc(label)} 7-day totals"><polyline fill="none" stroke="#17191f" stroke-width="1.7" stroke-linecap="round" points="${linePoints(values,82,36)}"/></svg>`;
}

function blocks(rows, key) {
    const result = [];
    for (let i = 0; i < rows.length; i += 7) result.push(sum(rows.slice(i, i + 7), key));
    return result;
}

function renderKpis() {
    const revenue = sum(data.daily, 'net_revenue'),
        paid = sum(data.daily, 'paid_orders'),
        sessions = sum(data.channels, 'sessions'),
        converted = sum(data.channels, 'converted_sessions');
    const weeklyRevenue = blocks(data.daily, 'net_revenue'),
        weeklyPaid = blocks(data.daily, 'paid_orders');
    const metrics = [
        ['Paid revenue · RON', fmt(revenue), weeklyRevenue],
        ['Paid orders', fmt(paid), weeklyPaid],
        ['Average order value', paid ? `${fmt(revenue/paid)} RON` : '—', weeklyRevenue.map((v, i) => weeklyPaid[i] ? v / weeklyPaid[i] : 0)],
        ['Session conversion', sessions ? `${fmt(converted/sessions*100,1)}%` : '—'],
        ['Repeat buyer rate', data.repeat[0].repeat_customer_rate === null ? '—' : `${fmt(data.repeat[0].repeat_customer_rate*100,1)}%`]
    ];
    document.querySelector('#kpis').innerHTML = metrics.map(([label, value, series]) => `<div class="kpi"><div class="kpi-label">${label}</div><div class="kpi-value">${value}</div>${series?spark(series,label):''}</div>`).join('');
}

function bars(rows, label, key, percent = false) {
    const max = Math.max(...rows.map(r => r[key]), 1);
    return rows.map(r => `<div class="bar-row"><span class="bar-label">${esc(label(r))}</span><div class="bar-track"><div class="bar" style="width:${Math.max(0,Math.min(100,r[key]/max*100))}%"></div></div><span class="bar-value">${fmt(percent?r[key]*100:r[key],percent?1:0)}${percent?'%':''}</span></div>`).join('');
}

function trend() {
    let rows = data.daily.map((r, i, all) => ({
        ...r,
        average: i >= 6 ? sum(all.slice(i - 6, i + 1), 'net_revenue') / 7 : null
    }));
    if (windowDays) rows = rows.slice(-windowDays);
    const W = 700,
        H = 240,
        left = 45,
        right = 10,
        top = 10,
        bottom = 35,
        max = Math.max(...rows.map(r => r.net_revenue), 1) * 1.08;
    const x = i => left + i * (W - left - right) / Math.max(rows.length - 1, 1),
        y = v => H - bottom - v * (H - top - bottom) / max;
    const points = rows.map((r, i) => `${x(i)},${y(r.net_revenue)}`).join(' '),
        avg = rows.map((r, i) => r.average === null ? null : `${x(i)},${y(r.average)}`).filter(Boolean).join(' ');
    const axis = Array.from({
        length: 5
    }, (_, i) => {
        const v = max * i / 4,
            Y = y(v);
        return `<line x1="${left}" y1="${Y}" x2="${W-right}" y2="${Y}" stroke="#eff1f3"/><text x="${left-10}" y="${Y+4}" text-anchor="end" fill="#667085" font-size="11">${fmt(v/1000,1)}k</text>`;
    }).join('');
    const dates = [0, Math.floor((rows.length - 1) / 2), rows.length - 1].map(i => `<text x="${x(i)}" y="${H-10}" text-anchor="middle" fill="#667085" font-size="11">${esc(rows[i].order_date.slice(5))}</text>`).join('');
    return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Daily revenue and 7-day average in fictional RON">${axis}<polygon points="${left},${H-bottom} ${points} ${W-right},${H-bottom}" fill="#17191f" opacity=".12"/><polyline points="${avg}" fill="none" stroke="#17191f" stroke-width="2.5"/>${rows.map((r,i)=>`<circle cx="${x(i)}" cy="${y(r.net_revenue)}" r="5" fill="transparent"><title>${r.order_date}: ${fmt(r.net_revenue,2)} RON</title></circle>`).join('')}${dates}</svg>`;
}

function channelRows() {
    return data.channels.filter(r => (names[r.channel] || r.channel).toLowerCase().includes(channelSearch.toLowerCase()));
}

function channelTable() {
    return `<div class="table-wrap"><table><thead><tr>${['Channel','Sessions','Converted sessions','Conversion','Revenue (RON)'].map(h=>`<th scope="col">${h}</th>`).join('')}</tr></thead><tbody id="channel-rows">${channelBody()}</tbody></table></div>`;
}

function channelBody() {
    return channelRows().map(r => `<tr><td>${esc(names[r.channel]||r.channel)}</td><td>${fmt(r.sessions)}</td><td>${fmt(r.converted_sessions)}</td><td><span class="badge">${fmt(r.conversion_rate*100,2)}%</span></td><td>${fmt(r.net_revenue,2)}</td></tr>`).join('') || '<tr><td colspan="5">No matching channels.</td></tr>';
}

function tablePanel() {
    return `<section class="panel"><div class="table-head"><div><h2>Channel performance</h2><p class="muted">Session-grain acquisition metrics · Full dataset</p></div><button class="secondary" id="export">${icon('download')}Export CSV</button></div><label class="sr-only" for="search">Search channels</label><input id="search" type="search" placeholder="Search channels…" value="${esc(channelSearch)}">${channelTable()}</section>`;
}

function overview() {
    const top = data.channels[0],
        best = [...data.channels].sort((a, b) => b.conversion_rate - a.conversion_rate)[0],
        revenue = sum(data.daily, 'net_revenue'),
        r = data.repeat[0];
    return `<div class="grid"><section class="panel trend"><h2>Revenue over time</h2><p class="muted">Daily paid revenue and 7-day rolling average · RON</p><div class="trend-controls">${[[0,'Full period'],[30,'Last 30 days'],[14,'Last 14 days']].map(([days,label])=>`<button data-days="${days}" class="${windowDays===days?'active':''}" aria-pressed="${windowDays===days}">${label}</button>`).join('')}</div>${trend()}<p class="muted">Pale area: daily revenue · Line: 7-day average. This window affects this chart only.</p></section><section class="panel"><h2>Revenue by category</h2><p class="muted">Contribution to paid-order revenue · RON</p>${bars(data.categories,r=>r.category,'net_revenue')}</section></div><div class="insights">${[['Leading revenue channel',names[top.channel],`${fmt(top.net_revenue/revenue*100,1)}% of paid-order revenue`],['Highest session conversion',names[best.channel],`${fmt(best.conversion_rate*100,1)}% of channel sessions converted`],['Returning buyers',`${r.repeat_customers} of ${r.paying_customers}`,'Paying customers with at least two paid orders']].map(([label,value,note])=>`<div class="insight"><small>${esc(label)}</small><strong>${esc(value)}</strong><small>${esc(note)}</small></div>`).join('')}</div>${tablePanel()}`;
}

function acquisition() {
    return tablePanel() + `<div class="grid equal"><section class="panel"><h2>Revenue by channel</h2><p class="muted">Paid-order revenue · RON</p>${bars(data.channels,r=>names[r.channel],'net_revenue')}</section><section class="panel"><h2>Conversion by channel</h2><p class="muted">Sessions containing at least one paid order</p>${bars([...data.channels].sort((a,b)=>b.conversion_rate-a.conversion_rate),r=>names[r.channel],'conversion_rate',true)}</section></div>`;
}

function categories() {
    return `<div class="grid equal"><section class="panel"><h2>Revenue contribution</h2><p class="muted">Paid sales by product category · RON</p>${bars(data.categories,r=>r.category,'net_revenue')}</section><section class="panel"><h2>Estimated product margin</h2><p class="muted">Paid sales less synthetic product cost · RON</p>${bars(data.categories,r=>r.category,'estimated_product_margin')}</section></div><section class="panel"><div class="table-head"><div><h2>Category breakdown</h2><p class="muted">Excludes tax, shipping, overhead and acquisition cost</p></div><button id="export-categories" class="secondary">${icon('download')}Export CSV</button></div><div class="table-wrap"><table><thead><tr>${['Category','Paid units','Revenue (RON)','Product margin (RON)'].map(v=>`<th scope="col">${v}</th>`).join('')}</tr></thead><tbody>${data.categories.map(r=>`<tr><td>${esc(r.category)}</td><td>${fmt(r.paid_units)}</td><td>${fmt(r.net_revenue,2)}</td><td>${fmt(r.estimated_product_margin,2)}</td></tr>`).join('')}</tbody></table></div></section>`;
}

function guide() {
    return `<section class="panel guide"><h2>How this demo works</h2><p>This public demo displays a <strong>verified, read-only snapshot</strong> exported from PostgreSQL marts after dbt and independent CSV reconciliation pass. It is not connected to a live database. The full Python/PostgreSQL/dbt/Streamlit application and reproducible Docker setup are available in the public repository.</p><p><code>Synthetic CSV → Python COPY → PostgreSQL → dbt → tested marts → reporting snapshot</code></p><h2>Metric contracts</h2><ul><li>Revenue: paid item quantity × unit price; cancelled/refunded orders add zero.</li><li>AOV: paid-order revenue / paid orders.</li><li>Conversion: sessions with at least one paid order / sessions.</li><li>Repeat buyers: customers with at least two paid orders / paying customers in this dataset.</li><li>Product margin: paid quantity × (unit price − unit cost); not net profit.</li></ul><p>All KPIs cover the full dataset. Trend windows affect their chart only. Searches filter the table and exported CSV; CSV conversion values are fractions. All data and RON amounts are fictional.</p><p>No incremental ingestion, external API source, production monitoring or anomaly detection is claimed.</p><p><a href="https://github.com/dutuvalentin16-dev/commerce-intelligence/blob/main/docs/case-study.md">Read the case study ↗</a> · <a href="https://github.com/dutuvalentin16-dev/commerce-intelligence/actions">View automated validation ↗</a></p></section>`;
}

function csvDownload(rows, filename) {
    const quote = v => '"' + String(v).replaceAll('"', '""') + '"';
    const csv = rows.map(r => r.map(quote).join(',')).join('\r\n');
    const url = URL.createObjectURL(new Blob([csv], {
        type: 'text/csv;charset=utf-8'
    }));
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function render() {
    if (!data) return;
    const view = location.hash.slice(1) in pages ? location.hash.slice(1) : 'overview';
    document.querySelector('#title').textContent = pages[view][0];
    document.querySelector('#subtitle').textContent = pages[view][1];
    document.querySelector('#nav').innerHTML = Object.keys(pages).map(k => `<a href="#${k}" class="${view===k?'active':''}" ${view===k?'aria-current="page"':''} title="${pages[k][0]}">${icon(k)}<span class="nav-label">${k==='guide'?'Metric guide':k[0].toUpperCase()+k.slice(1)}</span></a>`).join('');
    document.querySelector('#content').innerHTML = ({
        overview,
        acquisition,
        categories,
        guide
    } [view])();
    document.querySelectorAll('[data-days]').forEach(b => b.onclick = () => {
        windowDays = Number(b.dataset.days);
        render();
    });
    const search = document.querySelector('#search');
    if (search) search.oninput = () => {
        channelSearch = search.value;
        document.querySelector('#channel-rows').innerHTML = channelBody();
    };
    const exportButton = document.querySelector('#export');
    if (exportButton) exportButton.onclick = () => csvDownload([
        ['Channel', 'Sessions', 'Converted sessions', 'Conversion', 'Revenue (RON)'], ...channelRows().map(r => [names[r.channel], r.sessions, r.converted_sessions, r.conversion_rate, r.net_revenue])
    ], 'channel-performance.csv');
    const categoryButton = document.querySelector('#export-categories');
    if (categoryButton) categoryButton.onclick = () => csvDownload([
        ['Category', 'Paid units', 'Revenue (RON)', 'Product margin (RON)'], ...data.categories.map(r => [r.category, r.paid_units, r.net_revenue, r.estimated_product_margin])
    ], 'category-performance.csv');
}
document.querySelectorAll('[data-icon]').forEach(e => e.innerHTML = icon(e.dataset.icon));

function toggle() {
    const rail = document.body.classList.toggle('rail');
    const button = document.querySelector('#toggle');
    button.innerHTML = icon(rail ? 'expand' : 'collapse');
    button.setAttribute('aria-expanded', String(!rail));
    button.setAttribute('aria-label', rail ? 'Expand navigation' : 'Collapse navigation');
}
document.querySelector('#toggle').onclick = toggle;
if (innerWidth < 900) toggle();
window.addEventListener('hashchange', render);
fetch('data.json').then(r => {
    if (!r.ok) throw Error('Snapshot unavailable');
    return r.json();
}).then(snapshot => {
    data = snapshot;
    const target = Number(data.metadata.baseline.revenue);
    const totals = [sum(data.daily, 'net_revenue'), sum(data.channels, 'net_revenue'), sum(data.categories, 'net_revenue'), sum(data.repeat, 'total_customer_revenue')];
    if (totals.some(v => Math.abs(v - target) > .005) || sum(data.daily, 'paid_orders') !== data.metadata.baseline.paid_orders) throw Error('Snapshot reconciliation failed');
    document.querySelector('#quality').textContent = '✓ Reconciled';
    document.querySelector('#period').textContent = `${data.daily[0].order_date} – ${data.daily.at(-1).order_date} · UTC`;
    document.querySelector('#build').textContent = `Snapshot built ${data.metadata.generated_at.slice(0,10)} · Fictional RON`;
    renderKpis();
    render();
}).catch(error => {
    document.querySelector('#quality').textContent = 'Data unavailable';
    document.querySelector('#content').innerHTML = `<p class="error" role="alert">${esc(error.message)}. Please see the source repository for the reproducible demo.</p>`;
});
