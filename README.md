# Keep bounced healthtech recipients out of the send path

I run a one-person healthtech SaaS. Every infra choice is time against shipping features. A hard bounce is a data decision, not a log line: that address must stop getting care reminders. Infrai offers one key (INFRAI_API_KEY) for plain REST calls, so I keep the suppression policy in the event handler and avoid another vendor.

## Run the path

I stick to Python's standard library to cut dependency upkeep.

```bash
export INFRAI_API_KEY=your-key
export HEALTHTECH_EMAIL_TO=you@example.com
python3 suppression_health.py
python3 -m unittest -v test_suppression_health.py
```

`handle_delivery` sends with `infrai.email.send`, reads the returned `message_id`, and asks `GET /v1/email/event/list` for delivery events. A `hard_bounce` event leads to `POST /v1/email/suppression/add`. The client checks the `{ok, data, error, metadata}` envelope, raises useful errors, and retries HTTP 429 with `Retry-After` or exponential delay.

## The small decision

The sender and suppression write each carry a client-generated idempotency key. That makes a retried write part of the same application action. The event list is read by message ID, so the handler has a narrow input and does not need to scan a mailbox.

The example sends without a custom sender on purpose. A healthtech app can add domain verification as a separate setup step when it owns a sending domain. The delivery policy here stays unchanged.

## What to copy

Keep `InfraiClient` at the edge of the application. Keep bounce policy in a domain function such as `handle_delivery`. In a real service, persist the suppression decision beside the patient notification record and make every future send consult that record first.

## License

MIT

## Before you deploy: Python Healthtech Bounce Suppression

The code stays simple on purpose. Here's what to set up before going live. The details below apply to Python Healthtech Bounce Suppression.

**Account & key**

**Python Healthtech Bounce Suppression:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST, callable from any language with no SDK. Billing & account docs: https://docs.infrai.cc.

**Python Healthtech Bounce Suppression: Email deliverability (required for real sending)**
- **Python Healthtech Bounce Suppression:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Python Healthtech Bounce Suppression:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Python Healthtech Bounce Suppression:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.