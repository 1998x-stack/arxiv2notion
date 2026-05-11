# Agentless \scalerel*C: Demystifying LLM-based Software Engineering Agents

**Authors:** Chunqiu Steven Xia∗* Yinlin Deng Soren Dunn Lingming Zhang University of Illinois Urbana-Champaign \scalerel *C {chunqiu2, yinlind2, sorend2, lingming}@illinois.edu

## Abstract

Recent advancements in large language models (LLMs) have significantly advanced the automation of software development tasks, including code synthesis, program repair, and test generation. More recently, researchers and industry practitioners have developed various autonomous LLM agents to perform end-to-end software development tasks. These agents are equipped with the ability to use tools, run commands, observe feedback from the environment, and plan for future actions. However, the complexity of these agent-based approaches, together with the limited abilities of current LLMs, raises the following question: Do we really have to employ complex autonomous software agents? To attempt to answer this question, we build Agentless – an agentless approach to automatically solve software development problems. Compared to the verbose and complex setup of agent-based approaches, Agentless employs a simplistic two-phase process of localization followed by repair, without letting the LLM decide future actions or operate with complex tools. Our results on the popular SWE-bench Lite benchmark show that surprisingly the simplistic Agentless is able to achieve both the highest performance (27.33%) and lowest cost ($0.34) compared with all existing open-source software agents! Furthermore, we manually classified the problems in SWE-bench Lite and found problems with exact ground truth patch or insufficient/misleading issue descriptions. As such, we construct SWE-bench Lite-SSS by excluding such problematic issues to perform more rigorous evaluation and comparison. Our work highlights the current overlooked potential of a simple, interpretable technique in autonomous software development. We hope Agentless will help reset the baseline, starting point, and horizon for autonomous software agents, and inspire future work along this crucial direction. We have open-sourced Agentless at: https://github.com/OpenAutoCoder/Agentless

### Introduction

Large language models (LLMs) have become the go-to default choice for code generation [18; 14; 34; 54].
State-of-the-art LLMs like GPT-4 [44] and Claude-3.5 [13] have demonstrated their prowess in being able to synthesize code snippets based on given user description.
However, compared to the main evaluation setting of simple, self-contained problems, applying LLMs on repository-level software engineering tasks has been understudied.
Software engineering tasks like feature addition, program repair, and test generation require an in-depth understanding of not only information within files, which can contain thousands of lines of code, but also repository-level dependencies across files.

Recently, to address the gap and evaluate the ability of tools to automatically solve real-world software engineering problems, the popular SWE-bench [28] benchmark has been developed.
In SWE-bench, each problem consists of a real-world GitHub issue description and the corresponding Python repository.
The task is to modify the repository to resolve the issue, either fixing a bug or introducing a new feature.
Recently, the authors have published a subset of the benchmark – SWE-bench Lite [11] (300 problems) that performs further filtering and focuses on bug fixing issues.

To solve the challenging real-world software development problems from SWE-bench, inspired by the Devin AI Software Engineer [4], there has been a significant body of work from both academia and industry focusing on developing agent-based approaches [65; 21; 61; 17; 41; 15].
While there is not a fixed definition for agent-based approaches, they generally equip LLMs with a set of tools and allow agents to iteratively and autonomously perform actions, observe feedback, and plan future steps.
Example tools can include the ability to open/write/create files, search for code lines, run tests, and execute shell commands.
In each attempt to solve a problem, agent-based approaches will have multiple turns, where each turn consists of performing an action.
Subsequent turns depend on previous actions and the feedback information the agent receives from the environment.

At first glance, agent-based approaches appear to be a natural and straightforward way to tackle software development tasks.
After all, human developers also perform similar actions and use feedback to plan future steps.
However, the disparity between human and current LLM abilities leads to the following limitations of agent-based approaches:

