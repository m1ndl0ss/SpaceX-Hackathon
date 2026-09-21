# Yosemite — conservation coordination

A persistent browser demo connecting activists with a government dashboard. All application code, sample records, and tests live in `app`.

## Run

```bash
npm install
npm run dev
```

Open the URL printed by Vite. Use **Switch workspace** to move between roles. Use the same origin (hostname and port) in each tab to share records.

- **Activist:** enter a name and profile, submit a violation with location, observation time, urgency, details, and an optional evidence link. Follow its response history. Browse calls for help, join a crew, read government updates, or withdraw a signup.
- **Government:** review and filter the violation inbox, post a response and status, request volunteers for a specific violation, or publish an independent call for help. See each roster, post updates, close signups, and complete or cancel an action.
- The overview derives its counts, priorities, and activity from the same records. Resolving a violation is separate from completing a volunteer action. Closed violations can be reopened with an explanation.

## Persistence and demo scope

Reports, calls, profiles, signups, and response history are stored in `localStorage` under `yosemite.workspace.v1`. Refreshing preserves records; tabs on the same origin receive updates. Each tab remembers its active role/profile using `sessionStorage`. Returning with the same profile name restores that activist's identity and records. Profiles are demo identities, not authenticated accounts.

Sample records are created on first use, with upcoming action dates relative to that first visit. A full, closed, cancelled, completed, or past action cannot accept new signups. Withdrawing frees capacity. Errors from full or unavailable browser storage are shown without discarding the form.

This demo does not share data across browsers/devices or send email, alerts, invitations, or external submissions. Evidence is a link; files are not uploaded. Clearing this site's browser data removes its saved workspace.

The existing simulation remains separate from these workflows.

## Maps

Maps use Mapbox. Copy `.env.example` to `.env`, add a public `VITE_MAPBOX_TOKEN`, and restart Vite. Reports, calls, and dashboard controls work without a map token. Conservation layers and the sample map incident are illustrative; free-text report locations are not geocoded.

## Validation

```bash
npm test       # workflow rules, lifecycle, capacity, identity, persistence, and failure cases
npm run build # production bundle in dist/
npm run preview
```
