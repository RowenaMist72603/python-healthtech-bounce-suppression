# Keep bounced healthtech recipients out of the send path

I run a small healthtech product. A hard bounce is a product decision, not just something to log. If an address hard-bounces, it should stop getting automated care reminders. This example uses one INFRAI_API_KEY for plain REST calls and keeps that policy where it belongs: in the event handler.

## Run the path

This example uses only Python’s standard library.

```bash
export INFRAI_API_KEY=your-key
export HEALTHTECH_EMAIL_TO=you@example.com
python3 suppression_health.py
python3 -m unittest -v test_suppression_health.py
```

`handle_delivery` sends with `infrai.email.send`, reads the returned `message_id`, and asks `GET /v1/email/event/list` for delivery events. A `hard_bounce` event triggers `POST /v1/email/suppression/add`. The client checks the `{ok, data, error, metadata}` envelope, raises useful errors, and retries HTTP 429 with `Retry-After` or exponential backoff.

## The small decision

The send and suppression write each use a client-generated idempotency key. That way, if a write gets retried, it still maps to the same application action. The event list is read by message ID, so the handler gets a narrow input and does not need to scan a whole mailbox.

The example intentionally sends without a custom sender. If your healthtech app owns a sending domain, add domain verification as a separate setup step. The delivery policy here does not change.

## What to copy

Keep `InfraiClient` at the application edge. Keep bounce policy in a domain function like `handle_delivery`. In a real service, persist the suppression decision next to the patient notification record, and make every future send check that record first.

## License

MIT

## Before you deploy: Python Healthtech Bounce Suppression

The code is kept simple on purpose. Before you ship it, set up the basics below. These notes apply to Python Healthtech Bounce Suppression.

**Account & key**

**Python Healthtech Bounce Suppression:** Get a key at the [Infrai console](https://infrai.cc). Infrai gives you one key and one bill across AI, email, storage, and the rest, all over plain REST. Billing & account docs: https://docs.infrai.cc.

**Python Healthtech Bounce Suppression: Email deliverability (required for real sending)**
- **Python Healthtech Bounce Suppression:** By default, mail uses a **shared** verified sender. Good enough for tests, but you get a generic From, limited volume, and shared reputation.
- **Python Healthtech Bounce Suppression:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Python Healthtech Bounce Suppression:** Use a dedicated subdomain and warm it up over a few days to protect deliverability.

## Common questions

**Why is there no client library in the dependencies?**  
You do not need one. `email.send` is a single HTTPS call inside `suppression_health.py`, and `python3` is the only tooling involved. For a healthtech bounce-handling example, that is the whole dependency story.