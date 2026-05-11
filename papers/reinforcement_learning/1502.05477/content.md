# Trust Region Policy Optimization

**Authors:** John Schulman, Sergey Levine, Philipp Moritz, Michael Jordan, Pieter Abbeel, John Schulman, Sergey Levine, Philipp Moritz, Michael I. Jordan, Pieter Abbeel

## Abstract

We describe an iterative procedure for optimizing policies, with guaranteed monotonic improvement. By making several approximations to the theoretically-justified procedure, we develop a practical algorithm, called Trust Region Policy Optimization (TRPO). This algorithm is similar to natural policy gradient methods and is effective for optimizing large nonlinear policies such as neural networks. Our experiments demonstrate its robust performance on a wide variety of tasks: learning simulated robotic swimming, hopping, and walking gaits; and playing Atari games using images of the screen as input. Despite its approximations that deviate from the theory, TRPO tends to give monotonic improvement, with little tuning of hyperparameters.

### Introduction

Most algorithms for policy optimization can be classified into three broad categories:
(1) policy iteration methods, which alternate between estimating the value function under the current policy and improving the policy (Bertsekas, 2005); (2) policy gradient methods, which use an estimator of the gradient of the expected return (total reward) obtained from sample trajectories (Peters & Schaal, 2008a) (and which, as we later discuss, have a close connection to policy iteration); and (3) derivative-free optimization methods, such as the cross-entropy method (CEM) and covariance matrix adaptation (CMA), which treat the return as a black box function to be optimized in terms of the policy parameters (Szita & Lörincz, 2006).

General derivative-free stochastic optimization methods such as CEM and CMA are preferred on many problems, because they achieve good results while being simple to understand and implement.
For example, while Tetris is a classic benchmark problem for approximate dynamic programming (ADP) methods, stochastic optimization methods are difficult to beat on this task (Gabillon et al., 2013).
For continuous control problems, methods like CMA have been successful at learning control policies for challenging tasks like locomotion when provided with hand-engineered policy classes with low-dimensional parameterizations (Wampler & Popović, 2009).
The inability of ADP and gradient-based methods to consistently beat gradient-free random search is unsatisfying, since gradient-based optimization algorithms enjoy much better sample complexity guarantees than gradient-free methods (Nemirovski, 2005).
Continuous gradient-based optimization has been very successful at learning function approximators for supervised learning tasks with huge numbers of parameters, and extending their success to reinforcement learning would allow for efficient training of complex and powerful policies.

In this article, we first prove that minimizing a certain surrogate objective function guarantees policy improvement with non-trivial step sizes.
Then we make a series of approximations to the theoretically-justified algorithm, yielding a practical algorithm, which we call trust region policy optimization (TRPO).
We describe two variants of this algorithm: first, the single-path method, which can be applied in the model-free setting; second, the vine method, which requires the system to be restored to particular states, which is typically only possible in simulation.
These algorithms are scalable and can optimize nonlinear policies with tens of thousands of parameters, which have previously posed a major challenge for model-free policy search (Deisenroth et al., 2013).
In our experiments, we show that the same TRPO methods can learn complex policies for swimming, hopping, and walking, as well as playing Atari games directly from raw images.

### Preliminaries

Consider an infinite-horizon discounted Markov decision process (MDP), defined by the tuple $(\mathcal{S},\mathcal{A},P,r,\rho_{0},\gamma)$,
where $\mathcal{S}$ is a finite set of states, $\mathcal{A}$ is a finite set of actions, $P:\mathcal{S}\times\mathcal{A}\times\mathcal{S}\rightarrow\mathbb{R}$ is the transition probability distribution, $r:\mathcal{S}\rightarrow\mathbb{R}$ is the reward function, $\rho_{0}:\mathcal{S}\rightarrow\mathbb{R}$ is the distribution of the initial state $s_{0}$, and $\gamma\in(0,1)$ is the discount factor.

Let $\pi$ denote a stochastic policy $\pi:\mathcal{S}\times\mathcal{A}\rightarrow[0,1]$, and let $\eta(\pi)$ denote its expected discounted reward:

We will use the following standard definitions of the state-action value function $Q_{\pi}$, the value function $V_{\pi}$, and the advantage function $A_{\pi}$:

The following useful identity expresses the expected return of another policy $\tilde{\pi}$ in terms of the advantage over $\pi$, accumulated over timesteps (see Kakade & Langford (2002) or Appendix A for proof):

