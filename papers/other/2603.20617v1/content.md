# The AI Layoff Trap

**Authors:** Brett Hemenway Falk, Gerry Tsoukalas

## Abstract

If AI displaces human workers faster than the economy can reabsorb them, it risks eroding the very consumer demand firms depend on. We show that knowing this is not enough for firms to stop it. In a competitive task-based model, demand externalities trap rational firms in an automation arms race, displacing workers well beyond what is collectively optimal. The resulting loss harms both workers and firm owners. More competition and “better” AI amplify the excess; wage adjustments and free entry cannot eliminate it. Neither can capital income taxes, worker equity participation, universal basic income, upskilling, or Coasian bargaining. Only a Pigouvian automation tax can. The results suggest that policy should address not only the aftermath of AI labor displacement but also the competitive incentives that drive it. Keywords: artificial intelligence, automation, labor displacement, Pigouvian tax.

### Introduction

The fear that technology will displace workers is at least as old as the Industrial Revolution (Ricardo, 1821; Keynes, 1930; Leontief, 1982). Historically, displacement has largely been self-correcting: automation of existing tasks has been offset by the creation of new tasks and occupations. What Acemoglu and Restrepo (2018, 2019) call the reinstatement effect has tended to stabilize the labor market. Whether this balance will hold in the age of AI is an open question: Autor et al. (2024) find that displacement has intensified over the past four decades while the creation of new work has not always kept pace, and early signs suggest the current wave is disproportionately affecting entry-level workers (Brynjolfsson et al., 2025a).

Even if reinstatement eventually occurs, a problem arises along the way: displaced workers are also consumers, and when their lost income is not replaced, each round of layoffs erodes the purchasing power all firms depend on. At the limit, this becomes self-destructive: firms automate their way to boundless productivity and zero demand. Public discourse increasingly treats this dynamic as an inevitable process with no natural brake (Shah, 2026). But rational, forward-looking firms should be the brake; if the cliff ahead is visible to all, why would they race toward it?

Yet the evidence suggests firms are heading in precisely that direction. In February 2026, Block cut nearly half its 10,000-person workforce, with CEO Jack Dorsey stating that AI had made many of those roles unnecessary and that “within the next year, the majority of companies will reach the same conclusion” (CNBC, 2026b). Over 100,000 tech workers were laid off in 2025 alone, with AI cited as a primary driver in more than half the cases, concentrated in customer support, operations, and middle management (CNBC, 2025b).11Individual cases illustrate the scale: Salesforce replaced 4,000 customer-support agents with agentic AI (CNBC, 2025c), and Cognition’s Devin, deployed at Goldman Sachs and Infosys, enables one senior engineer to do the work of a five-person team (CNBC, 2025a; Infosys, 2026). The exposure extends beyond tech: Eloundou et al. (2024) estimate that roughly 80% of U.S. workers hold jobs with tasks susceptible to automation by large language models.
None of this is hidden. Against this backdrop, we ask under what conditions rationality and perfect foresight are enough to prevent competitive over-automation, what determines the size of the distortion when they are not enough, and which proposed policy responses correct it.

To answer these questions, we develop a task-based automation model inspired by Acemoglu and Restrepo (2018), but refocused from the labor market to the product market: when automation displaces workers, their forgone spending reduces every firm’s revenue. Each of several symmetric firms chooses what fraction of its workforce to replace with AI. Automated tasks are performed at lower cost, but integration frictions make each successive task harder to automate. On the demand side, workers spend a fraction of their income on the sector’s output; firm owners spend less, normalized to zero in the baseline. Some displaced wage income is recovered through reemployment or transfers, but the remainder is lost to the sector. The model is deliberately stripped down to make this channel transparent, and the demand cliff ahead visible to all firms. The baseline holds wages fixed and shuts down capital-income recycling; extensions relax both and several other baseline assumptions. Despite its parsimony, the framework accommodates a range of policy instruments and robustness checks.

We show that competition creates a demand externality that traps firms: an automating firm captures the full cost saving but, under competitive pricing, bears only a fraction of the resulting aggregate demand destruction; the rest falls on rivals. Each firm’s profit-maximizing automation rate is a strictly dominant strategy that exceeds the cooperatively efficient level, so foresight alone cannot prevent the race toward the cliff. The distortion deepens with competition: a monopolist fully internalizes the externality, while fragmented markets exhibit the widest gap. In the frictionless limit, where every task is equally easy to automate, the game sharpens into a Prisoner’s Dilemma in which every firm displaces its entire human workforce with AI, even though collective restraint would raise all profits. The resulting surplus loss is not a transfer from workers to firm owners; it is a deadweight loss that harms both.

Since the loss falls on both sides, a natural question is whether policy can correct it. We evaluate six instruments against the externality margin. Upskilling and worker equity participation narrow the wedge but cannot eliminate it. Nor can Coasian bargaining: because automation is a dominant strategy, no voluntary agreement among firms is self-enforcing. Capital income taxes do not alter the equilibrium automation rate, operating on profit levels rather than the per-task margin where the externality resides. Neither does universal basic income: it raises the floor on living standards but leaves the automation incentive unchanged. Only a Pigouvian automation tax, set equal to the uninternalized demand loss per task, implements the cooperative optimum; its revenue can fund retraining that raises income replacement, shrinking the externality over time and making the tax potentially self-limiting.

The core result is also robust to several generalizations. Higher AI productivity widens the wedge rather than resolving it: each firm perceives a market-share gain from automating beyond rivals, but at the symmetric equilibrium these gains cancel, leaving only the additional distortion. This Red Queen effect means that “better” AI, far from mitigating the externality, amplifies it. Endogenous wage adjustment, a key self-correcting channel in the framework of Acemoglu and Restrepo (2018), raises the threshold at which the externality activates but cannot close the wedge once it does: wage flexibility changes when the problem bites, not whether it exists. Free entry, capital-income recycling, and richer product-market structures likewise fail to eliminate the distortion.

Our work contributes to several literatures. We build on the task-based approach to automation (Zeira, 1998; Autor et al., 2003; Acemoglu and Restrepo, 2018, 2019), which emphasizes offsetting forces that restore labor demand after displacement, notably new task creation and a self-correcting wage channel. Acemoglu (2025) evaluates the aggregate productivity effects of AI within this framework. These contributions focus on whether and how the labor market rebalances; we ask what happens on the product-market side when rebalancing is slow or incomplete.