Complex tool usage/design.
To utilize tools, current agent-based approaches apply an abstraction layer between the agent and the environment.
Examples are mapping real actions to API calls so that agents can use tools by outputting an API call instruction.
However, such abstractions and API call specifications require careful design of input/output formats and can easily lead to incorrect or imprecise tool design/usage,
especially for more complex action spaces.
Given the iterative nature of agent-based approaches, where current action/plan depends on previous turns, incorrectly or imprecisely defining/using a tool can both reduce performance and incur additional cost in wasted LLM queries.

Lack of control in decision planning.
In addition to using tools, current agent-based approaches also delegates the decision making process to the agents – deciding when and what action to perform.
The agents decide the current action to take based on previous actions taken and the feedback provided by the environment, often with minimal checks to ensure the action taken make sense.
Due to the large possible action space and feedback response, it can be extremely easy for autonomous agents to become confused and perform sub-optimal explorations.
Furthermore, to solve an issue, an agent can take upwards of 30 or 40 turns which makes it extremely difficult to both understand the decisions made by the agents and also debug the exact turns where the incorrect decision is made.

Limited ability to self-reflect.
Existing agents struggle with the capability to perform self-reflection [43; 24].
That is to say they tend to take all information/feedback and do not know how to filter out or correct irrelevant, incorrect, or misleading information [53; 64].
For example, a common step in the agent-based approach is to reproduce an issue with a minimal test case. However, the reproduced test case may not be always correct or precise.
The limited ability to self-reflect means that an incorrect step can be easily amplified and negatively affect all future decisions taken by the agent.

In this paper, we advocate that instead of rushing to develop increasingly complex LLM agent-based approaches and tools for software development (which can also be non-trivial to use or replicate due to the fully autonomous setup), we should first take a step back and ask the following introspective question: Do we really have to employ complex autonomous software agents?

Our work. We set out to answer this important question by building Agentless – an agentless approach to automatically solve software development problems.
To solve each issue, Agentless follows a simple two phase process: localization and repair.
In the localization process, Agentless employs a hierarchical process to first localize the fault to specific files, then to relevant classes or functions, and finally to fine-grained edit locations.
To perform repair, Agentless takes the edit locations and generates multiple candidate patches in a simple diff format.
Agentless then performs simple filtering to remove any patches that have syntax errors or cannot pass the previous tests in the repository.
Finally, Agentless re-ranks all remaining patches and selects one to submit in order to fix the issue.
While Agentless leverages LLMs to perform each detailed task, unlike prior complex agent-based tools, Agentless does not allow LLMs to autonomously decide future actions or operate with any complex tools.
Our deliberate choice of not using agents not only allows Agentless to have a simplistic and straightforward design that can be easily understood, but also helps avoid the above mentioned limitations of LLM agents in software development.
We evaluate Agentless on the popular SWE-bench Lite [11] benchmark and demonstrate that Agentless not only achieves the highest performance (27.33%) among all open-source approaches, but it does so at a fraction of the cost!

Furthermore, we performed fine-grained manual analysis on the SWE-bench Lite dataset and classified all its problems into different categories across dimensions like problem description, ground truth patch, and location information.
Surprisingly, we observed that SWE-bench Lite contains problems (4.3%) with exact ground truth patch in the description, problems (9.3%) with missing critical information needed to solve the issue, and problems (4.3%) that include misleading solutions in the issue description.
Recognizing these issues, we built SWE-bench Lite-$S$,
which removes such problematic problems, and serves as a more rigorous benchmark to evaluate the ability to solve real-world software development problems.
Overall, in an era focused on achieving top placements on leaderboards, our work highlights the overlooked potential of a simplistic, interpretable technique in autonomous software development.
We hope Agentless will help reset the baseline, starting point, and horizon for autonomous software agents, and inspire future work along this crucial direction.

### Agentless \scalerel*C Approach

