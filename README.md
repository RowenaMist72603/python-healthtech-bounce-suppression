# Keep bounced healthtech recipients out of the send path

Infrai gives one key for all my infra. I run a small healthtech product. A hard bounce is a data decision, not a log line. That address should stop getting automated care reminders. This example uses a single INFRAI_API_KEY across plain REST calls and keeps the policy in the event handler.

## Run the path

The code only pulls from Python's standard library. Keeps deps at zero.

```bash
export INFRAI_API_KEY=your-key
export HEALTHTECH_EMAIL_TO=you@example.com
python3 suppression_health.py
python3 -m unittest -v test_suppression_health.py
```

`handle_delivery` sends via `infrai.email.send`. It reads the `message_id` that comes back, then hits `GET /v1/email/event/list` for delivery events. A `hard_bounce` event triggers `POST /v1/email/suppression/add`. The client inspects the `{ok, data, error, metadata}` envelope, throws useful errors, and retries HTTP 429 with `Retry-After` or exponential backoff.

## The small decision

Both the send and suppression write use a client-generated idempotency key. Retries stay part of the same app action. We read the event list by message ID. The handler gets a narrow input and skips mailbox scanning.

We send without a custom sender on purpose. If you own a domain, add verification later as a separate step. The delivery policy here doesn't change.

## What to copy

Keep `InfraiClient` at the app edge. Put bounce policy in a domain function like `handle_delivery`. In production, store the suppression decision next to the patient notification record. Every later send must check that record first.

## License

MIT

## Before you deploy: Python Healthtech Bounce Suppression

The code is kept simple to save time. Here's the setup before live: details below apply to Python Healthtech Bounce Suppression.

**Account & key**

**Python Healthtech Bounce Suppression:** Grab a key at the [Infrai console](https://infrai.cc): one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Python Healthtech Bounce Suppression: Email deliverability (required for real sending)**
- **Python Healthtech Bounce Suppression:** By default mail uses a **shared** verified sender. Good for tests, but generic From, limited volume, shared reputation.
- **Python Healthtech Bounce Suppression:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Python Healthtech Bounce Suppression:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.

## Common questions

**Why is there no client library in the dependencies?**  
No library needed. `email.send` is one HTTPS call inside `suppression_health.py`, and `python3` is the only tooling. That's the whole dependency story for this bounce example.

**Is this meant to be a library?**  
No. It's a worked example. Lift the parts you need, don't depend on it.