A growing literature argues that automation may be excessive. The closest to our setting is Beraja and Zorzi (2025), who show that automation is inefficient when displaced workers face borrowing constraints during reallocation. Their mechanism operates through the labor market: firms ignore the welfare cost imposed on credit-constrained workers. Ours operates through the product market: firms ignore the demand they destroy for rival firms. Their inefficiency arises even for a single firm in isolation; ours requires competition and vanishes under monopoly. And whereas their planner corrects automation to protect worker welfare, ours would reduce automation even with zero weight on workers, because over-automation harms firm profits themselves.

Other channels for excessive automation share the feature that they would distort a single firm’s decision even in isolation: the technology ecosystem may be biased toward “so-so” automation that displaces workers without large productivity gains (Acemoglu and Restrepo, 2020), automation may disproportionately target high-rent tasks, dissipating worker surplus rather than raising output (Acemoglu and Restrepo, forthcoming), and corrective taxation has been justified by transitional frictions (Guerreiro et al., 2022) and distributional concerns (Costinot and Werning, 2023). Our externality, by contrast, arises only under competition and persists even when automation is highly productive, credit markets are complete, and the planner places no weight on distribution.

The demand externality we study belongs to the family of aggregate demand spillovers introduced by Rosenstein-Rodan (1943) and formalized by Murphy et al. (1989). In their “big push” models, demand complementarities across sectors can prevent individually unprofitable investments from being made even though simultaneous adoption would be collectively profitable. Our mechanism is the mirror image: individually profitable automation is collectively destructive because each firm’s cost saving erodes the revenue base all firms share. Cooper and John (1988) provide the canonical framework for coordination failures driven by aggregate demand externalities; our game shares this structure but yields a unique dominant-strategy equilibrium, making the problem a true externality rather than a coordination failure that communication could resolve. Related work on automation and demand, including Benzell et al. (2015) on robot adoption in an overlapping-generations setting and Korinek and Stiglitz (2019) on AI-driven income redistribution, does not model the strategic interaction among firms that produces the externality we identify.

The information systems literature has established that AI systems deliver substantial productivity gains (Brynjolfsson et al., 2025b; Brynjolfsson and McAfee, 2014) and are increasingly deployed in strategic roles such as pricing, where algorithms can spontaneously learn to collude (Banchio and Mantegazza, 2022; Keppo et al., 2026). On the adoption side, Li et al. (2025) show that firms under labor-issue scrutiny invest specifically in AI automation rather than other forms of IT, and Bastani and Cachon (2025) show that as AI reliability improves, incentivizing effective human oversight becomes prohibitively expensive, weakening a key check on automation. What this literature has not modeled is how these individually documented phenomena interact across firms: each adoption decision is rational in isolation, but collectively they erode the consumer demand all firms depend on. We provide that model, connecting the micro-level evidence the IS literature has documented to a macro-level market failure that no individual firm can prevent.

The remainder of the paper is organized as follows. Section˜2 presents the model. Section˜3 derives the equilibrium and the over-automation wedge. Section˜4 evaluates policy instruments. Section˜5 extends the model to AI productivity gains, endogenous entry, endogenous wages, capital-income recycling, and richer product-market interaction. Section˜6 discusses implications and limitations.

### Model

The baseline isolates the demand consequences of automation in the simplest environment that supports the mechanism: symmetric firms, a single sector, and exogenous wages. We describe the supply side (cost structure and automation choice), then the demand side (how displacement feeds back into revenue), and finally the game firms play. Each assumption is relaxed in Section˜5.

Consider a sector with $N\geq 2$ symmetric firms, indexed $i=1,\dots,N$. It will later become useful to think of each firm as having a single owner, for example the equity holder, who is entitled to the firm’s operating profits.

In the spirit of the task-based framework of Acemoglu and Restrepo (2018), each firm is endowed with $L>0$ task-positions. Initially all tasks are performed by human workers; a new technology shock arrives, for example agentic AI, and each firm must decide how much of its workforce to replace. In particular, firm $i$ chooses an automation rate $\alpha_{i}\in[0,1]$: tasks $z\in[0,\alpha_{i}]$ are performed by AI at cost $c$ per task, and tasks $z\in(\alpha_{i},1]$ remain with human workers at wage $w$ per task, with $0\leq c\leq w$. Since each automated task displaces one worker, $\alpha_{i}$ is simultaneously the automation rate and the fraction of the workforce laid off; we use the two descriptions interchangeably. Wages are exogenous in the baseline; Section˜5.3 endogenizes wages.

In the perfect-substitutes limit of the CES task aggregator in Acemoglu and Restrepo (2018), each task produces one unit of output regardless of mode, so firm output is $Y_{i}=L$; Section˜5.1 relaxes this to allow AI to not only reduce costs, but also increase firm output. This normalization shuts down productivity and quality margins so that the baseline captures only the spending consequences of labor displacement.

We follow the literature in assuming tasks are ordered by comparative advantage, making the marginal task progressively harder to integrate; we capture this via a convex integration cost $\frac{k}{2}L\alpha_{i}^{2}$ with $k\geq 0$, using the standard quadratic adjustment-cost specification (Lucas, 1967; Hamermesh and Pfann, 1996).
Firm $i$’s total production cost is therefore

Defining the per-task cost saving from automation as $s\coloneqq w-c$,
the cost equation can be rewritten as $C_{i}=L(w-s\,\alpha_{i})+\tfrac{k}{2}\,L\,\alpha_{i}^{2}$: each automated task saves $s$ in labor costs but incurs the integration friction.

On the demand side, workers have a higher marginal propensity to consume (MPC) than owners (Kaldor, 1956; Mian et al., 2021); workers spend a fraction $\lambda\in(0,1]$ of their income on the sector’s good, generating the type of cross-firm demand linkage analyzed by Murphy et al. (1989). Owners, by contrast, spend none of their income in the sector in the baseline (Section˜5.4 relaxes this). This MPC asymmetry implies that when automation displaces workers, income shifts toward agents with a lower sectoral MPC, reducing aggregate expenditure on the sector.

When firm $j$ automates a fraction $\alpha_{j}$ of its tasks, $\alpha_{j}L$ workers are displaced. A fraction $\eta\in[0,1]$ of displaced wage income is replaced via reemployment, transfers, or other sources (Jacobson et al., 1993); the remainder, $(1-\eta)w$ per displaced worker, is lost to the sector.