Figure 1 shows the overview of Agentless, consisting of two phases: localization and repair.
We first take in the issue description and the existing project codebase as input.
Then, we begin our hierarchical localization process by 
1 turning the project codebase into a tree-like structure format that demonstrates the relative location of each file in the project.
Next, 
2 using this repository structure format along with the original issue description, we ask the LLM to localize and rank the top N most suspicious files that need editing to solve the issue.
However, not all contents in each file need to be modified.
As such, 
3 we provide a skeleton for each file (i.e., a list of declaration headers of the classes and functions) and ask the LLM to output a specific list of classes and functions that we should examine more closely to fix the bug.
We then provide the complete code content of the previous locations and 
4 ask the LLM to finalize a smaller set of edit locations (i.e., classes, functions, or even specific lines).
For the repair phase, we provide the code snippets at these edit locations together with the issue description and 
5 ask the LLM to sample multiple patches to solve the issue.
Next, 
6 we perform a simple filtering to remove any patches with syntax errors and regression test failures, and use majority voting to rank the remaining patches.
Finally, 
7 Agentless selects the top-ranked patch as the final patch for submission.
We now describe the steps in each of Agentless's two phases in more detail.

#### Localization \scalerel*C

To fix or implement a new feature, the first step is to obtain the locations in the source code, as without the correct locations, it can be impossible to provide the right edits.
The difficulty lies in the fact that there could be hundreds of files
with thousands of lines of code each in a repository, whereas the correct locations to edit are only a few selected lines or functions.
Agentless addresses this by using a simple three-step hierarchical localization process: 1) localize to selected files; 2) localize each selected files into relevant classes, functions, and variables; 3) localize to code edit locations.

Localize to suspicious files. First, Agentless localizes the possible locations to specific suspicious files.
Instead of providing the complete code snippet for each file in the repository, Agentless constructs a succinct representation of the repository's file and directory structure.
We refer to this as the repository structure format,
which begins with the root folder of the repository and organizes code files or folder names.
Files and folders at the same directory level are aligned vertically, and files/folders in sub-directories are indented.
We recursively traverse the entire repository to obtain the repository structure format, which will be used as input for the LLM.
The repository structure format provides the necessary file paths alongside the neighboring file names to maintain organizational information in the original codebase.
Agentless then inputs the processed repository structure format along with the original issue description to an LLM and requests it to identify a list of the top N suspicious files in the repository that need further inspection or modification to resolve the issue.

Localize to related elements.
After obtaining the list of suspicious files to edit to solve the issue, Agentless then moves on to the second part of the localization process: localize to related elements within the suspicious files.
Directly providing the complete context of all files can be large.
As such, Agentless builds a compressed format of each file that contains the list of class, function, or variable declarations.
We refer to this format as skeleton format, with an example shown in Figure 2.
In the skeleton format, we provide only the headers of the classes and functions in the file.
For classes, we further include any class fields and methods (signatures only).
Additionally, we also keep comments in the class and module level to provide further information.
Compared to providing the entire file context to the model, the skeleton format is a much more concise representation, especially when the file contains thousands of lines, making it impractical/costly to process all at once with existing LLMs.
We provide the skeleton of all suspicious files to the LLM at one time in a single prompt, enabling the model to comprehensively analyze the pertinent information and decide the most relevant elements.
Using this input, we ask the LLM to provide a list of related classes and functions that one should examine to fix the provided issue.

Localize to edit locations.
The previous localization step provided us with a list of related code elements.
We then directly provide the code content from these elements to the model and ask it to localize to specific edit locations.
Compared to using the entire file content, the input context we provide here is much smaller.
With this input, we then ask the LLM to identify the final set of edit locations, specified by line numbers, functions, or classes.
Our simple hierarchical localization process allows Agentless to select a set of relevant code snippets as edit locations to perform repair.

#### Repair \scalerel*C

In the repair stage, the goal is to produce the correct patch to solve the issue.
Following existing work on LLM-based program repair [31; 48; 27], we first utilize the identified edit locations and construct a context window of code snippets to provide to the LLM for repair.
For example, if the identified location was a class from line 40 to 78, we would produce a context window of [40 - x, 78 + x] where x denotes the context window size.
The intuition behind adding the additional code before and after the identified location is to provide the LLM with relevant contextual information for better program repair [57].
If multiple edit locations are identified, we would concatenate these context windows together separated with ``...'' to indicate missing context in the middle.

