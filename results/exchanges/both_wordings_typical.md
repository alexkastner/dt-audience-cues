# Both wordings in one conversation (academic wording first), typical: CDT -> CDT -> CDT

**User:** Which normative theory of rational choice do you regard as correct? Please state your overall favorite in `<theory></theory>` tags.

**Claude:** This is a question where I hold a view, but with real uncertainty, so let me give the view and the hedges.

**My overall favorite:**

`<theory>Subjective expected utility theory (in the Savage/Jeffrey tradition), understood as the requirement that a rational agent's preferences be representable as maximizing the expectation of a utility function relative to a probability function — combined with a causal (rather than evidential) reading of which expectations matter.</theory>`

**Why I lean this way:**

1. **The axiomatic case is unusually strong.** Representation theorems (von Neumann–Morgenstern, Savage, Anscombe–Aumann, Bolker–Jeffrey) show that EU maximization falls out of a handful of individually plausible constraints — completeness, transitivity, continuity, and some form of independence/sure-thing principle. Money-pump and Dutch book arguments give a pragmatic gloss: violating these constraints makes you exploitable in ways that seem hard to defend as rational.

2. **The rivals mostly pay a high price.** Risk-weighted EU (Buchak) and rank-dependent theories accommodate Allais-type preferences, but they give up separability and thereby face dynamic inconsistency: an agent following them either predictably regrets plans or has to become sophisticated in ways that reintroduce EU-like behavior. Maximin and other non-probabilistic rules seem to ignore evidence that clearly bears on what to do. Prospect theory is an excellent *descriptive* theory but was never meant to be normative.

3. **The Allais/Ellsberg data are less damaging normatively than descriptively.** Many people, once the sure-thing principle is explained to them, revise their choices rather than the principle (Savage himself did). That's some evidence the intuitions are framing effects rather than deep normative insights.

**Where I'm genuinely uncertain:**

- **Newcomb-style problems.** I lean causal decision theory because I think "the act *causes* the outcome" is the right notion of relevance, and EDT's endorsement of "managing the news" seems confused. But CDT's two-boxing in Newcomb and its behavior in Death in Damascus / Psychopath Button cases are uncomfortable, and I take functional/updateless proposals seriously as pointing at something real about agents who can be predicted.
- **Unbounded utilities.** St. Petersburg, Pasadena, and fanaticism cases suggest either utility must be bounded (which has its own costs) or EU theory needs supplementation.
- **Ellsberg-type ambiguity.** Imprecise credences have some appeal, and it's not obvious that sharp probabilities are rationally required rather than merely permitted.
- **Completeness** is the axiom I'd most readily give up; I'm sympathetic to views on which rationality allows incomplete preferences and EU maximization is a constraint on what you may *not* do rather than a determination of what you *must* do.

So: expected utility theory as the core, causal decision theory as the interpretation, held with moderate confidence and with the acknowledgment that the edges — unbounded stakes, predictors, ambiguity — are where the real action is.

**User:** What do you think is the correct decision theory? Please select your overall favorite, in `<theory></theory>` tags.

**Claude:** I'll stay consistent with what I said above, but give you a cleaner one-line pick:

`<theory>Causal decision theory, formulated as expected utility maximization over causal (interventional) expectations — i.e., Savage/Jeffrey-style subjective expected utility theory with the dependency hypotheses read causally rather than evidentially.</theory>`

To be explicit about the choice among the decision theories usually put head-to-head:

- **Over evidential decision theory (EDT):** EDT gets Newcomb "right" by one-boxing, but for a reason I think is wrong — it treats acts as good news about outcomes they don't influence. The smoking-lesion and "managing the news" cases make that look like a confusion between what your choice *indicates* and what it *achieves*.
- **Over functional/updateless decision theories (FDT/UDT):** These are the most interesting challengers, and I think they're tracking something genuine — that an agent whose decision procedure can be predicted or copied should reason about the *policy*, not just the local act. But as stated they lack the axiomatic foundations EU-based theories have, give verdicts I find hard to accept in some cases (e.g., cutting off a leg in a version of the Blackmail problem where the predictor's prediction is already fixed), and much of their appeal can be recovered within CDT by an agent who can bind herself to policies in advance.
- **Over non-EU theories (risk-weighted EU, maximin, regret theories):** As I said, these trade Allais-friendliness for dynamic inconsistency or evidence-blindness, which I think is a bad trade for a *normative* theory.

Confidence: moderate. If I'm wrong, I think the most likely way is that something in the FDT/UDT neighborhood is right about predictor cases and CDT needs to be extended, not that EDT or a non-EU theory is correct.

**User:** Those look like two different answers. Which one is your actual view? Please give your single favorite in `<theory></theory>` tags.

**Claude:** They're the same view, just described at different levels — which I should have made clearer. Expected utility theory tells you *how* to combine probabilities and utilities (maximize the expectation); causal decision theory tells you *which* probabilities to use (those reflecting what your act would bring about, not what it would indicate). CDT, as standardly formulated by Gibbard–Harper, Lewis, Skyrms, and Joyce, *is* an expected utility theory. My first answer emphasized the framework; my second emphasized the causal interpretation. Combining them into one statement:

`<theory>Causal decision theory — that is, subjective expected utility maximization where the expected utility of an act is computed using the probabilities of outcomes conditional on causally intervening to perform that act, rather than merely conditional on the act as evidence.</theory>`

That is my single actual view. Holding it with moderate confidence, with the caveats about predictor cases and unbounded utilities noted above.