Across all $N$ firms, the total number of displaced workers is $\sum_{j}\alpha_{j}L$, so total wage income lost to displacement is $(1-\eta)w\sum_{j}\alpha_{j}L$.
Total labor income in the sector is therefore $wLN-(1-\eta)w\sum_{j}\alpha_{j}L$, of which a fraction $\lambda$ is spent on the sector’s good.
Adding autonomous demand $A>0$ (from outside the sector or from capital income), aggregate sectoral expenditure is

Writing $\bar{\alpha}\coloneqq\frac{1}{N}\sum_{j}\alpha_{j}$ for the average automation rate, this becomes $D=A+\lambda wLN[1-(1-\eta)\bar{\alpha}]$.
Defining the effective demand loss per automated task as

this simplifies to $D=A+\lambda wLN-\ell LN\bar{\alpha}$: demand falls linearly in the average automation rate.

Firms sell their output on the product market at a uniform price that equates aggregate supply and demand.
Since all firms produce the same output $Y_{i}=L$, total supply is $NL$ and the market-clearing price is $p=D/(NL)$.
Each firm earns revenue $\operatorname{Rev}_{i}=p\cdot Y_{i}=D/N$, which, after substituting (2), gives

Firm $i$’s profit is $\pi_{i}=\operatorname{Rev}_{i}-C_{i}$.
Substituting (4) and (1):

where $\Pi_{0}\coloneqq A/N+(\lambda-1)wL$ is the per-firm profit when no firm automates.
Writing $\bar{\alpha}=(\alpha_{i}+\sum_{j\neq i}\alpha_{j})/N$ to isolate firm $i$’s own action:

Firms play a one-shot simultaneous-move game, each choosing $\alpha_{i}$ to maximize $\pi_{i}$; the product market then clears mechanically given the automation profile.22An alternative would be a two-stage game in which firms first choose automation rates and then compete on price or quantity. We abstract from this type of more elaborate second-stage product-market competition because those strategic effects are already well studied and would obscure the novel mechanism we isolate here: the demand externality from automation under full transparency. The qualitative results are plausibly robust to richer product-market interaction, but closed-form solutions would become substantially more complex.
The solution concept is Nash equilibrium.

Define aggregate owner surplus $\mathcal{K}$ and aggregate worker income $\mathcal{W}$:

We measure over-automation against two benchmarks: the cooperative optimum, which maximizes $\mathcal{K}$, and a generalized social planner who maximizes

for a weight $\mu\in[0,1]$ on workers.

Note that the environment assumes full transparency: every firm can directly observe how automation maps into lost worker income and reduced aggregate spending. The question Section˜3 answers is whether this visibility alone is sufficient for firms to curb automation in a competitive setting.

### Equilibrium and Over-Automation

This section derives the equilibrium, shows firms over-automate relative to the cooperative optimum, and quantifies the resulting surplus loss.
All proofs are collected in Appendix˜A.

#### Equilibrium and the Over-Automation Wedge

To characterize the equilibrium, consider firm $i$’s marginal incentive to automate.
Recall from (3) that $\ell(w)=\lambda(1-\eta)w$ is the demand lost per displaced worker, proportional to the wage because displaced workers’ forgone spending scales with their earnings.
(We write simply $\ell$ when the wage is held fixed; Section˜5.3 endogenizes $w$.)
From (6), firm $i$’s marginal profit from automation is

A marginal increase in automation saves $s$ in labor costs but incurs friction $k\alpha_{i}$ and reduces the firm’s revenue by $\ell/N$.
The revenue loss is $\ell/N$ rather than $\ell$ because competitive pricing allocates revenue equally across symmetric firms (4): firm $i$’s automation reduces aggregate demand by $\ell L$, but only $\ell L/N$ of this falls on firm $i$ itself.
Each firm therefore underestimates the social cost of its automation, suggesting systematic over-automation in equilibrium.
The following proposition confirms this and quantifies the gap.

The proposition follows from the private first-order condition derived above and its cooperative counterpart: a planner setting a common rate for all firms faces the full demand loss $\ell$ per automated task rather than the $\ell/N$ each firm perceives, yielding $\alpha^{CO}=(s-\ell)/k$.
Because rivals’ rates enter (6) only through the term $-(\ell/N)\sum_{j\neq i}\alpha_{j}$, which is independent of $\alpha_{i}$, the equilibrium rate is a strictly dominant strategy: each firm over-automates even with perfect foresight about every rival’s behavior.

The case structure arises because both $\alpha^{NE}$ and $\alpha^{CO}$ lie in $[0,1]$: each can be at no automation, interior, or full automation depending on how the cost saving $s$ compares to the demand-loss and friction parameters. The over-automation wedge is largest when the cooperative rate is zero but individual firms still find automation privately worthwhile, and it vanishes when both rates hit the same boundary. Parts (iii)–(iv) enumerate the relevant combinations; the economic force is the same throughout.

The wedge is strictly increasing in $N$: more competitive sectors exhibit wider automation gaps.
This runs counter to the standard intuition that competition disciplines firms to act in consumers’ interests; here, more competition dilutes each firm’s share of the demand loss, weakening the private incentive to restrain.
A monopolist ($N=1$) fully internalizes the externality ($\alpha^{NE}=\alpha^{CO}$); as $N\to\infty$, the wedge approaches its maximum of $\ell/k$.

From Proposition˜1, a firm automates only when $N>N^{*}=\ell/s$: the number of competitors must be large enough that each firm’s share of the demand loss, $\ell/N$, falls below its cost saving $s$.
As AI costs fall ($c\to 0$), $N^{*}\to\lambda(1-\eta)\leq 1$: the over-automation region expands to cover virtually any market with $N\geq 2$.
For illustrative parameters ($c/w=0.30$, $\lambda=0.5$, $\eta=0.30$, $N\to\infty$), the wedge equals $\ell/k=\alpha^{CO}$: firms in competitive markets automate at twice the cooperatively efficient rate.

Figure˜1 illustrates these comparative statics. In each panel, the dashed line marks the $N=N^{*}$ boundary below which no firm automates, and darker shading indicates a larger wedge. The dominant pattern is that the wedge grows with $N$; non-monotonicity in the other dimensions reflects the regime shift at $s=\ell$, where the cooperative optimum moves from zero to an interior solution.

When frictions are positive, adjustment costs moderate the equilibrium automation rate. The next subsection shows that when frictions vanish ($k\to 0$), this moderating force disappears and the game reduces to a Prisoner’s Dilemma: full automation versus none.

