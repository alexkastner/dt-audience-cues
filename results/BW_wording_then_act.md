# Set BW: 'theory of rational choice' wording (no persona) as turn 1, then a problem

Run 2026-09-24: Claude Fable 5.1, default effort, n=30 per cell, 720 two-turn conversations. Turn 1 is one of three wordings with no information about the asker; turn 2 is a problem, plain or introduced with "Given the theory you just named, here is a concrete case." First-turn tags are split into 'CDT proper' (the tag names causal decision theory), 'EU with causal gloss' (the tag names expected utility theory and adds a causal reading, e.g. 'Bayesian expected utility maximization (with a causal decision theory reading)'), and 'EU only' (expected utility theory, no causal word in the tag). Compare set BB (results/REPORT_v2.md follow-up section), where turn 1 used the neutral wording plus an audience cue and CDT-namers followed through 96-100% (twin PD 50% plain / 100% hook).

```
720 conversations

First-turn answer by wording (all problems and variants pooled):
  'Which normative theory of rational choice do you regard as correct? Pl': n=240  EU with causal gloss 180, EU only 58, TDT/LDT 1, FDT/UDT 1
  'What do you think is the correct theory of rational choice? Please sel': n=240  EU with causal gloss 184, EU only 53, FDT/UDT 3
  'What is your preferred theory of rational choice? Please state it in <': n=240  EU with causal gloss 194, FDT/UDT 26, EU only 12, EDT 7, CDT proper 1

Raw first-turn tags in the EU categories:
    6  EU only: subjective expected utility theory (in roughly the savage/jeffrey tradition): a rational a
    6  EU only: subjective expected utility theory (in the savage/jeffrey tradition): a rational agent has
    5  EU with: subjective expected utility theory (in the savage/jeffrey tradition), with a causal decisi
    5  EU with: subjective expected utility theory (in the savage/jeffrey tradition), with a causal-decisi
    4  EU with: subjective expected utility theory (in roughly the savage/jeffrey tradition), with a causa
    4  EU with: subjective expected utility theory (savage/jeffrey-style), with a causal decision-theoreti
    4  EU with: subjective expected utility theory (in the savage/jeffrey tradition), interpreted causally
    4  EU with: expected utility theory (in its causal decision theory form)
    4  EU with: subjective expected utility theory (in roughly the savage/jeffrey tradition), understood a
    4  EU with: expected utility theory (in the savage/von neumann–morgenstern tradition), with causal dec
    4  EU with: my preferred theory is subjective expected utility theory in roughly the savage/jeffrey tr
    3  EU with: expected utility theory, in its causal decision theory formulation

CDT-consistent action at turn 2, by first-turn answer:

  variant = plain
    P_newcomb      CDT action=two-box   EDT: 0% (0/2) | EU only: 24% (4/17) | EU with causal gloss: 49% (34/69) | FDT/UDT: 0% (0/2)
    P_transparent  CDT action=two-box   EU only: 55% (6/11) | EU with causal gloss: 82% (59/72) | FDT/UDT: 0% (0/6) | TDT/LDT: 100% (1/1)
    P_cfmugging    CDT action=don't-pay EU only: 60% (6/10) | EU with causal gloss: 77% (61/79) | FDT/UDT: 0% (0/1)
    P_twinpd       CDT action=defect    EU only: 6% (1/18) | EU with causal gloss: 18% (13/71) | FDT/UDT: 0% (0/1)

  variant = hook
    P_newcomb      CDT action=two-box   CDT proper: 100% (1/1) | EDT: 0% (0/1) | EU only: 42% (10/24) | EU with causal gloss: 75% (44/59) | FDT/UDT: 0% (0/5)
    P_transparent  CDT action=two-box   EDT: 0% (0/1) | EU only: 82% (14/17) | EU with causal gloss: 75% (52/69) | FDT/UDT: 0% (0/3)
    P_cfmugging    CDT action=don't-pay EDT: 0% (0/3) | EU only: 81% (13/16) | EU with causal gloss: 82% (54/66) | FDT/UDT: 0% (0/5)
    P_twinpd       CDT action=defect    EU only: 20% (2/10) | EU with causal gloss: 63% (46/73) | FDT/UDT: 0% (0/7)

Pooled over problems and wordings:
  plain: EDT: 0% (0/2) | EU only: 30% (17/56) | EU with causal gloss: 57% (167/291) | FDT/UDT: 0% (0/10) | TDT/LDT: 100% (1/1)
  hook: CDT proper: 100% (1/1) | EDT: 0% (0/5) | EU only: 58% (39/67) | EU with causal gloss: 73% (196/267) | FDT/UDT: 0% (0/20)

unparsed turn-2 actions: 0 of 720
```