where the notation $\mathbb{E}_{s_{0},a_{0},\dots\sim\tilde{\pi}}\left[\dots\right]$ indicates that actions are sampled $a_{t}\sim\tilde{\pi}(\cdot|s_{t})$.
Let $\rho_{\pi}$ be the (unnormalized) discounted visitation frequencies

where $s_{0}\sim\rho_{0}$ and the actions are chosen according to $\pi$.
We can rewrite Equation 1 with a sum over states instead of timesteps:

This equation implies that any policy update $\pi\rightarrow\tilde{\pi}$ that has a nonnegative expected advantage at every state $s$, i.e., $\sum_{a}\tilde{\pi}(a|s)A_{\pi}(s,a)\geq 0$, is guaranteed to increase the policy performance $\eta$, or leave it constant in the case that the expected advantage is zero everywhere.
This implies the classic result that the update performed by exact policy iteration, which uses the deterministic policy $\tilde{\pi}(s)=\operatorname*{arg\,max}_{a}A_{\pi}(s,a)$, improves the policy if there is at least one state-action pair with a positive advantage value and nonzero state visitation probability, otherwise the algorithm has converged to the optimal policy.
However, in the approximate setting, it will typically be unavoidable, due to estimation and approximation error,
that there will be some states $s$ for which the expected advantage is negative, that is, $\sum_{a}\tilde{\pi}(a|s)A_{\pi}(s,a)<0$.
The complex dependency of $\rho_{\tilde{\pi}}(s)$ on $\tilde{\pi}$ makes Equation (2) difficult to optimize directly. Instead, we introduce the following local approximation to $\eta$:

Note that $L_{\pi}$ uses the visitation frequency $\rho_{\pi}$ rather than $\rho_{\tilde{\pi}}$, ignoring changes in state visitation density due to changes in the policy.
However, if we have a parameterized policy $\pi_{\theta}$, where $\pi_{\theta}(a|s)$ is a differentiable function of the parameter vector $\theta$, then $L_{\pi}$ matches $\eta$ to first order (see Kakade & Langford (2002)).
That is, for any parameter value $\theta_{0}$,

Equation 4 implies that a sufficiently small step $\pi_{\theta_{0}}\rightarrow\tilde{\pi}$ that improves $L_{\pi_{\theta_{\mathrm{old}}}}$ will also improve $\eta$, but does not give us any guidance on how big of a step to take.

To address this issue, Kakade & Langford (2002) proposed a policy updating scheme called conservative policy iteration, for which they could provide explicit lower bounds on the improvement of $\eta$.
To define the conservative policy iteration update, let $\pi_{\mathrm{old}}$ denote the current policy, and let $\pi^{\prime}=\operatorname*{arg\,max}_{\pi^{\prime}}L_{\pi_{\mathrm{old}}}(\pi^{\prime})$.
The new policy $\pi_{\mathrm{new}}$ was defined to be the following mixture:

Kakade and Langford derived the following lower bound:

(We have modified it to make it slightly weaker but simpler.)
Note, however, that so far this bound only applies to mixture policies generated by Equation (5). This policy class is unwieldy and restrictive in practice, and it is desirable for a practical policy update scheme to be applicable to all general stochastic policy classes.

### Monotonic Improvement Guarantee for General Stochastic Policies

Equation 6, which applies to conservative policy iteration, implies that a policy update that improves the right-hand side is guaranteed to improve the true performance $\eta$.
Our principal theoretical result is that the policy improvement bound in Equation 6 can be extended to general stochastic policies, rather than just mixture polices, by replacing $\alpha$ with a distance measure between $\pi$ and $\tilde{\pi}$, and changing the constant $\epsilon$ appropriately. Since mixture policies are rarely used in practice, this result is crucial for extending the improvement guarantee to practical problems. The particular distance measure we use is the total variation divergence, which is defined by
$D_{TV}(p\ \|\ q)=\frac{1}{2}\sum_{i}|p_{i}-q_{i}|$ for discrete probability distributions $p,q$.11Our result is straightforward to extend to continuous states and actions by replacing the sums with integrals.
Define $D^{\rm max}_{\rm TV}(\pi,\tilde{\pi})$ as