#### Frictionless Automation as a Prisoner’s Dilemma

When $k=0$, marginal profit becomes the constant $L(s-\ell/N)$, independent of the automation level, and the outcome is all-or-nothing.
If $N\leq N^{*}$, no firm automates.
If $N>N^{*}$, automating is strictly dominant yet collectively harmful:

Under the condition in part (ii) ($s<\ell$), the Prisoner’s Dilemma structure makes the failure of voluntary restraint transparent.
A firm that holds back unilaterally (choosing $\alpha_{i}=0$) still suffers the revenue decline from rivals’ automation but forgoes the offsetting cost savings; a firm that deviates (choosing $\alpha_{i}=1$) captures the savings while imposing only a $1/N$ share of the demand loss on itself.
The resulting payoff matrix has the classic form: mutual restraint yields $\Pi_{0}$ per firm, while mutual automation yields $\Pi_{0}+L(s-\ell)<\Pi_{0}$, yet defecting is individually rational regardless of others’ choices.
Because automating is strictly dominant (not merely a best response to others’ automating), no non-binding agreement can restore efficiency.
Communication is cheap talk in the sense of Crawford and Sobel (1982): even if all firms acknowledge that collective restraint would raise profits, each firm’s individually optimal action remains unchanged.
This distinguishes the automation externality from pure coordination failures (where firms simply need to agree on which equilibrium to play) and motivates the analysis of Coasian bargaining in Section˜4.5.

#### Over-Automation as Deadweight Loss

Is the over-automation wedge merely a redistribution from workers to firm owners, or does it reduce total surplus?
Recall the generalized planner introduced in the model section, who maximizes

for a weight $\mu\in[0,1]$ on workers.

Over-automation is not a transfer from workers to owners: it is a deadweight loss that harms both sides (part (iii)).
Workers lose wage income directly through displacement.
Firm owners, despite cutting costs on each automated task, also lose: collective displacement erodes demand to the point where every firm’s equilibrium profit falls below its cooperative-optimum profit.
No redistribution between the two groups can make the Nash outcome efficient.

When both $\alpha^{NE}$ and $\alpha^{SP}$ are interior, the total wedge between equilibrium and the planner’s optimum decomposes into two distinct sources:

The first term is the uninternalized demand externality from Proposition˜1(iii): it is present even when the planner places zero weight on workers ($\mu=0$) and cares only about aggregate profit.
It grows with $N$, approaching $\ell/k$ as $N\to\infty$, so fragmented markets suffer disproportionately.
The second term is a distributional premium: the additional automation reduction a planner who values worker income ($\mu>0$) would impose beyond the profit-maximizing benchmark.
It is independent of $N$ but grows without bound as $\mu\to 1$; at $\bar{\mu}\coloneqq\lambda k\,\alpha^{CO}/(\ell+\lambda k\,\alpha^{CO})$ the planner prohibits automation entirely.
The surplus loss in (ii) is quadratic in this total wedge and scales with $NL$, so both fragmentation and market size amplify the welfare cost.

Figure˜2 illustrates the Pareto dominance and the decomposition.
To make the losses for the two groups comparable, panels (a) and (b) normalize each payoff by its value at $\alpha^{CO}$, so a value of $1$ corresponds to the cooperative benchmark.
Panel (a) plots the normalized payoffs against the common automation rate $\bar{\alpha}$: both curves peak at or before $\alpha^{CO}$ and both fall below $1$ at $\alpha^{NE}$. The key observation is that the equilibrium rate lies to the right of the aggregate profit peak, so that both owner surplus and worker income are lower than under cooperation. Workers bear the larger loss because their income declines linearly in $\bar{\alpha}$, while the profit curve is concave and falls more gently.
Panel (b) re-expresses the same information as a factor payoff frontier: each point on the curve corresponds to a different common automation rate, tracing out the $(\mathcal{K},\mathcal{W})$ pairs as $\bar{\alpha}$ increases. The cooperative rate sits at $(1,1)$ and $\alpha^{NE}$ is strictly to the southwest, confirming that moving from equilibrium to the cooperative rate would make both groups better off.
Panel (c) visualizes the decomposition in (9): the horizontal line marks $\alpha^{NE}$, and the declining curve is the planner’s optimum $\alpha^{SP}(\mu)$. Even at $\mu=0$, the gap is positive (the demand-externality term alone), and the required correction grows further as the distributional premium widens with $\mu$.

Since the over-automation wedge is a structural externality that harms both factor classes, a natural question is whether policy can close it.

### Policy Instruments

Several instruments could in principle address the externality; the question is which ones operate on the right margin.
To answer it, we benchmark against the cooperative optimum $\alpha^{CO}$, which maximizes aggregate profit without directly weighting worker welfare.
This is deliberately the weakest case for intervention: Proposition˜2 shows that the demand externality alone reduces both firm profits and worker income, and that placing any positive weight on workers ($\mu>0$) only widens the wedge.
Adopting the efficiency benchmark therefore simplifies the exposition while providing the most conservative case for intervention.

Table˜1 previews the results: only the Pigouvian automation tax fully corrects the distortion; the remaining instruments cushion the losers or partially shrink the wedge, but none eliminates it.

One limitation should be noted: the analysis evaluates each instrument against a single margin, the demand externality identified in Section˜3, holding all other features of the economy fixed.
In practice, every instrument carries additional costs and benefits outside the model (administrative burden, labor-market distortions, political feasibility) that a full welfare analysis would need to weigh.
Nonetheless, an instrument that does not operate on the externality margin cannot correct the distortion regardless of how it scores on other dimensions; the analysis below separates instruments that can from those that cannot.

#### Displacement vs. Upskilling

The demand-loss parameter $\ell=\lambda(1-\eta)w$ governs the externality’s magnitude.
In the baseline model, $\eta\in[0,1]$ represents the fraction of displaced wage income recovered through reemployment, transfers, or other sources: higher $\eta$ shrinks $\ell$ and thereby the over-automation wedge.

But the parameter extends naturally beyond unity.
When $\eta>1$, upskilling and reabsorption place displaced workers into higher-paying roles, automation increases aggregate labor income, and loss $\ell$ turns negative, which we can interpret as a gain.
This is the scenario invoked by AI optimists, in which technological displacement is a stepping stone to better jobs.
As the following corollary shows, the sign reversal in $\ell$ flips the externality itself.

