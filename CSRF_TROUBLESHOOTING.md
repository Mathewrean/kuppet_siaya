# Django CSRF Verification Failed: Troubleshooting Guide

## 1. Django Settings Configuration

### Current Settings Analysis
Inspect `kuppetsiaya/settings.py` and compare with the recommended configuration below.

### `CSRF_TRUSTED_ORIGINS`
Django 4.0+ requires **fully-qualified origins with scheme** for `CSRF_TRUSTED_ORIGINS`.

```python
# WRONG
CSRF_TRUSTED_ORIGINS = ['*.railway.app']

# CORRECT
CSRF_TRUSTED_ORIGINS = [
    'https://*.up.railway.app',    # Railway default domain
    'https://your-app.up.railway.app',  # Custom Railway domain
    'https://www.yourdomain.com',  # Your production domain
]
```

**Note:** Railway apps use `*.up.railway.app`, not `*.railway.app`. Update your settings to match the actual domain.

### `CSRF_COOKIE_SECURE` and `SESSION_COOKIE_SECURE`
```python
# Production should use secure cookies
CSRF_COOKIE_SECURE = True      # Transmit CSRF cookie only over HTTPS
SESSION_COOKIE_SECURE = True   # Transmit session cookie only over HTTPS
```

### `SECURE_PROXY_SSL_HEADER` — CRITICAL FOR RAILWAY
Railway terminates SSL at its load balancer and proxies requests to your app over HTTP. Without this setting, Django doesn't know the original request was HTTPS, causing secure cookies to be rejected.

```python
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```

### `USE_X_FORWARDED_HOST`
```python
USE_X_FORWARDED_HOST = True
```

### Additional Recommended Security Settings
```python
SECURE_SSL_REDIRECT = True  # Redirect all HTTP to HTTPS
```

---

## 2. Template Implementation (`{% csrf_token %}`)

### Standard HTML Forms
Every `<form method="post">` must include `{% csrf_token %}`:

```html
<form method="post">
    {% csrf_token %}
    <!-- form fields -->
</form>
```

**Current Project Status:** All templates in this project already include `{% csrf_token %}` in their forms.

### AJAX/Fetch Requests
When making AJAX POST requests, include the CSRF token in the `X-CSRFToken` header:

```javascript
// Correct: Get token from cookie (recommended for AJAX)
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

fetch('/api/endpoint/', {
    method: 'POST',
    headers: {
        'X-CSRFToken': csrftoken,
        'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
});
```

**Current Project Status:** The contact form AJAX in `templates/core/contact.html` correctly reads the token from `FormData` and includes it as `X-CSRFToken`.

---

## 3. Reverse Proxy Issues (Nginx/Apache/Load Balancers)

### Railway-Specific
Railway acts as a reverse proxy. Common issues:

| Issue | Cause | Solution |
|-------|-------|----------|
| CSRF cookie not set | `CSRF_COOKIE_SECURE=True` but Django sees HTTP request | Set `SECURE_PROXY_SSL_HEADER` |
| Session lost between requests | Same proxy SSL issue | Set `SECURE_PROXY_SSL_HEADER` |
| Domain mismatch | CSRF origin doesn't match trusted origins | Update `CSRF_TRUSTED_ORIGINS` |

### Nginx Configuration (if applicable)
If you add Nginx in front of Django:

```nginx
# Pass the original protocol
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header X-Forwarded-Host $host;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
```

### Apache Configuration (if applicable)
```apache
RequestHeader set X-Forwarded-Proto "https"
```

---

## 4. Middleware Configuration

### Required Middleware Order
Ensure `CsrfViewMiddleware` is present and properly ordered:

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',  # Must be here
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

### Exempting API Views from CSRF
For REST API views using DRF that receive JSON payloads from JavaScript:

**Option A (Recommended):** Use DRF's `SessionAuthentication` which handles CSRF automatically, or switch to `TokenAuthentication`/`JWTAuthentication` for stateless APIs.

**Option B:** If using Django's `JsonResponse` directly:

```python
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@csrf_exempt
def my_api_view(request):
    if request.method == 'POST':
        # handle JSON request
        pass
```