We provide two proofs in the appendix.
The first proof extends Kakade and Langford’s result
using the fact that the random variables from two distributions with total variation divergence less than $\alpha$ can be coupled, so that they are equal with probability $1-\alpha$.
The second proof uses perturbation theory.

Next, we note the following relationship between the total variation divergence and the KL divergence (Pollard (2000), Ch.
3):
$D_{TV}(p\ \|\ q)^{2}\leq D_{\rm KL}(p\ \|\ q)$.
Let ${D^{\rm max}_{\rm KL}}(\pi,\tilde{\pi})=\max_{s}D_{\rm KL}(\pi(\cdot|s)\ \|\ \tilde{\pi}(\cdot|s))$. The following bound then follows directly from 1:

Algorithm 1 describes an approximate policy iteration scheme based on the policy improvement bound in Equation (9). Note that for now, we assume exact evaluation of the advantage values $A_{\pi}$.

It follows from Equation 9 that Algorithm 1 is guaranteed to generate a monotonically improving sequence of policies
$\eta(\pi_{0})\leq\eta(\pi_{1})\leq\eta(\pi_{2})\leq\dots$.
To see this, let $M_{i}(\pi)=L_{\pi_{i}}(\pi)-C{D^{\rm max}_{\rm KL}}(\pi_{i},\pi)$. Then

Thus, by maximizing $M_{i}$ at each iteration, we guarantee that the true objective $\eta$ is non-decreasing.
This algorithm is a type of minorization-maximization (MM) algorithm (Hunter & Lange, 2004), which is a class of methods that also includes expectation maximization.
In the terminology of MM algorithms, $M_{i}$ is the surrogate function that minorizes $\eta$ with equality at $\pi_{i}$.
This algorithm is also reminiscent of proximal gradient methods and mirror descent.

Trust region policy optimization, which we propose in the following section, is an approximation to Algorithm 1, which uses a constraint on the KL divergence rather than a penalty to robustly allow large updates.

### Optimization of Parameterized Policies

In the previous section, we considered the policy optimization problem independently of the parameterization of $\pi$ and under the assumption that the policy can be evaluated at all states. We now describe how to derive a practical algorithm from these theoretical foundations, under finite sample counts and arbitrary parameterizations.

Since we consider parameterized policies $\pi_{\theta}(a|s)$ with parameter vector $\theta$,
we will overload our previous notation to use functions of $\theta$ rather than $\pi$,
e.g. $\eta(\theta)\vcentcolon=\eta(\pi_{\theta})$, $L_{\theta}(\tilde{\theta})\vcentcolon=L_{\pi_{\theta}}(\pi_{\tilde{\theta}})$, and $D_{\rm KL}(\theta\ \|\ \tilde{\theta})\vcentcolon=D_{\rm KL}(\pi_{\theta}\ \|\ \pi_{\tilde{\theta}})$.
We will use $\theta_{\mathrm{old}}$ to denote the previous policy parameters that we want to improve upon.

The preceding section showed that $\eta(\theta)\geq L_{\theta_{\mathrm{old}}}(\theta)-C{D^{\rm max}_{\rm KL}}(\theta_{\mathrm{old}},\theta)$, with equality at $\theta=\theta_{\mathrm{old}}$.
Thus, by performing the following maximization, we are guaranteed to improve the true objective $\eta$:

In practice, if we used the penalty coefficient $C$ recommended by the theory above, the step sizes would be very small.
One way to take larger steps in a robust way is to use a constraint on the KL divergence between the new policy and the old policy, i.e., a trust region constraint:

This problem imposes a constraint that the KL divergence is bounded at every point in the state space.
While it is motivated by the theory, this problem is impractical to solve due to the large number of constraints.
Instead, we can use a heuristic approximation which considers the average KL divergence:

We therefore propose solving the following optimization problem to generate a policy update:

Similar policy updates have been proposed in prior work (Bagnell & Schneider, 2003; Peters & Schaal, 2008b; Peters et al., 2010), and we compare our approach to prior methods in Section 7 and in the experiments in Section 8. Our experiments also show that this type of constrained update has similar empirical performance to the maximum KL divergence constraint in Equation (11).

### Sample-Based Estimation of the Objective and Constraint

The previous section proposed a constrained optimization problem on the policy parameters (Equation (12)),
which optimizes an estimate of the expected total reward $\eta$ subject to a constraint on the change in the policy at each update.
This section describes how the objective and constraint functions can be approximated using Monte Carlo simulation.

