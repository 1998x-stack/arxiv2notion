# Mastering Chess and Shogi by Self-Play with a General Reinforcement Learning Algorithm

**Authors:** David Silver,1∗ Thomas Hubert,1∗ Julian Schrittwieser,1∗ Ioannis Antonoglou,1 Matthew Lai,1 Arthur Guez,1 Marc Lanctot,1 Laurent Sifre,1 Dharshan Kumaran,1 Thore Graepel,1 Timothy Lillicrap,1 Karen Simonyan,1 Demis Hassabis1 1DeepMind, 6 Pancras Square, London N1C 4AG. ∗These authors contributed equally to this work

## Abstract

The game of chess is the most widely-studied domain in the history of artificial intelligence. The strongest programs are based on a combination of sophisticated search techniques, domain-specific adaptations, and handcrafted evaluation functions that have been refined by human experts over several decades. In contrast, the AlphaGo Zero program recently achieved superhuman performance in the game of Go, by tabula rasa reinforcement learning from games of self-play. In this paper, we generalise this approach into a single AlphaZero algorithm that can achieve, tabula rasa, superhuman performance in many challenging domains. Starting from random play, and given no domain knowledge except the game rules, AlphaZero achieved within 24 hours a superhuman level of play in the games of chess and shogi (Japanese chess) as well as Go, and convincingly defeated a world-champion program in each case.

### Methods

#### Anatomy of a Computer Chess Program

In this section we describe the components of a typical computer chess program, focusing specifically onStockfish(?), an open source program that won the 2016 TCEC computer chess championship.
For an overview of standard methods, see  (?).

Each position$s$is described by a sparse vector of
handcrafted features$\phi(s)$, including midgame/endgame-specific material point values, material imbalance tables, piece-square tables, mobility and trapped pieces, pawn structure, king safety, outposts, bishop pair, and other miscellaneous evaluation patterns.
Each feature$\phi_{i}$is assigned, by a combination of manual and automatic tuning, a corresponding weight$w_{i}$and the position is evaluated by a linear combination$v(s,w)=\phi(s)^{\top}w$. However, this raw evaluation is only considered accurate for positions that are “quiet”, with no unresolved captures or checks. A domain-specialisedquiescence searchis used to resolve ongoing tactical situations before the evaluation function is applied.

The final evaluation of a position$s$is computed by a minimax search that evaluates each leaf using a quiescence search. Alpha-beta pruning is used to safely cut any branch that is provably dominated by another variation. Additional cuts are achieved using aspiration windows and principal variation search.
Other pruning strategies include null move pruning (which assumes a pass move should be worse than any variation, in positions that are unlikely to be inzugzwang, as determined by simple heuristics), futility pruning (which assumes knowledge of the maximum possible change in evaluation), and other domain-dependent pruning rules (which assume knowledge of the value of captured pieces).

The search is focused on promising variations both by extending the search depth of promising variations, and by reducing the search depth of unpromising variations based on heuristics like history, static-exchange evaluation (SEE), and moving piece type. Extensions are based on domain-independent rules that identify singular moves with no sensible alternative, and domain-dependent rules, such as extending check moves. Reductions, such as late move reductions, are based heavily on domain knowledge.

The efficiency of alpha-beta search depends critically upon the order in which moves are considered. Moves are therefore ordered by iterative deepening (using a shallower search to order moves for a deeper search). In addition, a combination of domain-independent move ordering heuristics, such as killer heuristic, history heuristic, counter-move heuristic, and also domain-dependent knowledge based on captures (SEE) and potential captures (MVV/LVA).

A transposition table facilitates the reuse of values and move orders when the same position is reached by multiple paths. A carefully tuned opening book is used to select moves at the start of the game. An endgame tablebase, precalculated by exhaustive retrograde analysis of endgame positions, provides the optimal move in all positions with six and sometimes seven pieces or less.

Other strong chess programs, and also earlier programs such as Deep Blue, have used very similar architectures  (?, ?) including the majority of the components described above, although important details vary considerably.

None of the techniques described in this section are used byAlphaZero. It is likely that some of these techniques could further improve the performance ofAlphaZero; however, we have focused on a pure self-play reinforcement learning approach and leave these extensions for future research.

#### Prior Work on Computer Chess and Shogi

In this section we discuss some notable prior work on reinforcement learning in computer chess.