**Note:** The `api_tests.py` tests use `csrf=False` in WebTest because DRF viewsets should use proper authentication classes.

---

## 5. DEBUG=False Transition Checklist

Moving from development to production:

| Setting | Development (`DEBUG=True`) | Production (`DEBUG=False`) |
|---------|---------------------------|----------------------------|
| `CSRF_COOKIE_SECURE` | `False` | `True` |
| `SESSION_COOKIE_SECURE` | `False` | `True` |
| `SECURE_PROXY_SSL_HEADER` | Not needed | `('HTTP_X_FORWARDED_PROTO', 'https')` |
| `CSRF_TRUSTED_ORIGINS` | `['http://localhost:*', 'http://127.0.0.1:*']` | `['https://your-domain.com']` |
| `ALLOWED_HOSTS` | `['localhost', '127.0.0.1']` | `['your-domain.com', 'www.your-domain.com']` |

### Step-by-Step Debug-to-Production Transition

1. **Set `DEBUG=False`** in production environment
2. **Set `SECRET_KEY`** via environment variable (never hardcode)
3. **Configure `ALLOWED_HOSTS`** with production domains
4. **Update `CSRF_TRUSTED_ORIGINS`** with production origins (include scheme)
5. **Set secure cookies:**
   ```python
   CSRF_COOKIE_SECURE = True
   SESSION_COOKIE_SECURE = True
   ```
6. **Add proxy SSL header:**
   ```python
   SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
   USE_X_FORWARDED_HOST = True
   ```
7. **Verify all templates** include `{% csrf_token %}` in forms
8. **Verify AJAX requests** send `X-CSRFToken` header
9. **Test in production** with private/incognito browser to avoid cached cookies

---

## 6. Debugging Steps

### Step 1: Check the Error Message
Django's CSRF error page includes:
- The "Referer" header it received
- The "Origin" header it received
- Which cookie domain was expected

### Step 2: Inspect Browser Cookies
Open DevTools > Application > Cookies:
- Is `csrftoken` present?
- Is the `Domain` correct?
- Is `Secure` flag set (expected in production)?

### Step 3: Check Request Headers
In DevTools > Network, inspect the POST request:
- Is `Cookie: csrftoken=...` present?
- Is `X-CSRFToken: ...` present (for AJAX)?
- Is `X-Forwarded-Proto: https` present (behind Railway proxy)?

### Step 4: Django Logs
Check Railway logs for `Forbidden (CSRF token missing or incorrect.)`

### Step 5: Test with `curl`
```bash
# Get CSRF cookie
curl -c cookies.txt https://your-app.up.railway.app/

# Make POST request with cookie
curl -b cookies.txt -X POST https://your-app.up.railway.app/contact/ \
  -d "first_name=Test&last_name=User&email=test@example.com" \
  -H "X-CSRFToken: <token-from-cookies>"
```

---

## 7. Railway-Specific Fixes

### Verify These Settings Are Present

```python
# In settings.py
DEBUG = str_to_bool(config('DEBUG', default='False'))

CSRF_TRUSTED_ORIGINS = [
    'https://*.up.railway.app',
]

SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
```

### Railway Environment Variables
Ensure these are set in Railway dashboard:

| Variable | Value |
|----------|-------|
| `DEBUG` | `False` |
| `SECRET_KEY` | (strong random string) |
| `DATABASE_URL` | (provided by Railway PostgreSQL) |

---

## 8. DRF API Views and CSRF

DRF viewsets using `SessionAuthentication` enforce CSRF. If your frontend makes API calls from JavaScript, ensure:

1. The CSRF token cookie is sent with requests
2. The `X-CSRFToken` header is included

Alternatively, use token-based authentication for APIs:

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
```

---

## Quick Reference: Most Common Fixes

1. **Update `CSRF_TRUSTED_ORIGINS`** — add `https://*.up.railway.app`
2. **Add `SECURE_PROXY_SSL_HEADER`** — Railway terminates SSL, Django needs to know
3. **Set `CSRF_COOKIE_SECURE = True`** — required when DEBUG=False
4. **Verify `{% csrf_token %}`** in all POST forms
5. **Check cookie domain** — Railway apps may use `*.up.railway.app` which requires wildcard in trusted origins
