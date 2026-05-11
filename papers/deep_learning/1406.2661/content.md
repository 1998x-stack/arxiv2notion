# Generative Adversarial Nets

**Authors:** Ian J. Goodfellow, Jean Pouget-Abadie, Mehdi Mirza, Bing Xu, David Warde-Farley, Sherjil Ozair, Aaron Courville, Yoshua Bengio Département d’informatique et de recherche opérationnelle Université de Montréal Montréal, QC H3C 3J7

## Abstract

We propose a new framework for estimating generative models via an adversarial process, in which we simultaneously train two models: a generative model GGG that captures the data distribution, and a discriminative model DDD that estimates the probability that a sample came from the training data rather than GGG. The training procedure for GGG is to maximize the probability of DDD making a mistake. This framework corresponds to a minimax two-player game. In the space of arbitrary functions GGG and DDD, a unique solution exists, with GGG recovering the training data distribution and DDD equal to 1212\frac{1}{2} everywhere. In the case where GGG and DDD are defined by multilayer perceptrons, the entire system can be trained with backpropagation. There is no need for any Markov chains or unrolled approximate inference networks during either training or generation of samples. Experiments demonstrate the potential of the framework through qualitative and quantitative evaluation of the generated samples.

### Introduction

The promise of deep learning is to discover rich, hierarchical models [2] that represent
probability distributions over the kinds of data encountered in artificial intelligence applications,
such as natural images, audio waveforms containing speech, and symbols in natural language corpora.
So far, the most striking successes in deep learning have involved discriminative models,
usually those that map a high-dimensional, rich sensory input to a class
label [14, 22]. These
striking successes have primarily been based on the backpropagation and dropout algorithms, using
piecewise linear units
 [19, 9, 10] which have a particularly well-behaved gradient
. Deep generative models have had less of an impact, due to the difficulty of approximating
many intractable probabilistic computations that arise in maximum likelihood estimation and
related strategies, and due to difficulty of leveraging the benefits of piecewise linear units in
the generative context. We propose a new generative model estimation procedure that sidesteps these difficulties.
11All code and hyperparameters available at http://www.github.com/goodfeli/adversarial

In the proposed adversarial nets framework, the generative model is pitted against an
adversary: a discriminative model that learns to determine whether a sample is
from the model distribution or the data distribution. The generative model can be thought of
as analogous to a team of counterfeiters, trying to produce fake currency and use it without
detection, while the discriminative model is analogous to the police, trying to detect the
counterfeit currency. Competition in this game drives both teams to improve their methods until the counterfeits
are indistiguishable from the genuine articles.

This framework can yield specific training algorithms for many kinds of model and optimization
algorithm. In this article, we explore the special case when the generative model generates
samples by passing random noise through a multilayer perceptron, and the discriminative model
is also a multilayer perceptron. We refer to this special case as adversarial nets.
In this case, we can train both models using only
the highly successful backpropagation and dropout algorithms [17]
and sample from the generative
model using only forward propagation. No approximate inference or Markov chains are necessary.

### Related work

An alternative to directed graphical models with latent variables are undirected graphical models
with latent variables, such as restricted Boltzmann machines (RBMs) [27, 16],
deep Boltzmann machines (DBMs) [26] and their numerous variants.
The interactions within such models are represented as the product of
unnormalized potential functions, normalized by a global
summation/integration over all states of the random variables.
This quantity (the partition function) and
its gradient are intractable for all but the most trivial
instances, although they can be estimated by Markov chain Monte
Carlo (MCMC) methods. Mixing poses a significant problem for learning
algorithms that rely on
MCMC [3, 5].

Deep belief networks (DBNs) [16] are hybrid models containing a single undirected layer and several directed layers.
While a fast approximate layer-wise training criterion exists, DBNs incur the computational
difficulties associated with both undirected and directed models.

Alternative criteria that do not approximate or bound
the log-likelihood have also been proposed, such as score matching [18]
and noise-contrastive estimation (NCE) [13].
Both of these require the learned probability density to be analytically specified
up to a normalization constant. Note that in many interesting generative models with several
layers of latent variables (such as
DBNs and DBMs), it is not even possible to derive a tractable unnormalized probability density.
Some models such as denoising auto-encoders [30] and contractive
autoencoders have learning rules very similar to score matching applied to RBMs.
In NCE, as in this work, a discriminative training criterion is
employed to fit a generative model. However, rather than fitting a separate discriminative
model, the generative model itself is used to discriminate generated data from samples
a fixed noise distribution. Because NCE uses a fixed noise distribution, learning slows
dramatically after the model has learned even an approximately correct distribution over
a small subset of the observed variables.