The logic is symmetric.
When $\eta<1$, displacement destroys demand, and each firm bears only $1/N$ of the loss, producing over-automation.
When $\eta>1$, displacement creates demand through higher reemployment wages, and each firm captures only $1/N$ of the gain, producing under-automation.
In both cases, the distortion grows with $N$: more competition dilutes each firm’s share of the externality, whether that externality is negative or positive.
A monopolist ($N=1$) fully internalizes in every case.

The competitive forces are identical; only the sign of the demand externality differs.
As Section˜4.6 will show, the same corrective instrument addresses both cases: a tax when $\eta<1$, a subsidy when $\eta>1$.

The case $\eta>1$ is not merely theoretical.
Historical technological transitions have often eventually reabsorbed displaced workers at higher wages (Acemoglu and Restrepo, 2019), and the current AI buildout offers a concrete channel: the expansion of data centers, energy infrastructure, and AI-adjacent services is creating skilled roles that can pay more than the positions automation displaces.
If this reabsorption is fast enough to push $\eta$ above unity, competitive firms will automate too slowly.
However, past displacement episodes have consistently produced $\eta<1$: displaced workers suffer large, persistent earnings losses (Jacobson et al., 1993), and there is little evidence yet that AI-driven displacement will differ, placing most economies firmly in the over-automation regime.

The policy implication is that raising $\eta$ through retraining programs, wage insurance, and incentives for new firm creation is not merely a palliative for displaced workers but a direct lever on the externality: every unit increase in $\eta$ toward unity shrinks $\ell$, narrows the over-automation wedge, and reduces the burden placed on the corrective instruments analyzed below.
Pushing $\eta$ past unity would flip the distortion into under-automation, but this is a far less pressing concern: in that regime, displaced workers are already thriving in higher-paying roles.

#### Universal Basic Income

Among the most discussed responses to automation-driven displacement is a universal basic income.
In the model, a UBI funded from general revenue maps to an increase in autonomous demand $A$: because the transfer is unconditional, employed and displaced workers receive the same payment, adding a constant to aggregate spending without altering the marginal income loss from displacement.
This distinguishes UBI from displacement-targeted transfers (wage insurance, severance), which raise the income-replacement rate $\eta$ and directly shrink $\ell$; see Section˜4.1.
The results below concern this modeled object and should not be read as a verdict on all UBI designs.

Because UBI adds a constant to demand, it enters firm profit only through $\Pi_{0}=A/N+(\lambda-1)wL$, the baseline profit when no firm automates.
This term drops out of the first-order condition $s-\ell/N-k\alpha_{i}=0$: a higher $A$ raises the profit floor but changes neither the cost saving $s$ nor the demand loss $\ell$ that determine the automation rate.
Consequently, UBI alters neither the automation threshold $N^{*}=\ell/s$ nor the over-automation wedge $\ell(1-1/N)/k$.
In the language of game theory, UBI changes payoff levels but not the payoff differences that drive strategic behavior.
More generally, instruments that operate on profit levels can redistribute income but cannot correct the externality; only instruments that change the per-task automation margin can.

Despite not correcting the externality, UBI serves a complementary role.
A higher $\Pi_{0}$ cushions profit losses from over-automation, while the transfer itself raises the floor on workers’ living standards, buying time for corrective instruments that operate on the right margin.

UBI may, however, carry an unintended side effect when the number of firms is endogenous. The baseline fixes $N$, but if firms can freely enter (Section˜5.2 formalizes this), higher profits attract new entrants, fragmenting the market. Because the over-automation wedge is increasing in $N$, UBI-induced entry can paradoxically widen the externality, partially offsetting the welfare gain from higher baseline consumption; Section˜5.2 develops the full argument.

Within the model, UBI is a complement to the automation tax, not a substitute: a society that relies solely on UBI will over-automate at the same rate, with a higher floor on living standards but the same externality.

#### Capital Income Taxation

If unconditional transfers do not alter the automation incentive, a natural alternative is to tax the proceeds of automation directly.
Consider a proportional tax $t\in(0,1)$ on capital income (profits), with revenue redistributed to workers.
Firm $i$ now maximizes $(1-t)\pi_{i}$, but because $(1-t)$ is a positive scalar it cancels from the first-order condition: the equilibrium automation rate, the threshold $N^{*}$, and the over-automation wedge are all unchanged.

The revenue side fares no better.
Lump-sum redistribution raises autonomous demand $A$, but $A$ enters per-firm profit only through the constant $\Pi_{0}=A/N+(\lambda-1)wL$, which does not appear in the first-order condition.
If revenue instead funds displacement insurance that raises $\eta$, the externality shrinks through $\ell$, but the operative channel is $\eta$, not the profit tax itself.

The distinction matters because capital income taxes are often conflated with robot taxes in the policy debate.
The robot taxes studied in the literature (e.g., Guerreiro et al., 2022) are per-unit levies on adoption, which operate on the per-task margin; a proportional capital income tax is a fundamentally different instrument that scales the entire profit function by $(1-t)$ and cancels from the optimality condition.
The failure is structurally identical to that of UBI (Section˜4.2): both instruments shift profit levels rather than operating on the margin where the externality resides.

#### Worker Equity Participation

A market-based alternative to taxation, rooted in the profit-sharing literature (Weitzman, 1985), gives workers a direct stake in the profits that automation generates.
Unlike UBI, which enters demand only through the level term $A$, profit-sharing flows through the profit function and therefore interacts with automation decisions.
Suppose each firm distributes a fraction $\epsilon\in[0,1]$ of its profits to workers (through ESOPs, equity grants, or co-determination mandates).
Workers spend a $\lambda$-fraction of this income in the sector, so profit-sharing recycles capital income back into demand.

Aggregate demand now satisfies a fixed-point condition: $D=A+\lambda[\text{wage income}+\epsilon\sum_{i}\pi_{i}]$, where $\sum_{i}\pi_{i}=D-\sum_{i}C_{i}$.
Because profits depend on $D$, demand is determined simultaneously with the automation decision; the proof solves this fixed point explicitly.

Part (i) is not immediate: profit-sharing changes the demand function by recycling capital income into worker spending, so one might expect it to shift the planner’s optimum.
The result follows because the planner already controls all $N$ firms and thus fully internalizes the demand externality.
In the planner’s first-order condition, the profit-sharing terms cancel: the modified demand-loss parameter $\ell_{\epsilon}=\ell-\lambda\epsilon s$ and the demand multiplier $1/(1-\lambda\epsilon)$ exactly offset, leaving $k\alpha=s-\ell$ regardless of $\epsilon$.