NeuroChess(?) evaluated positions by a neural network that used 175 handcrafted input features. It was trained by temporal-difference learning to predict the final game outcome, and also the expected features after two moves.NeuroChesswon 13% of games againstGnuChessusing a fixed depth 2 search.

Beal and Smith applied temporal-difference learning to estimate the piece values in chess  (?) and shogi  (?), starting from random values and learning solely by self-play.

KnightCap(?) evaluated positions by a neural network that used an attack-table based on knowledge of which squares are attacked or defended by which pieces. It was trained by a variant of temporal-difference learning, known as TD(leaf), that updates the leaf value of the principal variation of an alpha-beta search.KnightCapachieved human master level after training against a strong computer opponent with hand-initialised piece-value weights.

Meep(?) evaluated positions by a linear evaluation function based on handcrafted features. It was trained by another variant of temporal-difference learning, known as TreeStrap, that updated all nodes of an alpha-beta search.Meepdefeated human international master players in 13 out of 15 games, after training by self-play with randomly initialised weights.

Kaneko and Hoki  (?) trained the weights of a shogi evaluation function comprising a million features, by learning to select expert human moves during alpha-beta serach. They also performed a large-scale optimization based on minimax search regulated by expert game logs  (?); this formed part of theBonanzaengine that won the 2013 World Computer Shogi Championship.

Giraffe(?) evaluated positions by a neural network that included mobility maps and attack and defend maps describing the lowest valued attacker and defender of each square. It was trained by self-play using TD(leaf), also reaching a standard of play comparable to international masters.

DeepChess(?) trained a neural network to performed pair-wise evaluations of positions. It was trained by supervised learning from a database of human expert games that was pre-filtered to avoid capture moves and drawn games.DeepChessreached a strong grandmaster level of play.

All of these programs combined their learned evaluation functions with an alpha-beta search enhanced by a variety of extensions.

An approach based on training dual policy and value networks usingAlphaZero-like policy iteration was successfully applied to improve on the state-of-the-art in Hex  (?).

#### MCTS and Alpha-Beta Search

For at least four decades the strongest computer chess programs have used alpha-beta search  (?, ?).AlphaZerouses a markedly different approach that averages over the position evaluations within a subtree, rather than computing the minimax evaluation of that subtree. However, chess programs using traditional MCTS were much weaker than alpha-beta search programs,  (?, ?); while alpha-beta programs based on neural networks have previously been unable to compete with faster, handcrafted evaluation functions.

AlphaZeroevaluates positions using non-linear function approximation based on a deep neural network, rather than the linear function approximation used in typical chess programs. This provides a much more powerful representation, but may also introduce spurious approximation errors. MCTS averages over these approximation errors, which therefore tend to cancel out when evaluating a large subtree. In contrast, alpha-beta search computes an explicit minimax, which propagates the biggest approximation errors to the root of the subtree. Using MCTS may allowAlphaZeroto effectively combine its neural network representations with a powerful, domain-independent search.

#### Domain Knowledge

The input features describing the position, and the output features describing the move, are structured as a set of planes; i.e. the neural network architecture is matched to the grid-structure of the board.

AlphaZerois provided with perfect knowledge of the game rules. These are used during MCTS, to simulate the positions resulting from a sequence of moves, to determine game termination, and to score any simulations that reach a terminal state.

Knowledge of the rules is also used to encode the input planes (i.e. castling, repetition, no-progress) and output planes (how pieces move, promotions, and piece drops in shogi).

The typical number of legal moves is used to scale the exploration noise (see below).

Chess and shogi games exceeding a maximum number of steps (determined by typical game length) were terminated and assigned a drawn outcome; Go games were terminated and scored with Tromp-Taylor rules, similarly to previous work  (?).

AlphaZerodid not use any form of domain knowledge beyond the points listed above.

#### Representation

In this section we describe the representation of the board inputs, and the representation of the action outputs, used by the neural network inAlphaZero. Other representations could have been used; in our experiments the training algorithm worked robustly for many reasonable choices.

The input to the neural network is an$N\times N\times(MT+L)$image stack that represents state using a concatenation of$T$sets of$M$planes of size$N\times N$. Each set of planes represents the board position at a time-step$t-T+1,...,t$, and is set to zero for time-steps less than 1. The board is oriented to the perspective of the current player. The$M$feature planes are composed of binary feature planes indicating the presence of the player’s pieces, with one plane for each piece type, and a second set of planes indicating the presence of the opponent’s pieces. For shogi there are additional planes indicating the number of captured prisoners of each type. There are an additional$L$constant-valued input planes denoting the player’s colour, the total move count, and the state of special rules: the legality of castling in chess (kingside or queenside); the repetition count for that position (3 repetitions is an automatic draw in chess; 4 in shogi); and the number of moves without progress in chess (50 moves without progress is an automatic draw). Input features are summarised in TableS1.