Finally, some techniques do not involve defining a probability distribution explicitly,
but rather train a generative machine to draw samples from the desired distribution.
This approach has the advantage that such machines can be designed to be trained by
back-propagation. Prominent recent work in this area includes the generative stochastic network
(GSN) framework [5], which extends generalized denoising
auto-encoders [4]: both can be seen as defining a
parameterized Markov chain, i.e., one learns the parameters of a machine that
performs one step of a generative Markov chain.
Compared to GSNs, the adversarial nets framework does not require a Markov chain for
sampling. Because adversarial nets do not require feedback loops during generation,
they are better able to leverage piecewise linear
units [19, 9, 10],
which improve the performance of backpropagation but have problems with unbounded activation when used ina feedback loop.
More recent examples of training a generative machine by back-propagating into it
include recent work on auto-encoding variational Bayes [20]
and stochastic backpropagation [24].

### Adversarial nets

The adversarial modeling framework is most straightforward to apply when the models are both
multilayer perceptrons. To learn the generator’s distribution $p_{g}$ over data $\bm{x}$, we
define a prior on input noise variables $p_{\bm{z}}(\bm{z})$, then represent a
mapping to data space as $G(\bm{z};\theta_{g})$, where $G$ is a differentiable function
represented by a multilayer perceptron with parameters $\theta_{g}$. We also define a second
multilayer perceptron $D(\bm{x};\theta_{d})$ that outputs a single scalar. $D(\bm{x})$ represents
the probability that $\bm{x}$ came from the data rather than $p_{g}$. We train $D$ to maximize the
probability of assigning the correct label to both training examples and samples from $G$.
We simultaneously train $G$ to minimize $\log(1-D(G(\bm{z})))$:

In other words, $D$ and $G$ play the following two-player minimax game with value function $V(G,D)$:

In the next section, we present a theoretical analysis of adversarial nets,
essentially showing that the training criterion allows one to recover the data
generating distribution as $G$ and $D$ are given enough capacity, i.e., in the
non-parametric limit. See Figure 1 for a less formal, more pedagogical
explanation of the approach.
In practice, we must implement the game using an iterative, numerical approach. Optimizing $D$ to completion in the
inner loop of training is computationally prohibitive,
and on finite datasets would result in overfitting. Instead, we alternate between $k$ steps
of optimizing $D$ and one step of optimizing $G$. This results in $D$ being maintained
near its optimal solution, so long as $G$ changes slowly enough. This strategy is analogous
to the way that SML/PCD [31, 29] training maintains samples from a Markov chain from one
learning step to the next in order to avoid burning in a Markov chain as part of the inner loop
of learning. The procedure is formally presented
in Algorithm 1.

In practice, equation 1 may not provide sufficient gradient for $G$ to learn
well. Early in learning, when $G$ is poor, $D$ can reject samples with high confidence because they are
clearly different from the training data. In this case, $\log(1-D(G(\bm{z})))$ saturates. Rather than
training $G$ to minimize $\log(1-D(G(\bm{z})))$ we can train $G$ to maximize $\log D(G(\bm{z}))$.
This objective function results in the same fixed point of the dynamics of $G$ and $D$ but provides much
stronger gradients early in learning.

### Theoretical Results

The generator $G$ implicitly defines a probability distribution $p_{g}$ as
the distribution of the samples $G(\bm{z})$ obtained when $\bm{z}\sim p_{\bm{z}}$. Therefore, we would like Algorithm 1 to converge to a
good estimator of $p_{\text{data}}$, if given enough capacity and training time. The
results of this section are done in a non-parametric setting, e.g. we represent a
model with infinite capacity by studying convergence in the space of probability
density functions.

We will show in section 4.1 that this minimax game
has a global optimum for $p_{g}=p_{\text{data}}$. We will then show in
section 4.2 that Algorithm 1
optimizes Eq 1, thus obtaining the desired
result.

#### Global Optimality of pg=pdatasubscriptpgsubscriptpdatap_{g}=p_{\text{data}}

We first consider the optimal discriminator $D$ for any given generator $G$.

Note that the training objective for $D$ can be interpreted as maximizing the log-likelihood for estimating the conditional probability $P(Y=y|\bm{x})$, where $Y$ indicates whether $\bm{x}$ comes from $p_{\text{data}}$ (with $y=1$) or from $p_{g}$ (with $y=0$). The minimax game in Eq. 1 can now be reformulated as:

#### Convergence of Algorithm 1

In practice, adversarial nets represent a limited family of $p_{g}$ distributions via the function $G(\bm{z};\theta_{g})$,
and we optimize $\theta_{g}$ rather than $p_{g}$ itself. Using a multilayer perceptron to define $G$ introduces multiple
critical points in parameter space.
However, the excellent performance of multilayer
perceptrons in practice suggests that they are a reasonable model to use despite their lack of theoretical guarantees.

