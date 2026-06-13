# CloakBrowser Anti-Detection Skill

## Overview
CloakBrowser is a stealth Chromium fork with 58 source-level C++ patches across 16 fingerprinting categories. When running in `BU_CLOAK=1` mode, all browser-harness commands automatically use CloakBrowser.

## Bot Detection Bypass
CloakBrowser passes ALL major bot detection systems:
- Cloudflare Turnstile ✅
- reCAPTCHA v3 (0.9 score) ✅
- DataDome ✅
- PerimeterX ✅
- Akamai Bot Manager ✅
- Shape Security ✅
- FingerprintJS ✅
- CreepJS ✅
- BrowserLeaks ✅
- PixelScan ✅

## Fingerprinting Categories Patched (16)
Canvas, WebGL, Audio, Fonts, GPU, Screen, WebRTC, Navigator, Network, Hardware, Battery, Media, Automation, Speech, Timezone, CDP

## Usage Patterns

### Basic anti-detect browsing
```python
# With BU_CLOAK=1 set, all commands use CloakBrowser automatically
new_tab("https://protected-site.com")
wait_for_load()
info = page_info()
print(info)  # page loads without bot detection
```

### Screenshot-based verification
```python
new_tab("https://deviceandbrowserinfo.com/are_you_a_bot")
wait_for_load()
img = capture_screenshot()
# Verify: "You are human!" visible
```

### Cloudflare-protected sites
```python
new_tab("https://cloudflare-protected-site.com")
wait_for_load()  # CloakBrowser auto-passes Turnstile
# Continue normal interaction
click_at_xy(x, y)
```

### Form filling on protected sites
```python
new_tab("https://login.site.com")
wait_for_load()
# Type into fields — no bot detection triggers
js("document.querySelector('#email').focus()")
type_text("user@example.com")
press_key("Tab")
type_text("password")
press_key("Enter")
```

## Anti-Detection Signals (all return false)
These are the 20 signals that bot detection sites check — CloakBrowser spoofs all of them:

| Signal | CloakBrowser |
|--------|-------------|
| hasBotUserAgent | false |
| hasWebdriverTrue | false |
| hasWebdriverInFrameTrue | false |
| isPlaywright | false |
| hasInconsistentChromeObject | false |
| isPhantom | false |
| isNightmare | false |
| isSequentum | false |
| isSeleniumChromeDefault | false |
| isHeadlessChrome | false |
| isWebGLInconsistent | false |
| isAutomatedWithCDP | false |
| isAutomatedWithCDPInWebWorker | false |
| hasInconsistentClientHints | false |
| hasInconsistentGPUFeatures | false |
| isIframeOverridden | false |
| hasInconsistentWorkerValues | false |
| hasHighHardwareConcurrency | false |
| hasHeadlessChromeDefaultScreenResolution | false |
| hasSuspiciousWeakSignals | false |

## Environment Variables
- `BU_CLOAK=1` — Enable CloakBrowser mode
- `BU_CLOAK_PORT=9222` — CDP port (default 9222)
- `BU_CLOAK_BINARY=` — Override binary path
- `BU_CLOAK_WIDTH=1920` — Viewport width
- `BU_CLOAK_HEIGHT=1080` — Viewport height

## Limitations
- CloakBrowser prevents bot detection but does NOT solve CAPTCHAs automatically
- Some sites may still block based on IP reputation (not fingerprinting)
- headless=new mode — no visible browser window
- Requires `--no-sandbox` on Linux (standard for headless automation)

## Troubleshooting
- If bot detection still triggers: check IP reputation, try with proxy
- If CDP connection fails: verify port not in use, check `--no-sandbox`
- If page blank: add `wait_for_load()` after navigation