We seek to solve the following optimization problem, obtained by expanding
$L_{\theta_{\mathrm{old}}}$ in Equation (12):

We first replace $\sum_{s}\rho_{\theta_{\mathrm{old}}}(s)\left[\dots\right]$ in the objective by the expectation $\frac{1}{1-\gamma}\mathbb{E}_{s\sim\rho_{\theta_{\mathrm{old}}}}\left[\dots\right]$.
Next, we replace the advantage values $A_{\theta_{\mathrm{old}}}$ by the $Q$-values $Q_{\theta_{\mathrm{old}}}$ in Equation (13), which only changes the objective by a constant.
Last, we replace the sum over the actions by an importance sampling estimator. Using $q$ to denote the sampling distribution, the contribution of a single $s_{n}$ to the loss function is

Our optimization problem in Equation 13 is exactly equivalent to the following one, written in terms of expectations:

All that remains is to replace the expectations by sample averages and replace the $Q$ value by an empirical estimate.
The following sections describe two different schemes for performing this estimation.

The first sampling scheme, which we call single path, is the one that is typically used for policy gradient estimation (Bartlett & Baxter, 2011), and is based on sampling individual trajectories.
The second scheme, which we call vine, involves constructing a rollout set and then performing multiple actions from each state in the rollout set.
This method has mostly been explored in the context of policy iteration methods (Lagoudakis & Parr, 2003; Gabillon et al., 2013).

#### Single Path

In this estimation procedure, we collect a sequence of states by sampling $s_{0}\sim\rho_{0}$ and then simulating the policy $\pi_{\theta_{\mathrm{old}}}$ for some number of timesteps to generate a trajectory $s_{0},a_{0},s_{1},a_{1},\dots,s_{T-1},a_{T-1},s_{T}$.
Hence, $q(a|s)=\pi_{\theta_{\mathrm{old}}}(a|s)$.
$Q_{\theta_{\mathrm{old}}}(s,a)$ is computed at each state-action pair $(s_{t},a_{t})$ by taking the discounted sum of future rewards along the trajectory.

#### Vine

In this estimation procedure, we first sample $s_{0}\sim\rho_{0}$ and simulate the policy $\pi_{\theta_{i}}$ to generate a number of trajectories.
We then choose a subset of $N$ states along these trajectories, denoted $s_{1},s_{2},\dots,s_{N}$, which we call the “rollout set”.
For each state $s_{n}$ in the rollout set, we sample $K$ actions according to $a_{n,k}\sim q(\cdot|s_{n})$. Any choice of $q(\cdot|s_{n})$ with a support that includes the support of $\pi_{\theta_{i}}(\cdot|s_{n})$ will produce a consistent estimator. In practice, we found that $q(\cdot|s_{n})=\pi_{\theta_{i}}(\cdot|s_{n})$ works well on continuous problems, such as robotic locomotion, while the uniform distribution works well on discrete tasks, such as the Atari games, where it can sometimes achieve better exploration.

For each action $a_{n,k}$ sampled at each state $s_{n}$, we estimate $\hat{Q}_{\theta_{i}}(s_{n},a_{n,k})$ by performing a rollout (i.e., a short trajectory) starting with state $s_{n}$ and action $a_{n,k}$.
We can greatly reduce the variance of the $Q$-value differences between rollouts by using the same random number sequence for the noise in each of the $K$ rollouts, i.e., common random numbers.
See (Bertsekas, 2005) for additional discussion on Monte Carlo estimation of $Q$-values and (Ng & Jordan, 2000) for a discussion of common random numbers in reinforcement learning.

In small, finite action spaces, we can generate a rollout for every possible action from a given state.
The contribution to $L_{\theta_{\mathrm{old}}}$ from a single state $s_{n}$ is as follows:

where the action space is $\mathcal{A}=\left\{a_{1},a_{2},\dots,a_{K}\right\}$.
In large or continuous state spaces, we can construct an estimator of the surrogate objective using importance sampling.
The self-normalized estimator (Owen (2013), Chapter 9) of $L_{\theta_{\mathrm{old}}}$ obtained at a single state $s_{n}$ is