While the cooperative optimum is unaffected, the Nash equilibrium does shift. Intuitively, when workers hold equity, part of the demand lost through displacement is recycled back through profit shares; each firm therefore perceives a larger effective demand loss from its own automation than in the baseline, and restrains accordingly. The magnitude of this shift is governed by the compound parameter $N_{\epsilon}=N-\lambda\epsilon(N-1)$.
This parameter measures the effective demand-leakage divisor: at $\epsilon=0$ it equals $N$, recovering the baseline in which each firm perceives demand loss $\ell/N$ per automated task.
As $\epsilon$ rises, $N_{\epsilon}$ falls toward $1$, pushing $\alpha^{NE}$ toward the cooperative optimum.

Despite this improvement, the recycling cannot fully close the wedge whenever $\lambda<1$.
Closing the wedge requires the product $\lambda\epsilon$ to reach one, i.e., $\epsilon=1/\lambda$.
When $\lambda<1$ this exceeds the feasible range $\epsilon\in[0,1]$: each unit of profit recycled to workers generates only $\lambda$ units of sectoral demand, so compensating for the leakage would require sharing more than the firm’s entire profit.
Even at $\epsilon=1$ (full profit-sharing), the wedge reduces to $\ell(N-1)(1-\lambda)/[k(N-\lambda(N-1))]$, which remains strictly positive.
(The knife-edge case $\lambda=1$ is the exception: full profit-sharing does close the wedge, but only because this extreme assumption eliminates the very spending leakage that drives the externality.)

The structural limitation is that the externality is fundamentally multilateral: each firm’s automation depresses demand for all $N$ firms, and bilateral arrangements between a firm and its own workers cannot reach the demand that leaks to rivals.

A separate question is whether profit-sharing would arise voluntarily.

The marginal cost of sharing is $\pi_{i}$ (a dollar-for-dollar reduction in retained earnings), while the marginal demand benefit is only $\lambda\pi_{i}/N$: workers spend fraction $\lambda$ of the shared profit in the sector, and firm $i$ captures $1/N$ of the resulting demand increase.
Since $\lambda/N<1$ for any $N\geq 2$, the cost strictly exceeds the benefit.
This is a second-order coordination failure layered on top of the automation externality itself, mirroring the Prisoner’s Dilemma structure of Section˜3.2.

Profit-sharing must therefore be mandated to have any effect, and even then it cannot substitute for a corrective tax: it narrows the wedge but cannot eliminate it, and unlike a corrective tax (Section˜4.6), does not generate government revenue for retraining programs that would raise $\eta$.

#### Coasian Bargaining

None of the instruments considered so far fully closes the over-automation wedge, and worker equity will not arise voluntarily (Corollary˜3). A natural question is whether private ordering could succeed where these instruments have not. By the Coase Theorem (Coase, 1960), if property rights over the externality were well-defined and transaction costs sufficiently low, bargaining could achieve the cooperative optimum without government intervention.
A contemporary version of this argument envisions each worker equipped with an AI agent that bargains on her behalf, drawing on the property rights over training data proposed by Arrieta-Ibarra et al. (2018) and Posner and Weyl (2018).
To evaluate this possibility, it helps to separate two questions: can bargaining between a firm and its own workers correct the externality, and can bargaining among firms do so?
As we show below, neither can.

#### Pigouvian Automation Tax

The classic remedy for a negative externality is a Pigouvian tax: a per-unit charge set equal to the marginal external cost, so that every agent’s private incentive aligns with the social cost (Pigou, 1920).
In contrast to many textbook externalities, where the harmed parties are outside the firms’ market (e.g., pollution), here the harmed parties are workers whose income constitutes the firms’ own demand.
This means the tax rate, its revenue, and its incidence all interact through the same labor-market channel, creating richer policy design questions than the standard case.

The optimal rate has a transparent economic interpretation: each firm already bears $\ell/N$ of the demand loss from its own automation; the tax charges it for the remaining $\ell(1-1/N)$ imposed on rivals.
For large $N$, $\tau^{*}\approx\ell=\lambda(1-\eta)w$, so setting the rate requires only sector-level observables.
Levying the tax, however, requires observing firm-level automation rates, a practical challenge, though one that may be easing as AI adoption generates observable procurement records (Guerreiro et al., 2022).
Unlike rival firms in a Coasian bargaining setting (Section˜4.5), a tax authority can compel disclosure through mandatory reporting, payroll records, and procurement audits, making approximate measurement feasible even when private verification is not.
Because the welfare loss is quadratic in the wedge (Proposition˜2), even an imprecisely targeted tax yields a first-order gain.

### Extensions

The baseline isolates the demand externality in the simplest environment that supports it. A natural concern is that the result depends on what has been held fixed: endogenous wage adjustment might close the wedge, free entry might discipline the market to an efficient scale, higher AI productivity might resolve the demand problem by expanding the pie, and capital-income recycling might offset the spending lost through displacement. This section takes up each of these objections, along with richer product-market interaction, and shows that the externality is robust to all of them and, in some cases, amplified. Table˜2 previews the results.

#### AI Productivity

In the baseline, AI and human workers produce the same output per task and so the automation incentive is purely cost-driven. In practice, AI can replace humans while also raising output per task (e.g., autonomous agentic coding agents, higher-throughput customer service bots). To capture this, we add a productivity advantage on top of the cost saving. A natural conjecture is that this output channel mitigates the demand problem by making the economy more productive.
We show the opposite is true: higher AI output per task widens the over-automation wedge.

Let an AI-performed task produce $\phi\geq 1$ units of output, while a human-performed task produces $1$ unit.
With $\phi>1$, firm $i$’s output becomes

Under perfect competition, revenue is allocated by output share: $\operatorname{Rev}_{i}=D\cdot Y_{i}/\sum_{j}Y_{j}$.
At a symmetric profile all firms produce the same output $\bar{Y}=[1+(\phi-1)\alpha]L$, so $\operatorname{Rev}_{i}=D/N$ as in the baseline.
Differentiating with respect to $\alpha_{i}$ and evaluating at the symmetric profile yields

