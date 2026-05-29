# API Changelog — v3.2

## Notes

- The `/v1/export` endpoint is **deprecated** and will be removed in v4. Migrate to `/v2/export`.
- This release is backward compatible. Existing API keys and request formats continue to work.
- Rate limits are unchanged at 1000 requests per minute.

## Added

- `/v2/export` supports streaming responses.