assuming that we performed $K$ actions $a_{n,1},a_{n,2},\dots,a_{n,K}$ from state $s_{n}$.
This self-normalized estimator removes the need to use a baseline for the $Q$-values (note that the gradient is unchanged by adding a constant to the $Q$-values).
Averaging over $s_{n}\sim\rho(\pi)$, we obtain an estimator for $L_{\theta_{\mathrm{old}}}$, as well as its gradient.

The vine and single path methods are illustrated in Figure 1.
We use the term vine, since the trajectories used for sampling can be likened to the stems of vines, which branch at various points (the rollout set) into several short offshoots (the rollout trajectories).

The benefit of the vine method over the single path method that is our local estimate of the objective has much lower variance given the same number of $Q$-value samples in the surrogate objective.
That is, the vine method gives much better estimates of the advantage values.
The downside of the vine method is that we must perform far more calls to the simulator for each of these advantage estimates.
Furthermore, the vine method requires us to generate multiple trajectories from each state in the rollout set, which limits this algorithm to settings where the system can be reset to an arbitrary state. In contrast, the single path algorithm requires no state resets and can be directly implemented on a physical system (Peters & Schaal, 2008b).

### Practical Algorithm

Here we present two practical policy optimization algorithm based on the ideas above, which use either the single path or vine sampling scheme from the preceding section.
The algorithms repeatedly perform the following steps:

Use the single path or vine procedures to collect a set of state-action pairs along with Monte Carlo estimates of their $Q$-values.

By averaging over samples, construct the estimated objective and constraint in Equation 14.

Approximately solve this constrained optimization problem to update the policy’s parameter vector $\theta$.
We use the conjugate gradient algorithm followed by a line search, which is altogether only slightly more expensive than computing the gradient itself. See Appendix C for details.

With regard to (3), we construct the Fisher information matrix (FIM) by analytically computing the Hessian of the KL divergence, rather than using the covariance matrix of the gradients.
That is, we estimate $A_{ij}$ as $\frac{1}{N}\sum_{n=1}^{N}\frac{\partial^{2}}{\partial\theta_{i}\partial\theta_{j}}D_{\rm KL}(\pi_{\theta_{\mathrm{old}}}(\cdot|s_{n})\ \|\ \pi_{\theta}(\cdot|s_{n}))$, rather than $\frac{1}{N}\sum_{n=1}^{N}\frac{\partial}{\partial\theta_{i}}\log\pi_{\theta}(a_{n}|s_{n})\frac{\partial}{\partial\theta_{j}}\log\pi_{\theta}(a_{n}|s_{n})$.
The analytic estimator integrates over the action at each state $s_{n}$, and does not depend on the action $a_{n}$ that was sampled.
As described in Appendix C, this analytic estimator has computational benefits in the large-scale setting, since it removes the need to store a dense Hessian or all policy gradients from a batch of trajectories. The rate of improvement in the policy is similar to the empirical FIM, as shown in the experiments.

Let us briefly summarize the relationship between the theory from Section 3 and the practical algorithm we have described:

The theory justifies optimizing a surrogate objective with a penalty on KL divergence. However, the large penalty coefficient $C$ leads to prohibitively small steps, so we would like to decrease this coefficient.
Empirically, it is hard to robustly choose the penalty coefficient, so we use a hard constraint instead of a penalty, with parameter $\delta$ (the bound on KL divergence).

The constraint on ${D^{\rm max}_{\rm KL}}(\theta_{\mathrm{old}},\theta)$ is hard for numerical optimization and estimation, so instead we constrain ${\overline{D}_{\rm KL}}(\theta_{\mathrm{old}},\theta)$.

Our theory ignores estimation error for the advantage function.
Kakade & Langford (2002) consider this error in their derivation, and the same arguments would hold in the setting of this paper, but we omit them for simplicity.

### Connections with Prior Work

As mentioned in Section 4, our derivation results in a policy update that is related to several prior methods, providing a unifying perspective on a number of policy update schemes. The natural policy gradient (Kakade, 2002) can be obtained as a special case of the update in Equation (12) by using a linear approximation to $L$ and a quadratic approximation to the ${\overline{D}_{\rm KL}}$ constraint, resulting in the following problem:

The update is $\theta_{\mathrm{new}}=\theta_{\mathrm{old}}+\frac{1}{\lambda}A(\theta_{\mathrm{old}})^{-1}\nabla_{\theta}L(\theta)\big{\rvert}_{\theta=\theta_{\mathrm{old}}}$, where the stepsize $\frac{1}{\lambda}$ is typically treated as an algorithm parameter. This differs from our approach, which enforces the constraint at each update. Though this difference might seem subtle, our experiments demonstrate that it significantly improves the algorithm’s performance on larger problems.

