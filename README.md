# Leads & AI

A dependency-free CRM starter for a website agency. Requires Python 3.10+; Node is optional.

## Run

Run `python3 server.py` from this directory (or `npm start`). The server listens on port 3000; set `PORT` to override it. SQLite data persists in ignored `data/crm.sqlite`.

The workspace supports manual lead entry, search and stage filtering, requirement capture, outreach drafts, template-based website concept previews, editable starter package prices, meeting records, and downloadable calendar events with a 15-minute reminder. Prices are stored per browser; leads are stored in SQLite.

## Integration boundaries

Lead discovery, automatic outreach, AI website generation, public website hosting, client-facing proposals, email notifications, and calendar synchronization are not connected. Website previews are local templates, not AI output. No messages are sent. These capabilities need provider selection and secure server-side integration.

This development starter has no authentication or tenant isolation. Add those before hosting real client information on a public server. The `/preview/<lead-id>` route exposes the saved business requirements as concept copy; review copy before external publication.

## Validate

Run `python3 -m unittest discover -s tests`. Start the server and request `/api/leads`, create a lead, update its requirements, and open `/preview/<id>` for a functional smoke check.