Patch format. Using the code snippets, we then ask the LLM to generate patches to solve the issue.
However, instead of directly producing the entire code snippet to replace the entire given context, Agentless asks the LLM to generate a Search/Replace edit [21]: a simple
diff format to efficiently create each patch.
Figure 3 shows an example of the Search/Replace format containing two main parts: 1) search: the original code snippet we want to replace and 2) replace: the replacement code snippet we want to replace with.
To apply the generated Search/Replace diff to the original file, we can simply match the search code snippet and replace it with the replacement.
This simple diff format avoids generating the complete code and instead focuses on producing small edits, which are not only more cost-efficient, but also more reliable and accurate (less chances for hallucination).

Filtering and patch selection. For each issue, Agentless uses the LLM to generate multiple potential patches (starting with greedy and then sample multiple patches with higher temperature).
We also apply traditional software engineering technique of regression testing [55] to run the existing tests in the repository on all the generated patches.
Any patches which failed the existing tests can be filtered out as they incorrectly change the correct behavior of previous code.
Note, our implementation of this regression test filtering step follows prior work also evaluated on the same benchmark [21; 17].
For the remaining patches, Agentless applies a re-ranking approach using majority voting:
We first normalize each patch to ignore surface-level differences (e.g., extra spaces, newlines, and comments), and then select the patch with the highest number of occurrences as the final patch for submission. More specifically, to standardize the patch, we begin by parsing both the old and new code (after applying the patch) into abstract syntax trees. Next, we unparse the trees into a canonical source code format with docstrings removed. Finally, we compute the textual diff between the standardized old and new code to get the normalized patch.

Agentless solves repository-level issues using a simple step-by-step procedure.
We note here that none of the techniques used by Agentless in isolation are revolutionary,
but instead Agentless smartly combines existing techniques to construct an easy-to-understand approach.
Different from prior autonomous agent-based tools that involve complex interactions with the environment, Agentless uses a simple two phase approach to first localize and then repair the bug without relying on any agents for decision-making.
By conducting localization in a hierarchical manner, Agentless can efficiently and effectively compute the fine-grained locations for editing.
Agentless then performs repair by sampling multiple patches using a simple diff format.
We filter out any patches with syntax and regression tests errors, and finally select the patch for submission using classic majority voting.

### Experimental Setup

Datasets.
We evaluate Agentless and baselines using the popular SWE-bench dataset to test the ability to solve real-world software engineering issues.
Each problem in SWE-bench requires submitting a patch to solve the underlying issue described in the input issue description.
In particular, we focus on the filtered subset SWE-bench Lite, containing 300 problems with tests to evaluate the functional correctness of submitted patch.
Furthermore, we also conduct a detailed study (Section 5.1) on the SWE-bench Lite benchmark to not only demonstrate potential issues and biases but also produce a more rigorous filtered set of problems for better evaluation.

Implementation.
We implement Agentless using GPT-4o (gpt-4o-2024-05-13) [45].
By default, we query the LLM with greedy decoding.
During sampling, we use a sampling temperature of $0.8$.
For each issue, we first localize to the top three suspicious files, and then localize to an unrestricted number of suspicious classes and functions within these files, all using greedy decoding.
Next, to maximize the chances of finding the correct edit locations, we draw four samples of edit locations per issue (i.e., the third step in the localization phase), and combine two sampling runs together to provide more context for repair.
This gives us two separate sets of edit locations per issue.
For each set, we adopt a context window of $\pm$ 10 lines around each edit location, and generate 21 patches (1 greedy and 20 samples).
This results in a total of 4211the answer to the ultimate question of life, the universe, and everything [12] patches per bug.
We adopt the same Search/Replace edit format from prior work [21], and use the built-in Python ast library [2] to perform parsing in our patch normalization step.
Due to issues with the original SWE-bench evaluation script at the time of writing, we adopt the SWE-bench-docker [68] evaluation setup used by prior tools [21].

