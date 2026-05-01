# MagnetBank Frontend

The user-facing interface for the MagnetBank ecosystem.

## 🟢 Features
- **Neon UI**: High-contrast, retro-modern aesthetic for maximum "terminal" vibes.
- **Responsive Card Grid**: Easy-to-scan gallery of torrent metadata.
- **Standards Mode**: Fully compliant HTML5/CSS3 layout.
- **Dynamic Link Generation**: Automatically appends the latest public trackers and `xs=` source links via Client-side JS (`torrents.js`).
- **Hive Integration**: Native support for **Hive Keychain** for secure, non-custodial metadata submissions.

## 🛠️ Development

### Local Execution
From the project root:
```bash
export FLASK_APP=frontend/app.py
uv run flask run --port 8080
```

### Key Paths
- **Templates**: `frontend/templates/` (Jinja2)
- **Static Assets**: `frontend/static/` (CSS/JS/Images)
- **Shared Utils**: `utils/` (Database & Helpers)

## 🎨 UI Customization
Styles are managed via `frontend/static/css/styles.css` using CSS variables for the neon theme.

```css
:root {
  --neon-green: #39ff14;
  --dark-bg: #0a0b0e;
}
```
