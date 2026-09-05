# Examples — LinkedIn Humanizer

## Example

> **Input:**
> "In today's fast-paced landscape, businesses must fundamentally leverage AI to unlock robust ROI. It's not just about adoption, it's about transformation. As of my last update in January 2024, the trends are clear — here's what I've learned."
>
> **Output (default mode = forensic + strict):**
> "businesses need AI to cut costs. adoption is the easy part. transformation is the actual work. here's what we learned running 35k LinkedIn profiles through our system daily."
>
> **Diff:**
> - FORENSIC: removed "As of my last update in January 2024" disclaimer
> - STRICT: paragraph scored 5 markers (fast-paced landscape, fundamentally, leverage, unlock, robust) = rewrite the paragraph, not word-by-word
> - STRICT: removed "It's not just X, it's Y" negative parallelism (single-hit rule), replaced with paired declaratives
> - PASS 1: the one em dash was under the cap (~1 per 100 words); it went only because the sentence around it was rewritten. It was not replaced with a period
> - PASS 3: added a number with a referent (35k LinkedIn profiles, daily) from the user's own input; nothing fabricated, no hedge, no "let me be honest" frame
> - PASS 4: two fragments in the output ("adoption is the easy part." "transformation is the actual work.") are within the 2-per-post cap and are paired declaratives, not a "The result?" reveal; left as is
> - AESTHETIC was NOT applied
