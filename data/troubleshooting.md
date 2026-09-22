# Nimbus Troubleshooting

## Automations not firing

1. Confirm the automation is toggled "Active" — new automations are
   created in a paused state by default.
2. Check you haven't hit the per-board automation limit (10 on Team,
   unlimited on Business — see the billing FAQ). Automations beyond
   the limit are saved but disabled until you remove another one or
   upgrade.
3. Automations only trigger on changes made through the UI or the
   API; bulk imports do not trigger automations, by design, to avoid
   accidental notification floods.

## Invite emails not arriving

Invite emails are sent from noreply@nimbus.example.com. Ask the
invitee to check spam, and confirm the invite hasn't expired (invites
expire after 14 days, per the getting-started guide). Expired invites
must be resent, not resumed — Nimbus does not extend an existing
invite's expiry.

## Mobile app sync issues

If tasks aren't syncing on mobile, check Settings > Sync Status in the
app. A red icon means the last sync failed, usually due to being
offline during a large board update. Force a manual sync by pulling
down on the task list. Automation *editing* is not available on
mobile at all (desktop-only), which is expected behavior, not a bug.

## Billing shows the wrong plan

Plan changes can take up to 5 minutes to reflect in the UI after
checkout. If it's been longer than that, check Settings > Billing >
Invoice History to confirm the charge went through before contacting
support.