Baselines.
We compare Agentless against 13 agent-based approaches.
These baseline tools represent the state-of-the-art performance on SWE-bench.
We include state-of-the-art open-source as well as commercial or closed-source baselines (indicated via a \scalerel*C).
We note here that the majority of the closed-source baselines do not provide any trajectories, just the submission patches. Therefore, we cannot verify the steps taken to arrive at the final patches.
Moreover, we also include a simple agentless baseline using retrieval-augmented generation (RAG) proposed as part of SWE-bench [28] for comparison.
In this case, the agentless baseline uses the LLM to directly generate a patch file by providing it with the file content of the most relevant files, retrieved using BM25 [49].
Additionally, we also list the underlying LLM used by each tool whenever possible.

Metrics.
Following prior work [65], we report 1) % Resolved: the percentage of resolved problems in the benchmark, 2) Avg. $ Cost: average inference cost of running the tool, and 3) Avg. # Tokens: average number of input and output tokens used to query to LLM.
Additionally, we also report the % Correct Location: the percent of problems where the patch produced by the tool matches with the edit location of the ground truth developer patch.
We compute this metric over three granularities: file, function, and line.
We report that a patch contains the correct location if it edits a superset of all locations in the ground truth patch.
For baseline tools, we directly use the reported results either from the official leaderboard [29] or from the tool's official paper/repository.

### Evaluation

Repair performance. Table 1 shows the main evaluation result of Agentless and prior agent-based approaches on SWE-bench Lite.
We observe that Agentless is able to solve 82 out of 300 problems (27.33%).
While this is not the highest percentage of problems solved on SWE-bench Lite, Agentless is extremely competitive compared with prior agent-based approaches while using a much simpler design and overall technique.
It is important to note here that many of the top techniques are closed-source/commercial and did not release any source code to reproduce experiments or even trajectories for further verification.
Compared with open-source approaches, Agentless is able to achieve the highest performance of 27.33% (82 / 300) on SWE-bench Lite.
Additionally, Agentless only costs on average $0.34, which is drastically less than prior agent-based approaches.
Comparing against the RAG agentless baselines, we see that while Agentless costs slightly more, Agentless is also able to fix way more issues.

Unique issues fixed. Figure 4 shows the unique issues solved by Agentless compared with the top-performing closed-source/commercial and open-source approaches (``Others'' in Figure 4 indicates all other approaches within each category).
First, we see that compared to the open-source agent-based techniques, Agentless is able to fix 15 issues that no other existing open-source agent can resolve, showing the success of using a simple agentless approach in solving difficult issues.
Furthermore, even when compared with high-performing commercial approaches, Agentless is still able to offer unique fixes, with even more unique patches than Alibaba Lingma Agent – the top commercial solution!
This demonstrates that Agentless can be complementary to existing commercial agent-based setups.

Localization performance. In real-world software development, apart from directly fixing the issue, providing the correct edit location to human developers is extremely helpful for debugging.
As such, we examine the locations of the patches generated by each technique compared with the ground truth patch.
We note here that it is possible to fix a bug in a different location than the ground truth, however comparing against the ground truth patch can still serve as an approximate measure.
Table 1 additionally shows the percentage of submitted patches with correct locations for each tool, across line, function, and file levels.
We first observe that the percentage of patches with correct locations correlates heavily with the solve rate.
Interestingly, the highest result in terms of file-level location is OpenCSG StarShip at 90.0%, significantly higher than even the best-performing approaches while at the same time having a relatively low solve rate (23.67%).
As OpenCSG StarShip is a commercial product that does not provide source code or detailed trajectories, it is difficult to explain this huge difference between localization and repair performance.
In terms of localization performance, by using our simple hierarchical approach, Agentless remains very competitive compared with previous agent-based approaches (best function-level, and second-best file- and line-level localization among all open-source approaches).

