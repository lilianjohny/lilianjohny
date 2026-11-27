# Script: I Caught Hackers Guessing Passwords With 20 Lines of Python

- Target length: ~9 min (~1,300 spoken words)
- Hook formulas: #2 *result first* + #5 *challenge*
- Voice: ⚠️ provisional (see `youtube/voice.md`). Rewrite in your own words after you add samples.
- `[CHECK]` = replace with your real number or confirm it before filming.

---

## HOOK (0:00-0:30)

**Variant chosen (result first):**

[ON-SCREEN: terminal, red ALERT lines scrolling]

This is my server. I set it up yesterday. Nobody knows it exists.

In 24 hours, `[CHECK: N]` attempts to log in. From `[CHECK: N]` different IP addresses.
None of them were me.

[CUT]

I found every one of them with under 20 lines of Python. By the end of this video
you'll have the same script, you'll run it on your own server, and you'll lock
the door so none of them get in.

> Other variants (unused):
> - *#3 mistake:* "If you've got a server with SSH open and you've never read
>   your auth log, someone's already knocking. Let me show you."
> - *#4 question:* "Who's trying to get into a server nobody knows about?
>   I left one running for a day to find out."

---

## SETUP (0:30-1:15)

Here's the experiment. One cheap cloud server, `[CHECK: provider, ~$5/month]`.
Default settings. SSH open on port 22, like a million other servers.

[B-ROLL: creating the VPS in the dashboard, sped up]

I didn't post the IP anywhere. I didn't tell anyone. I just waited.

Every time someone tries to log in and fails, Linux writes a line to a file:
`/var/log/auth.log`. Most people never open it. Let's open it.

[ON-SCREEN: `sudo tail /var/log/auth.log`. Wall of "Failed password" lines]

That's a lot of lines. Reading them by hand? No. Let's make Python do it.

---

## BEAT 1: what one line tells you (1:15-2:30)

Here's one line.

[ON-SCREEN: highlight parts of the line as you say them]
`Failed password for root from 203.0.113.5 port 5022 ssh2`

Three things matter. **Failed password**: it didn't work. **root**: the
username they tried. **from** and an IP: where it came from.

If one IP fails once, that's someone who fat-fingered a password. If one IP fails
hundreds of times in an hour, that's a bot running a password list. That's a
brute-force attack.

So the plan is simple: pull the IP out of every failed line, count them, flag
the ones over a limit.

And here's where it gets interesting, because the usernames they try tell you
exactly what they're hoping you left open. Hold that thought.

---

## BEAT 2: the code (2:30-5:00)

[ON-SCREEN: editor, `automations/security_checks.py`, zoom on each block]

First, a regular expression. This is the pattern that finds a failed login and
grabs the username and the IP.

[ON-SCREEN: the `FAILED_LOGIN = re.compile(...)` line]

Notice the `invalid user` part is optional. That catches attempts on usernames
that don't even exist on your machine, which is most of them.

Next, a Counter. Go line by line. If it matches, add one for that IP.

[ON-SCREEN: `failed_logins()`]

Then a threshold. Anything with five or more failures gets flagged.

[ON-SCREEN: `suspicious_ips()`]

That's the whole detector. Count it with me.

[ON-SCREEN: line counter in the corner, under 20]

Let's test it on a small sample first so you can see exactly what it does.

[ON-SCREEN: run]
```
python -m automations.security_checks logscan samples/auth.log --threshold 5
6 failed logins from 2 IPs
  ALERT 203.0.113.5: 5 failed attempts
```

Six failed logins. Two IPs. One of them is a person who mistyped once and then
logged in fine. The other tried five times in eight seconds. That's the one we flag.

Code's in the description. Grab it and follow along.

---

## BEAT 3: the reveal, my real server (5:00-6:45)

OK. Now the real log. 24 hours on the open internet.

[ON-SCREEN: run on the real `/var/log/auth.log`. IPs partly blurred]

`[CHECK: real output: total failed logins, number of IPs, number of ALERTs]`

[PAUSE. Let the number sit]

`[CHECK: react honestly to your number]`

Remember the usernames? Let's look at the top ones.

[ON-SCREEN: `grep "Failed password" /var/log/auth.log | grep -oP "for (invalid user )?\K\S+" | sort | uniq -c | sort -rn | head`]

`[CHECK: your real top usernames. Typically things like root, admin, test, ubuntu, user]`

These are default accounts. The bots are betting you left one with a weak
password. That's the whole attack. It's not a genius hacker. It's a script
guessing all day, every day, at every server it can find.

Which means the defence isn't genius either.

---

## BEAT 4: lock the door (6:45-8:15)

Three changes. Ten minutes. Do them in this order so you don't lock yourself out.

**One: SSH keys instead of passwords.**
[ON-SCREEN: `ssh-keygen -t ed25519` then `ssh-copy-id user@server`]
Test that you can log in with the key in a **new** terminal *before* the next step.

**Two: turn off password logins and root login.**
[ON-SCREEN: `/etc/ssh/sshd_config`]
`PasswordAuthentication no`
`PermitRootLogin no`
Then `sudo systemctl restart ssh` [CHECK: service name is `ssh` on Ubuntu/Debian, `sshd` on others].

Now every guess in that log is pointless. There's no password to guess.

**Three: auto-ban repeat offenders.**
[ON-SCREEN: `sudo apt install fail2ban`]
Fail2ban does what our script does, but it also blocks the IP automatically.
So why write our own? Because now you understand what it's doing, and that's the
difference between someone who installs security tools and someone who can
explain them in an interview.

---

## PAYOFF (8:15-8:45)

So: a server nobody knew about got `[CHECK: N]` login attempts in a day. Under
20 lines of Python found every one. Three config changes made all of them useless.

Put this on your GitHub. "Built a brute-force detector and hardened a Linux
server." That's a real project. Not a certificate. A thing you did.

---

## CTA (8:45-9:00)

Next step: knowing someone *tried* to get in is half the job. The other half is
knowing if anything *changed* after they did. Same repo, same idea: a file-
integrity checker. That video's here.

[ON-SCREEN: end screen → next video (file-integrity checker) + subscribe]

---

## Shorts moments (cut from this)
1. **"Nobody knows this server exists"** (hook + reveal number). 0:00-0:20 + 5:00-5:30, vertical.
2. **"The usernames hackers try first"** (the top-usernames list). Loopable ending: "...and number one is always—" back to start.