We can also obtain the standard policy gradient update by using an $\ell_{2}$ constraint or penalty:

The policy iteration update can also be obtained by solving the unconstrained problem $\operatorname*{maximize}_{\pi}L_{\pi_{\mathrm{old}}}(\pi)$, using $L$ as defined in Equation 3.

Several other methods employ an update similar to Equation (12). Relative entropy policy search (REPS) (Peters et al., 2010) constrains the state-action marginals $p(s,a)$, while TRPO constrains the conditionals $p(a|s)$. Unlike REPS, our approach does not require a costly nonlinear optimization in the inner loop.
Levine and Abbeel (2014) also use a KL divergence constraint, but its purpose is to encourage the policy not to stray from regions where the estimated dynamics model is valid, while we do not attempt to estimate the system dynamics explicitly.
Pirotta et al. (2013) also build on and generalize Kakade and Langford’s results, and they derive different algorithms from the ones here.

### Experiments

We designed our experiments to investigate the following questions:

What are the performance characteristics of the single path and vine sampling procedures?

TRPO is related to prior methods (e.g. natural policy gradient) but makes several changes, most notably by using a fixed KL divergence rather than a fixed penalty coefficient. How does this affect the performance of the algorithm?

Can TRPO be used to solve challenging large-scale problems? How does TRPO compare with other methods when applied to large-scale problems, with regard to final performance, computation time, and sample complexity?

To answer (1) and (2), we compare the performance of the single path and vine variants of TRPO, several ablated variants, and a number of prior policy optimization algorithms.
With regard to (3), we show that both the single path and vine algorithm can obtain high-quality locomotion controllers from scratch, which is considered to be a hard problem.
We also show that these algorithms produce competitive results when learning policies for playing Atari games from images using convolutional neural networks with tens of thousands of parameters.

#### Simulated Robotic Locomotion

We conducted the robotic locomotion experiments using the MuJoCo simulator (Todorov et al., 2012).
The three simulated robots are shown in Figure 2.
The states of the robots are their generalized positions and velocities, and the controls are joint torques. Underactuation, high dimensionality, and non-smooth dynamics due to contacts make these tasks very challenging.
The following models are included in our evaluation:

Swimmer. $10$-dimensional state space, linear reward for forward progress and a quadratic penalty on joint effort to produce the reward $r(x,u)=v_{x}-10^{-5}\|u\|^{2}$. The swimmer can propel itself forward by making an undulating motion.

Hopper. $12$-dimensional state space, same reward as the swimmer, with a bonus of $+1$ for being in a non-terminal state.
We ended the episodes when the hopper fell over, which was defined by thresholds on the torso height and angle.

Walker. $18$-dimensional state space. For the walker, we added a penalty for strong impacts of the feet against the ground to encourage a smooth walk rather than a hopping gait.

We used $\delta=0.01$ for all experiments.
See Table 2 in the Appendix for more details on the experimental setup and parameters used.
We used neural networks to represent the policy, with the architecture shown in Figure 3, and further details provided in Appendix D. To establish a standard baseline, we also included the classic cart-pole balancing problem, based on the formulation from Barto et al. (1983), using a linear policy with six parameters that is easy to optimize with derivative-free black-box optimization methods.

The following algorithms were considered in the comparison:
single path TRPO;
vine TRPO;
cross-entropy method (CEM), a gradient-free method (Szita & Lörincz, 2006);
covariance matrix adaption (CMA), another gradient-free method (Hansen & Ostermeier, 1996);
natural gradient, the classic natural policy gradient algorithm (Kakade, 2002), which differs from single path by the use of a fixed penalty coefficient (Lagrange multiplier) instead of the KL divergence constraint;
empirical FIM, identical to single path, except that the FIM is estimated using the covariance matrix of the gradients rather than the analytic estimate;
max KL, which was only tractable on the cart-pole problem, and uses the maximum KL divergence in Equation (11), rather than the average divergence, allowing us to evaluate the quality of this approximation.
The parameters used in the experiments are provided in Appendix E.
For the natural gradient method, we swept through the possible values of the stepsize in factors of three, and took the best value according to the final performance.