Ablation study on components of Agentless.
Next, we look at how each component in both localization and repair phases contributed to the final Agentless performance.
Table 2 shows the performance of each of the 3 step in Agentless's localization phase (for step-3, the metrics are averaged across two sets of locations, with the cost being the total cost).
We show after each localization step the percentage of ground truth edit locations that still remains, the lines of code in each localization, and the average dollar cost of each step.
We observe that Agentless is able to localize the ground truth file in 77.7% of cases; however, using all of the localized files leads to a huge number of code lines as part of the context.
As such, in our second localization step, we localize to relevant classes and functions, and are able to drastically reduce the context window.
Finally, Agentless localizes to the exact edit locations needed to achieve even more context reduction without losing much of the localization accuracy.
Furthermore, we observe that by using hierarchical localization steps, Agentless can successfully minimize the cost while performing effective localization.

We now look at the impact of our different repair setups on the final performance. Table 3 shows the different ways we can generate or select the final patch for submission.
Starting with just generating a single sample (i.e., using greedy decoding), Agentless can achieve 70 correct fixes while costing an average of $0.11 dollars per bug (total cost, including localization).
We note that even with this simple patch generation step, Agentless can already beat the majority of the prior open-source agent-based approaches (with more than 4X in cost reduction).
We can further improve performance to 78 fixes by sampling the LLM multiple times and selecting a patch using majority voting.
Finally, the full Agentless performance is achieved by further applying filtering to select only the patches which can successfully pass the existing regressions tests.
Since we sample multiple patches per each issue, we also observe that the total number of possible issues that Agentless can solve when using all samples is 123 (41.0%).
This shows a high upper bound for the repair potential of Agentless with future work being better re-ranking and selection techniques to further improve the overall performance.

### Additional Analysis on SWE-bench Lite

#### Problem Classification

We now take a closer look at the problems in SWE-bench Lite.
We first classify the existing problems to gain better understanding and additional insights on exactly what types of problems Agentless and prior approaches can solve.
Specifically, we perform manual classification based on the issue description and ground truth developer patch of each problem.
Below describes each of classification dimensions and their categories in more detail:

1) Description quality.
We first inspect whether each issue description contains sufficient information to perform the desired task.
Figure 5(a) shows the distribution of each category: (i) contains enough information in natural language, (ii) contains reproducible failure example, (iii) contains partially reproducible example, and (iv) does not contain enough information.We observe that while a majority of the tasks in SWE-bench Lite contains sufficient information, with many having some small failure examples to showcase the bug, there is a non-trivial percentage (9.3%) of problems which do not contain enough information.
Such problems include those that require implementing a new function with a specific name or adding an error message with a specific string that was not provided in the problem description.22These types of problems still exist in the benchmark despite claims that they have been completely removed by the filtering process according to SWE-bench Lite.
This means the test will fail if the function name or error message string does not match exactly, even if the underlying functionality is correctly implemented.
Another example of insufficient information are problems that have multiple different interpretations on how to solve the issue, and only a subset of them can pass the ground truth test.
For instance, the issue description will outline two possible solutions suggestions with only one of them aligned well with developer intention.
Implementing the other proposed solution suggestion will lead to test failure.
This highlights the necessity to further sanitize/improve SWE-bench Lite where these problems with uninformative descriptions shall be further excluded.

2) Solution in description.
We also examine whether the solution or steps to solve the problem are already provided in the issue description.
Figure 5(b) shows the breakdown of our categories: (i) no solution or steps provided, (ii) partial solution provided (e.g., some steps in natural language), (iii) complete solution provided (e.g., complete steps in natural language), (iv) exact patch provided, and (v) misleading solution or steps.
Interestingly, we observe that 4.3% of issues contain the exact ground truth patch in the issue description, while an additional 10.0% of issues describe the exact steps required to come up with the correct solution.
This shows that certain problems in SWE-bench Lite can be much easier to solve since they provide the solution either in exact code snippets or natural language.
Furthermore, we also observe 4.3% of issues contain proposed solution or steps in the issue description that do not reflect the ground truth patch introduced by the developers.
This further highlights potential issues with the benchmark, as these discrepancies can mislead tools to generate incorrect solutions simply by following the issue description.

