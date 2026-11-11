"""Small, local SVG primitives; no icon fonts or network dependency."""
from html import escape

PATHS = {
    'collapse': '<path d="m11 7-5 5 5 5m7-10-5 5 5 5"/>',
    'expand': '<path d="m6 7 5 5-5 5m7-10 5 5-5 5"/>',
    'layers': '<path d="m12 3 9 5-9 5-9-5 9-5Z"/><path d="m3 12 9 5 9-5M3 16l9 5 9-5"/>',
    'overview': '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
    'acquisition': '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
    'categories': '<path d="M3 7h18v13H3zM3 7l3-4h12l3 4M9 11h6"/>',
    'guide': '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7h.01"/>',
    'calendar': '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 11h18"/>',
    'search': '<circle cx="10.5" cy="10.5" r="7.5"/><path d="m16 16 5 5"/>',
    'refresh': '<path d="M20 7v5h-5M4 17v-5h5"/><path d="M6.1 6a8 8 0 0 1 13 2M17.9 18a8 8 0 0 1-13-2"/>',
    'download': '<path d="M12 3v12m-5-5 5 5 5-5M4 15v6h16v-6"/>',
    'check': '<path d="m5 12 4 4L19 6"/>',
    'chevrons': '<path d="m8 9 4-4 4 4m-8 6 4 4 4-4"/>',
}


def icon(name: str, size: int = 18) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
            'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{PATHS[name]}</svg>')


def sparkline(values, name: str) -> str:
    """Render real weekly values; normalize only geometry, never fabricate a trend."""
    values = [float(v) for v in values if v is not None]
    if len(values) < 2:
        return ''
    low, high = min(values), max(values)
    span = high - low or 1
    points = [(2 + i * 78 / (len(values) - 1), 30 - (v - low) * 25 / span)
              for i, v in enumerate(values)]
    line = ' '.join(f'{x:.1f},{y:.1f}' for x, y in points)
    gradient = f'spark-{escape(name, quote=True)}'
    return (f'<svg class="sparkline" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 82 36" '
            f'role="img" aria-label="{escape(name)} weekly trend"><defs><linearGradient id="{gradient}" '
            'x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#17191f" stop-opacity=".12"/>'
            '<stop offset="100%" stop-color="#17191f" stop-opacity="0"/></linearGradient></defs>'
            f'<polygon points="2,35 {line} 80,35" fill="url(#{gradient})"/>'
            f'<polyline points="{line}" fill="none" stroke="#17191f" stroke-width="1.7" '
            'stroke-linecap="round" stroke-linejoin="round"/></svg>')