### Experiments

We trained adversarial nets an a range of datasets including MNIST[23], the
Toronto Face Database (TFD) [28], and CIFAR-10 [21].
The generator nets used a mixture of rectifier linear
activations [19, 9] and sigmoid
activations, while the discriminator net used maxout [10] activations.
Dropout [17] was applied in training the
discriminator net. While our theoretical framework permits the use of dropout and other noise
at intermediate layers of the generator, we used noise as the input to only the bottommost layer
of the generator network.

We estimate probability of the test set data under $p_{g}$ by fitting a Gaussian Parzen window to the samples
generated with $G$ and reporting the log-likelihood under this distribution.
The $\sigma$ parameter of the Gaussians
was obtained by cross validation on the validation set. This procedure was introduced in Breuleux et al. [8]
and used for various generative models for which the exact likelihood is
not
tractable [25, 3, 5]. Results
are reported in Table 1. This method of estimating the likelihood has somewhat high variance
and does not perform well in high dimensional spaces but it is the best method available to our knowledge.
Advances in generative models that can sample but not estimate likelihood directly motivate further research
into how to evaluate such models.

In Figures 2 and 3 we
show samples drawn from the generator net after training.
While we make no claim that these samples are better than
samples generated by existing methods, we believe that these samples are at
least competitive with the better generative models in the literature and
highlight the potential of the adversarial framework.

### Advantages and disadvantages

This new framework comes with advantages and disadvantages relative to previous
modeling frameworks. The disadvantages are primarily that there is no explicit
representation of $p_{g}(\bm{x})$, and that $D$ must be synchronized well with $G$
during training (in particular, $G$ must not be trained too much without updating
$D$, in order to avoid “the Helvetica scenario” in which $G$ collapses too many
values of $\mathbf{z}$ to the same value of $\mathbf{x}$ to have enough diversity
to model $p_{\text{data}}$),
much as the negative chains of a Boltzmann machine must be
kept up to date between learning steps. The advantages are that Markov chains
are never needed, only backprop is used to obtain gradients,
no inference is needed during learning, and a wide variety of
functions can be incorporated into the model.
Table 2 summarizes the comparison of generative adversarial nets with other
generative modeling approaches.

The aforementioned advantages are primarily computational. Adversarial models may
also gain some statistical advantage from the generator network not being updated
directly with data examples, but only with gradients flowing through the discriminator.
This means that components of the input are not copied directly into the generator’s
parameters. Another advantage of adversarial networks is that they can represent
very sharp, even degenerate distributions, while methods based on Markov chains require
that the distribution be somewhat blurry in order for the chains to be able to mix
between modes.

### Conclusions and future work

This framework
admits many straightforward extensions:

A conditional generative model $p(\bm{x}\mid\bm{c})$ can be obtained by adding $\bm{c}$
as input to both $G$ and $D$.

Learned approximate inference can be performed by training an auxiliary network to predict
$\bm{z}$ given $\bm{x}$. This is similar to the inference net trained by the wake-sleep algorithm  [15]
but with the advantage that the inference net may be trained for a fixed generator net after the generator
net has finished training.

One can approximately model all conditionals $p(\bm{x}_{S}\mid\bm{x}_{\not S})$ where $S$ is a subset of
the indices of $\bm{x}$
by training a family of conditional models that share parameters. Essentially, one can use adversarial nets to implement
a stochastic extension of the deterministic MP-DBM [11].

Semi-supervised learning: features from the discriminator or inference net could improve performance
of classifiers when limited labeled data is available.

Efficiency improvements: training could be accelerated greatly by divising better methods for
coordinating $G$ and $D$ or determining better distributions to sample $\mathbf{z}$ from during training.

This paper has demonstrated the viability of the adversarial modeling framework, suggesting that these research
directions could prove useful.

##### Acknowledgments

We would like to acknowledge Patrice Marcotte, Olivier Delalleau, Kyunghyun Cho, Guillaume Alain and Jason Yosinski for helpful discussions.
Yann Dauphin shared his Parzen window evaluation code with us.
We would like to thank the developers of
Pylearn2 [12]
and
Theano [7, 1], particularly
Frédéric Bastien who rushed a Theano feature specifically to benefit this project.
Arnaud Bergeron provided much-needed support with LaTeX typesetting.
We would also like to thank CIFAR, and Canada Research Chairs for funding, and Compute Canada, and Calcul Québec
for providing computational resources. Ian Goodfellow is supported by the 2013 Google Fellowship in Deep
Learning. Finally, we would like to thank Les Trois Brasseurs for stimulating our creativity.