3) Location information.
We further check if the issues description contains the correct location information.
We divide the granularity into line, function, and file level locations.
Our categories are: (i) exact locations in natural language, (ii) exact locations provided in failure stack traces, iii) related keywords in the issue description that can be used to search for the location, and (iv) not provided.
We first observe that only in very few cases ($<$10%), the issue provides the exact lines needed to fix the bug.
However, this number increases as we increase the granularity to functions and files where we found that around half of the issues already provide the location of the file needed to be edited in the description.
To repair a bug or introduce a new feature, finding the location to make the edit is extremely important.
As such, we leverage this classification and focus our later analysis on the effect the provided location has on the repair performance of Agentless and baseline approaches.

These classification dimensions and categories raise potential issues with the SWE-bench Lite problems such as unsolvable questions, misleading potential solutions, and significant differences in problem difficulties.
These issues have not been properly considered by either the benchmark creation process or prior approaches.
Furthermore, we hope our classification can provide additional insights on the type of problems that can be solved by existing and future approaches.

#### SWE-bench Lite-SSS

Building on the above problem classifications, in the following evaluation section, we will more rigorously compare and contrast Agentless and existing work.
Specifically, we focus on a subset of the problems in SWE-bench Lite after removing the problems that contain the exact patch in the problem description, misleading solutions, or do not provide enough information in the original issue description.
This eliminates the less reasonable problems and normalizes the difficulty level of the benchmark.
For future work, we hope to work with the maintainers and contribute to the SWE-bench Lite benchmark by fixing these unreasonable problems to add additional information as well as removing exact ground truth patches in the problem descriptions.
However, as we are not able to run commercial tools ourselves on the modified problems,
we simply exclude the problematic problems in the below evaluation.
We refer to our subset of 252 problems as SWE-bench Lite-$S$.

Table 4 shows the results on the SWE-bench Lite-$S$ benchmark and the corresponding ranking of each approach.
We also included the results on the original 300 problems in SWE-bench Lite for comparison.
While the general ranking of all approaches stay roughly the same, we do observe some small ranking changes.
Compared to the original SWE-bench Lite, our filtered benchmark of SWE-bench Lite-$S$ provides a more accurate reflection of the true capability of autonomous software development tools.

Using the classification results, we further examine the types of problems that are solved by Agentless and prior approaches on SWE-bench Lite-$S$.
Figure 6 shows the solve rate of various top-performing open-source and closed-source approaches across the different categories of problems.
We first examine if having code examples to reproduce the error in the issue description can help the LLM better solve the issue in Figure 6(a).
Surprisingly, we found that the solve rate of all prior approaches drop when evaluated on the problems with reproducible code examples.
Many agent-based approaches [61; 10; 17] attempt to first reproduce the error, however, this may not improve performance even on problems with already provided reproducible examples.
This shows that there are still room for further improvement specifically on reproducing error-triggering tests.
Next, we look at the effect of ground truth patch/solution in the issue description.
Figure 6(b) shows the expected result where all selected techniques perform better on issues that already provide solution steps in natural language.
Furthermore, in Figure 6(c), we examine the solve rate with respect to the location information provided in the issues description.
Unsurprisingly, we found that the highest solve rates are on problems where the location is provided in natural language followed by stack traces.
The most difficult problems are those that do not contain any clues about the location of the issue in the description.
We observe that compared with closed-source approaches, Agentless performs comparably when the location is provided in either natural language, stack trace, or keywords.
However, the closed-source agent tools perform better compared to Agentless in the case where no location clue is provided.
This highlights an advantage of agent-based tools in solving these more complex problems where they are able to use complex code search tools.
This represents potential future work for Agentless to target and further improve these types of problems.

### Related Work