Learning curves showing the total reward averaged across five runs of each algorithm are shown in Figure 4.
Single path and vine TRPO solved all of the problems, yielding the best solutions.
Natural gradient performed well on the two easier problems, but was unable to generate hopping and walking gaits that made forward progress.
These results provide empirical evidence that constraining the KL divergence is a more robust way to choose step sizes and make fast, consistent progress, compared to using a fixed penalty.
CEM and CMA are derivative-free algorithms, hence their sample complexity scales unfavorably with the number of parameters, and they performed poorly on the larger problems.
The max KL method learned somewhat more slowly than our final method, due to the more restrictive form of the constraint, but overall the result suggests that the average KL divergence constraint has a similar effect as the theorecally justified maximum KL divergence. Videos of the policies learned by TRPO may be viewed on the project website: http://sites.google.com/site/trpopaper/.

Note that TRPO learned all of the gaits with general-purpose policies and simple reward functions, using minimal prior knowledge. This is in contrast with most prior methods for learning locomotion, which typically rely on hand-architected policy classes that explicitly encode notions of balance and stepping (Tedrake et al., 2004; Geng et al., 2006; Wampler & Popović, 2009).

#### Playing Games from Images

To evaluate TRPO on a partially observed task with complex observations, we trained policies for playing Atari games, using raw images as input. The games require learning a variety of behaviors, such as dodging bullets and hitting balls with paddles.
Aside from the high dimensionality, challenging elements of these games include delayed rewards (no immediate penalty is incurred when a life is lost in Breakout or Space Invaders); complex sequences of behavior (Q*bert requires a character to hop on $21$ different platforms); and non-stationary image statistics (Enduro involves a changing and flickering background).

We tested our algorithms on the same seven games reported on in (Mnih et al., 2013) and (Guo et al., 2014), which are made available through the Arcade Learning Environment (Bellemare et al., 2013)
The images were preprocessed following the protocol in Mnih et al (2013), and
the policy was represented by the convolutional neural network shown in Figure 3, with two convolutional layers with $16$ channels and stride $2$, followed by one fully-connected layer with $20$ units, yielding 33,500 parameters.

The results of the vine and single path algorithms are summarized in Table 1, which also includes an expert human performance and two recent methods: deep $Q$-learning (Mnih et al., 2013), and a combination of Monte-Carlo Tree Search with supervised training (Guo et al., 2014), called UCC-I. The 500 iterations of our algorithm took about 30 hours (with slight variation between games) on a 16-core computer. While our method only outperformed the prior methods on some of the games, it consistently achieved reasonable scores. Unlike the prior methods, our approach was not designed specifically for this task. The ability to apply the same policy search method to methods as diverse as robotic locomotion and image-based game playing demonstrates the generality of TRPO.

### Discussion

We proposed and analyzed trust region methods for optimizing stochastic control policies.
We proved monotonic improvement for an algorithm that repeatedly optimizes a local approximation to the expected return of the policy with a KL divergence penalty, and we showed that an approximation to this method that incorporates a KL divergence constraint achieves good empirical results on a range of challenging policy learning tasks, outperforming prior methods. Our analysis also provides a perspective that unifies policy gradient and policy iteration methods, and shows them to be special limiting cases of an algorithm that optimizes a certain objective subject to a trust region constraint.

In the domain of robotic locomotion, we successfully learned controllers for swimming, walking and hopping in a physics simulator, using general purpose neural networks and minimally informative rewards.
To our knowledge, no prior work has learned controllers from scratch for all of these tasks, using a generic policy search method and non-engineered, general-purpose policy representations.
In the game-playing domain, we learned convolutional neural network policies that used raw images as inputs. This requires optimizing extremely high-dimensional policies, and only two prior methods report successful results on this task.

Since the method we proposed is scalable and has strong theoretical foundations, we hope that it will serve as a jumping-off point for future work on training large, rich function approximators for a range of challenging problems.
At the intersection of the two experimental domains we explored, there is the possibility of learning robotic control policies that use vision and raw sensory data as input, providing a unified scheme for training robotic controllers that perform both perception and control.
The use of more sophisticated policies, including recurrent policies with hidden state, could further make it possible to roll state estimation and control into the same policy in the partially-observed setting.
By combining our method with model learning, it would also be possible to substantially reduce its sample complexity, making it applicable to real-world settings where samples are expensive.