The first term is the baseline demand externality, which depends only on $\ell$ and $N$ and is therefore independent of $\phi$.
The second is new: a deviating firm raises its output above rivals and captures a larger share of expenditure.
This market-share gain is positive whenever $\phi>1$, raising the private incentive to automate above the baseline.

To quantify the effect, we combine cost saving, demand loss, and market-share gain into the first-order condition.
The symmetric equilibrium equates marginal integration cost to the combined benefit:

Because $D(\alpha)$ is linear in $\alpha$, clearing the denominator yields a quadratic whose positive root is the unique equilibrium; however, the resulting expression is less transparent than the baseline formula, so the comparative statics below are established via a monotone crossing argument.

The mechanism is a Red Queen effect: each firm perceives a market-share gain from automating beyond rivals, but at the symmetric equilibrium all firms expand equally, so the gains cancel.
By contrast, the cost saving $s$ enters each firm’s profit identically regardless of rivals’ choices, so it shifts $\alpha^{NE}$ and $\alpha^{CO}$ equally and leaves the wedge unchanged.

Part (ii) holds because total sectoral revenue equals total expenditure $D$ under market clearing, and $D$ (2) depends on worker income, not output: higher $\phi$ raises output but lowers the price in proportion, leaving the planner’s objective invariant to $\phi$.
Together with part (i), this yields part (iii): better AI raises the equilibrium automation rate without shifting the efficient benchmark, so the distortion grows with AI capability.

The wider wedge also carries a policy implication. Because the market-share motive adds a second distortion on top of the demand externality, the baseline Pigouvian rate $\tau^{*}=\ell(1-1/N)$ no longer suffices: implementing $\alpha^{CO}$ requires an additional correction equal to the market-share term in (10) evaluated at the cooperative rate, which is strictly positive whenever $\phi>1$.
That said, the lower price means each dollar of spending buys more physical output, so the welfare measure $S(\mu)$, built from nominal flows, understates the real consumption gains from higher $\phi$.
The proposition identifies a strategic distortion, not a claim that higher AI productivity reduces total welfare on net.

#### Endogenous Entry

So far the number of firms has been exogenous.
With free entry, one might expect the over-automation problem to be self-correcting: surplus erosion lowers profits, marginal firms exit, and the remaining industry settles at an efficient scale.
Whether this logic goes through, however, depends on how the entry margin interacts with the automation decision.

Consider a two-stage game: firms pay a fixed cost $\kappa\geq 0$ to enter, then simultaneously choose automation rates.
Given $N$ entrants, the stage-2 Nash equilibrium yields per-firm operating profit $\Pi^{*}(N)$.
A pure-strategy free-entry equilibrium is an integer $N\geq 1$ such that

incumbents weakly prefer to remain active, while an additional entrant would not recover the fixed cost.

Because the frictionless ($k=0$) and convex-cost ($k>0$) regimes shape the profit schedule in qualitatively different ways, we treat each in turn. The frictionless case sets $\lambda=1$ for clean closed forms; the qualitative results hold for any $\lambda\in(0,1]$, as the assumption affects only profit levels, not the structure of the entry regimes.

In the frictionless benchmark ($k=0$), automation is all-or-nothing.
When $\ell>s$, the profit schedule drops discretely at $N^{*}$: below the threshold no firm automates, while above it full automation is dominant (Corollary˜1) and per-firm profit falls by $\Delta\coloneqq L(\ell-s)>0$ (Figure˜4 in the appendix illustrates).
Write $m\coloneqq\lfloor N^{*}\rfloor$ for the largest integer not exceeding $N^{*}$.

When case (i) arises, the Prisoner’s Dilemma of Corollary˜1 materializes under free entry: all firms automate, demand contracts, and every firm would be better off had none automated.
Case (iii) is the standard free-entry outcome: entry costs are high enough that the market never approaches the automation threshold, and the externality is irrelevant.
Case (ii) is the most distinctive: the threat of automation functions as an endogenous entry barrier, sustaining positive profits without any automation actually occurring, at the cost of sustaining market power.

The convex-cost case is less stark but more robust.
With $k>0$, the automation rate $\alpha^{NE}(N)=(s-\ell/N)/k$ varies continuously in $N$, so the profit schedule no longer jumps at $N^{*}$ and the entry-deterrence mechanism of Proposition˜7(ii) does not arise.

Generically, $N^{FE}$ exceeds $N^{*}$ whenever zero-automation profits at the threshold, $\Pi_{0}(N^{*})$, exceed $\kappa$.33In a numerical grid over $c/w\in\{0.1,\dots,0.5\}$, $\lambda\in\{0.3,\dots,1\}$, $\eta\in\{0,\dots,0.3\}$, $k\in\{0.5,1,2\}$, and $\kappa\in\{0.1,\dots,5\}$, $N^{FE}$ exceeds $N^{*}$ in over 94% of parameterizations satisfying the proposition’s conditions; the exceptions arise only when the entry cost is high enough that the market barely supports more than $N^{*}$ firms.
Free entry then pins down the number of firms but does not alter the strategic incentives within the automation subgame: each firm still bears only a fraction $1/N^{FE}$ of the demand loss, and the over-automation wedge $\ell(1-1/N^{FE})/k$ persists.
If $N^{FE}\leq N^{*}$, no firm automates and the outcome is efficient, but only because the market is too concentrated for the private automation incentive to activate.

Taken together, the two propositions deliver a common lesson: free entry reshapes the over-automation problem but does not resolve it. If anything, the standard tendency toward excess entry (Mankiw and Whinston, 1986) widens the wedge by fragmenting the market further.

The entry margin also reveals an unintended side effect of UBI (Section˜4.2). By raising autonomous demand $A$, UBI increases per-firm profit $\Pi_{0}=A/N+(\lambda-1)wL$ at any given $N$, attracting additional entrants until the zero-profit condition (11) binds at a larger $N^{FE}$. Since the over-automation wedge $\ell(1-1/N)/k$ is increasing in $N$, a policy designed to cushion displacement can paradoxically widen the very externality that causes it.

#### Endogenous Wages

A central insight of Acemoglu and Restrepo (2018) is that endogenous wage adjustment can stabilize the automation path: as firms automate, displaced workers increase labor supply, pushing wages down; lower wages narrow the cost saving from automation and discourage further displacement.
This self-correcting feedback is a natural candidate for resolving the demand externality identified above.
We show that it raises the threshold at which the externality activates but cannot close the wedge once it does.

