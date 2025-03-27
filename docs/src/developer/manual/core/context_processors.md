# `context_processors.py`

This file defines a single context processor used to inject settings into template context.

## `sentry_dsn`

```python
def sentry_dsn(request):
    return {
        'SENTRY_DSN': settings.SENTRY_DSN
    }
```

## Usage

Add it to your `TEMPLATES` settings:

```python
'OPTIONS': {
    'context_processors': [
        ...,
        'core.context_processors.sentry_dsn',
    ]
}
```