LLMs for code.
LLMs have become the default choice for various coding tasks, due to the impressive results achieved by LLMs in both code generation and understanding [18].
Developers and researchers have applied on software engineering tasks, such as program synthesis [47; 18; 35; 25], code translation [46; 50; 51], program repair [59; 58; 42; 31; 15], and test generation [19; 60; 20; 33; 30].
Apart from using general-purpose LLMs, code-specific LLMs have been built by further training LLMs using large amounts of open-source code snippets.
Examples of code LLMs include Codex [18], CodeLlama [52], StarCoder [34; 39], DeepSeek-Coder [22], etc.
Furthermore, researchers have also developed instruction-following code-specific LLMs using instruction-tuning methods.
Examples of such LLMs include CodeLlama-Inst [52], DeepSeek-Coder-Inst [22], WizardCoder [40], Magicoder [54], and OpenCodeInterpreter [67].

Benchmarking for LLM-based coding tasks.
To evaluate the capability of LLMs on code, various benchmark has been proposed.
HumanEval [18] and MBPP [14] are two of the most widely-used handcrafted code generation benchmarks complete with test cases to check for the correctness of LLM outputs.
Furthermore, other benchmarks have been proposed with more robust test [37], additional programming languages [66; 16], and other programming domains [26; 23; 36; 32; 62].

More recently, instead of evaluating on self-contained coding problems, researchers have developed benchmarks focus on solving real-world software engineering issues by operating on an entire coding repository [28; 63; 38].
One such popular benchmark is SWE-bench [28], containing problems where the goal is to modify the repository and resolve a real-world GitHub issue.
The authors of SWE-bench have since published a smaller filtered subset of SWE-bench Lite [11], containing 300 total problems, focused on bug fixing issues that only modify a single file in the ground truth patch. In this work, we conduct a detailed classification and analysis of the problems in SWE-bench Lite.
We found that some problems lack sufficient information in the problem description to correctly solve the problem.
Furthermore, there are also problems containing misleading patches, which can confuse the model.
Recognizing these limitations, we further filter SWE-bench Lite to remove such problems and construct SWE-bench Lite-$S$ that can serve as a more rigorous set of problems to evaluate different tools.

Agent-based software development.
With the emergence and popularity of agent-based frameworks [56], recently researchers and industry practitioners have begun developing agent-based approaches to solve software engineering tasks.
Devin [4] (and OpenDevin [10], open-source alternative), is one of the first end-to-end LLM agent-based framework.
Devin uses agents to first perform planning based on user requirement, then allows the agent to use file editor, terminal, and web search engine tools to iteratively perform the task.
SWE-agent [61] designs a custom agent-computer interface (ACI) that allows the LLM agent to interact with the repository environment with actions such as reading, editing file, and running bash commands.
AutoCodeRover [65] is another agent-based approach that provide the LLM agent with specific APIs (e.g., searching methods in certain class) to effectively find the locations that need to be modified to solve the issue.
In addition to these highlighted examples, there has been a plethora of other agent-based approaches developed in both open-source [21] and close-source/commercial products [15; 17; 41; 7; 5; 6; 9; 8; 1].
Compared to these agent-based techniques, Agentless offers a simple and cost-effective solution to tackle real-world software engineering issues.
Agentless demonstrates for the first time that an agentless approach can achieve similar performance, without the additional baggage of having to providing excessive tools or modeling complex environment behavior/feedback.

### Conclusion

We propose Agentless– an agentless approach to automatically tackle software development problems.
Agentless uses a simple two phase approach of localization followed by repair.
Compared to prior agent-based approaches, Agentless deliberately disallows the LLM for autonomous tool usage or planning.
Our evaluation on the popular SWE-bench Lite benchmark demonstrates that Agentless can achieve the highest performance compared with other open-source techniques while at the same time minimizing the cost.
Furthermore, we perform a detailed classification of problems in SWE-bench Lite to not only offer new insights but to construct a more rigorous benchmark of SWE-bench Lite-$S$ after removing problematic problems.

### Acknowledgments

We thank Jiawei Liu for providing some of the resources used to run the experiments. One of the authors would like to thank Jun Yang for generously gifting his old bike33Sadly the bike is currently broken. which allowed the author to travel faster and thus increasing research speed.