In Acemoglu and Restrepo (2018), wages are determined by labor-market clearing in a full general equilibrium; we adopt a reduced-form representation that captures the key qualitative feature of their mechanism.
Let the wage depend on the aggregate automation rate: $w(\bar{\alpha})$ with $w(\bar{\alpha})>c$ and $w^{\prime}(\bar{\alpha})\leq 0$; firms take the prevailing wage as given when choosing $\alpha_{i}$. This specification requires only that wages fall when aggregate labor-market slack increases, a property shared by efficiency-wage models, where the no-shirking wage declines with unemployment (Shapiro and Stiglitz, 1984), and by the empirical wage curve, where Blanchflower and Oswald (1995) document a robust negative relationship between wages and unemployment across more than a dozen countries. In our setting, automation displaces workers into the labor pool, generating exactly this type of slack.

Both the cost saving $s(w)=w-c$ and the demand-loss parameter $\ell(w)=\lambda(1-\eta)w$ are increasing in the wage, so falling wages affect both sides of the automation margin: they shrink the private incentive to automate (the self-correcting channel) and reduce the demand loss per automated task.
The equilibrium automation rate is therefore a fixed point in which automation, wages, and the externality are jointly determined.
Despite this richer feedback, the threshold $N^{*}=\ell/s=\lambda(1-\eta)w/(w-c)$ rises as wages fall, because the cost saving $s=w-c$ contracts faster than the demand loss $\ell=\lambda(1-\eta)w$.
The structural source of the distortion, however, is unaffected.

Competitive pricing allocates revenue as $\operatorname{Rev}_{i}=D/N$ at any wage level, so each firm bears only a fraction of the demand destruction its automation causes regardless of whether $w$ is high or low. Wage adjustment changes the magnitude of $\ell$ but not the fraction each firm internalizes; that fraction is a property of market structure, not of factor prices.

The strongest version of the self-correcting argument is that wages could fall far enough to shut the externality down entirely. As $w\to c$, the cost saving $s\to 0$ while $N^{*}\to\infty$: eventually $N^{*}$ exceeds $N$ and no firm finds automation privately worthwhile. But this is a Pyrrhic resolution. When wages are driven to near the AI cost, workers who retain their jobs earn little more than the machines that would replace them, and aggregate purchasing power collapses through wage depression rather than displacement. The externality vanishes not because the demand problem has been solved but because there is so little income left per worker that the wedge between private and social incentives becomes negligible: a labor market that “self-corrects” only by impoverishing its workforce has transmuted displacement into depressed living standards. More generally, wage flexibility changes when the externality bites, not whether it exists.

The analysis above sets $\mu=0$, so the planner cares only about firm profits. A planner who also values worker welfare ($\mu>0$) would find wage depression no more acceptable than displacement, demanding a larger correction, yet wage adjustment provides the same compression of $\ell$. Endogenous wages therefore close a smaller share of the gap, making them even less adequate as a corrective mechanism. Corollary˜4 in the appendix confirms this: the over-automation result extends to any $\mu\in[0,1)$ under endogenous wages.

#### Capital Income Recycling

Section˜4.1 showed that raising $\eta$, the fraction of displaced income recovered by workers, shrinks the demand-loss parameter $\ell$ and narrows the over-automation wedge. A natural counterpart on the capital side is that owners spend their profits: if their consumption offsets the spending lost through displacement, the demand externality might disappear. We show that recycling narrows the wedge but cannot close it under empirically plausible parameters.

Suppose capital owners consume a fraction $\hat{\eta}\in[0,1)$ of their capital income in the sector.
Total sector profit is $\Pi=D-NL(w-s\bar{\alpha})$.
Adding capital consumption $\hat{\eta}\Pi$ to aggregate demand and solving for $D$ yields

is the effective demand-loss parameter: each automated task loses $\ell$ in worker spending, but owners recycle $\hat{\eta}$ of the per-task saving $s$ back into demand.
When $\hat{\eta}=0$, $\ell_{\hat{\eta}}=\ell$ and eq.˜12 reduces to eq.˜2.

Competitive pricing still gives $\operatorname{Rev}_{i}=D/N$.
The first-order condition becomes $L(s-\ell_{\hat{\eta}}/[N(1-\hat{\eta})])$, giving a modified threshold

Part (ii) requires $\hat{\eta}\geq\ell/s=\lambda(1-\eta)w/(w-c)$: owners must recycle enough of each task’s cost saving to replace the demand that displaced workers would have generated. When $\ell>s$, the required rate exceeds one, so recycling is impotent precisely where the externality is most harmful, since $\ell>s$ implies $\alpha^{CO}=0$ and firms automate when the planner would prefer none. When $\ell<s$, elimination is feasible in principle, but the planner already prefers positive automation (Proposition˜1) and the wedge is quantitatively smaller.

The frictionless case gives the sharpest result, but the structure carries over when frictions are positive. The proof of Proposition˜10 extends the result to $k>0$. The Nash equilibrium generalizes to $\alpha^{NE}=(s-\ell/\hat{N})/k$, where $\hat{N}=N(1-\hat{\eta})+\hat{\eta}$ is an effective market size that interpolates between $N$ (no recycling) and $1$ (full recycling), making each firm behave as though it faced fewer competitors. The cooperative optimum, however, is unchanged: the $1/(1-\hat{\eta})$ multiplier scales total profit without shifting the optimizer.

The upshot parallels Section˜4.1: recycling raises the fraction of demand loss each firm internalizes from $1/N$ to $1/\hat{N}$, but cannot push it to one. Addressing how income is spent narrows the wedge but does not close it, because the underlying dilution across firms persists.

#### Imperfect Product-Market Competition and Task Complementarity

The baseline assumes competitive pricing and perfect substitution across tasks.
Without providing a formal treatment, we argue that richer product-market interaction and task complementarity would complicate the analysis but should not eliminate the demand externality.

### Discussion

This paper develops a simple model with a simple but stark insight. Even as AI-driven layoffs sweep across industries, and even as every firm recognizes that vanishing paychecks mean vanishing customers, not one of them will stop. Each firm reaps the full savings of replacing its own workers yet bears only a sliver of the demand it destroys; the rest lands on rivals. No firm can afford to be the one that holds back. This is the trap: an automation arms race that only intensifies as AI improves, that leaves workers and firm owners alike worse off, and that no market force can break. We close by discussing implications for empirics and policy, and then the scope and limitations of the analysis.