A move in chess may be described in two parts: selecting the piece to move, and then selecting among the legal moves for that piece. We represent the policy$\pi(a|s)$by a$8\times 8\times 73$stack of planes encoding a probability distribution over 4,672 possible moves. Each of the$8\times 8$positions identifies the square from which to “pick up” a piece. The first 56 planes encode possible ‘queen moves’ for any piece: a number of squares$[1..7]$in which the piece will be moved, along one of eight relative compass directions$\{N,NE,E,SE,S,SW,W,NW\}$. The next 8 planes encode possible knight moves for that piece. The final 9 planes encode possible underpromotions for pawn moves or captures in two possible diagonals, to knight, bishop or rook respectively. Other pawn moves or captures from the seventh rank are promoted to a queen.

The policy in shogi is represented by a$9\times 9\times 139$stack of planes similarly encoding a probability distribution over 11,259 possible moves. The first 64 planes encode ‘queen moves’ and the next 2 moves encode knight moves. An additional$64+2$planes encode promoting queen moves and promoting knight moves respectively. The last 7 planes encode a captured piece dropped back into the board at that location.

The policy in Go is represented identically toAlphaGo Zero(?), using a flat distribution over$19\times 19+1$moves representing possible stone placements and the pass move.
We also tried using a flat distribution over moves for chess and shogi; the final result was almost identical although training was slightly slower.

The action representations are summarised in TableS2. Illegal moves are masked out by setting their probabilities to zero, and re-normalising the probabilities for remaining moves.

#### Configuration

During training, each MCTS used 800 simulations. The number of games, positions, and thinking time varied per game due largely to different board sizes and game lengths, and are shown in TableS3. The learning rate was set to 0.2 for each game, and was dropped three times (to 0.02, 0.002 and 0.0002 respectively) during the course of training. Moves are selected in proportion to the root visit count. Dirichlet noise$\text{Dir}(\alpha)$was added to the prior probabilities in the root node; this was scaled in inverse proportion to the approximate number of legal moves in a typical position, to a value of$\alpha=\{0.3,0.15,0.03\}$for chess, shogi and Go respectively. Unless otherwise specified, the training and search algorithm and parameters are identical toAlphaGo Zero(?).

During evaluation,AlphaZeroselects moves greedily with respect to the root visit count. Each MCTS was executed on a single machine with 4 TPUs.

#### Evaluation

To evaluate performance in chess, we usedStockfishversion 8 (official Linux release) as a baseline program, using 64 CPU threads and a hash size of 1GB.

To evaluate performance in shogi, we usedElmoversion WCSC27 in combination with YaneuraOu 2017 Early KPPT 4.73 64AVX2 with 64 CPU threads and a hash size of 1GB with the usi option of EnteringKingRule set to NoEnteringKing.

We evaluated the relative strength ofAlphaZero(Figure1) by measuring the Elo rating of each player. We estimate the probability that player$a$will defeat player$b$by a logistic function$p(a\text{ defeats }b)=\frac{1}{1+\exp{(c_{\mathrm{elo}}(e(b)-e(a))}}$, and estimate the ratings$e(\cdot)$by Bayesian logistic regression, computed by theBayesEloprogram  (?) using the standard constant$c_{\mathrm{elo}}=1/400$.
Elo ratings were computed from the results of a 1 second per move tournament between iterations ofAlphaZeroduring training, and also a baseline player: eitherStockfish,ElmoorAlphaGo Leerespectively. The Elo rating of the baseline players was anchored to publicly available values  (?).

We also measured the head-to-head performance ofAlphaZeroagainst each baseline player. Settings were chosen to correspond with computer chess tournament conditions: each player was allowed 1 minute per move, resignation was enabled for all players (-900 centipawns for 10 consecutive moves forStockfishandElmo, 5% winrate forAlphaZero). Pondering was disabled for all players.

#### Example games

In this section we include 10 example games played byAlphaZeroagainstStockfishduring the 100 game match using 1 minute per move.
