# Plan-Then-Execute: An Empirical Study of User Trust and Team Performance When Using LLM Agents As A Daily Assistant

**Authors:** Gaole He, Gianluca Demartini, Ujwal Gadiraju

## Abstract

Since the explosion in popularity of ChatGPT, large language models (LLMs) have continued to impact our everyday lives. Equipped with external tools that are designed for a specific purpose (e.g., for flight booking or an alarm clock), LLM agents exercise an increasing capability to assist humans in their daily work. Although LLM agents have shown a promising blueprint as daily assistants, there is a limited understanding of how they can provide daily assistance based on planning and sequential decision making capabilities. We draw inspiration from recent work that has highlighted the value of ‘LLM-modulo’ setups in conjunction with humans-in-the-loop for planning tasks. We conducted an empirical study (NN = 248) of LLM agents as daily assistants in six commonly occurring tasks with different levels of risk typically associated with them (e.g., flight ticket booking and credit card payments). To ensure user agency and control over the LLM agent, we adopted LLM agents in a plan-then-execute manner, wherein the agents conducted step-wise planning and step-by-step execution in a simulation environment. We analyzed how user involvement at each stage affects their trust and collaborative team performance. Our findings demonstrate that LLM agents can be a double-edged sword — (1) they can work well when a high-quality plan and necessary user involvement in execution are available, and (2) users can easily mistrust the LLM agents with plans that seem plausible. We synthesized key insights for using LLM agents as daily assistants to calibrate user trust and achieve better overall task outcomes. Our work has important implications for the future design of daily assistants and human-AI collaboration with LLM agents.

### Introduction

Autonomous agents have been regarded as a research focus for artificial intelligence (AI) over the last century (Albrecht and Stone, 2018).
With the wish that autonomous agents can make our life better, many autonomous agents have been designed as virtual personal assistants (Kepuska and Bohouta, 2018).
These AI assistants (e.g., Siri) perform well (albeit imperfectly) in following user instructions to execute low-risk tasks like playing a song, reporting weather forecasts, or searching for an image to support everyday tasks. However, on tasks entailing potential risks (e.g., monetary payments or hiring an employee), humans hesitate to trust such AI systems due to loss aversion (Tversky and Kahneman, 1991) and algorithmic aversion (Hou and Jung, 2021; Mahmud et al., 2022; Dietvorst et al., 2015).
Only when users can obtain a sense of control by being able to modify the outcomes of imperfect AI can they overcome such algorithm aversion and be willing to collaborate with imperfect AI systems (Dietvorst et al., 2018).

With the recent rise of large language models (LLMs) in natural language understanding and generation (Zhao et al., 2023), researchers have started to analyze LLM-based agents and their applicability in a plethora of tasks  (Xi et al., 2023; Wang et al., 2024b).
The term ‘LLM agent’ refers to an artificial entity based on LLMs that perceives its context, makes decisions, and then takes actions in response (Xi et al., 2023).
Compared to existing deep learning and LLM-based methods (e.g., chaining multiple LLMs (Wu et al., 2022)), LLM agents provide more flexibility in task solving and user interaction, which makes them suitable for daily assistance. This is primarily due to three reasons.
First, with a planning module, LLM agents can generate a dynamic plan based on the tools provided (Xi et al., 2023; Wang et al., 2024b).
Such plans are typically defined in a logical structure — step-wise plans, which can be easily understood by humans.
Second, with LLMs as a core control module, users can access and interact with external toolkits via a more natural interaction (i.e., conversation) with LLM agents (Bommasani et al., 2021; Zhao et al., 2023), reducing manual control efforts over function-specific tools.
For example, LLM agents can complete time-consuming jobs like information seeking and information filtering (e.g., searching for a flight in itinerary planning) based on specific user needs.
Third, the Markov decision process of LLM agents can generate a sequence of actions (i.e., using external toolkits)11In our study, the usage of one tool is the same as executing one action. Therefore, we refer to a tool and action interchangeably. as output.
Paired with an understanding of actions and necessary parameters for the interaction with the LLM agents, users can get involved in the real-time execution of tasks with LLM agents and fix potential problems while benefiting from task delegation (Lubars and Tan, 2019). Based on an intuitive framework for task delegation, Lubars et al. (Lubars and Tan, 2019) found that user trust can play an important role in human delegation behaviors to AI systems. However, there is a relatively limited understanding of user trust development and calibration in collaboration with LLM agents.

There is also a growing debate in the machine learning and AI research communities about whether LLMs can be truly considered as reasoning and planning agents (Kambhampati et al., 2024). With this in the backdrop, existing work on automated task completion has revealed that LLM agents can exhibit promising performance in handling complex tasks like playing games (Wang et al., 2023a), answering complex questions (Zhuang et al., 2024), and in simulating social behavior (Park et al., 2023).
However, such agents are still far from perfect. Due to the probabilistic nature of LLMs, there is much uncertainty in automating LLM agents for tasks with high risks attached. To avoid unintended or unexpected consequences, there is a need for user control over the real-time execution process. Through an empirical study of LLM planning capabilities, planning experts found that “LLMs’ ability to generate executable plans autonomously is rather limited” (Valmeekam et al., 2023).
However, when combined with a sound planner in an ‘LLM-Modulo’ mode, “the LLM-generated plans can improve the search process for underlying sound planners” (Valmeekam et al., 2023).
Humans can potentially be the ‘sound planners’ who can work in conjunction and optimize plans drafted by LLMs, which can then be executed by LLM agents. Such human-AI collaboration can reduce human efforts in generating a reliable plan from scratch.

Attracted by the promise of LLM agents, there have been some early explorations (Geissler et al., 2024) of adopting them in human-AI collaboration.
However, the existing works have mainly analyzed how LLM agents can serve specific use cases (e.g., design creation (Geissler et al., 2024)), and others have conducted structured interviews to obtain expert insights (Zhang et al., 2024; Zheng et al., 2023).
It is still unknown how well LLM agents can work as general daily assistants to assist users in everyday tasks with varying stakes and how user trust and team performance are shaped by interacting with LLM agents.

In our work, we address this research gap and adopt LLM agents to assist humans in everyday tasks by following a plan-then-execute workflow (Wang et al., 2023b).
First, the LLM agent generates a step-wise plan formulated with a hierarchical structure.
Then, the LLM agent executes the generated plan by transforming it into a sequence of actions (leveraging external toolkits).
The benefits of such a plan-then-execute framing are three-fold:
(1) Compared to a dynamic process where planning and execution are bound closely, separating planning and execution into two stages provides more task clarity to the users, which reduces user cognitive load and contributes to the quality of task outcomes (Gadiraju et al., 2017).
(2) With planning at the beginning of the task, users can develop a global understanding of how the LLM agents will execute the task.
Based on a follow-up step-by-step execution, it would be straightforward for users to be involved in such a process and control the outcomes of task execution. (3) Planning and execution are representative abstractions of how LLM agents work.
The findings of such an empirical study can be generalized to human-AI collaboration with other kinds of LLM agents (e.g., dynamic planning-execution). To this end, we propose the following research questions:

RQ1: How does human involvement in the high-level planning and real-time execution shape their trust in an AI system powered by LLM agents?

RQ2: How does human involvement in the high-level planning and real-time execution of tasks with an AI system powered by LLM agents affect the overall task performance?

Addressing these research questions, we carried out an empirical
study ($N$ = 248) of human-AI collaboration in six different everyday scenarios with varying stakes and risks attached (e.g., credit card payment and itinerary planning).
We found that user involvement in the planning and execution can be beneficial in addressing imperfect plans and fixing execution errors.
As a result, LLM agents can achieve better task performance. However, we also found that user involvement in the planning and execution stages of the LLM agent fails to calibrate user trust in corresponding task outcomes.
A potential reason here is that the plausible plans generated by the LLMs can mislead users into trusting the LLM agents when they are in fact wrong.
Our findings highlight that user involvement can also bring about additional trade-offs to consider: (1) user involvement in the planning and execution poses a high cognitive load on users and decreases user confidence in their decisions; (2) user involvement can be harmful in some task contexts (e.g., user involvement reduces plan quality).
Further research is required to understand when to provide necessary user involvement.
Our key insight is that as opposed to following a fixed mode of user involvement, it is prudent to explore how user involvement in planning and execution can be tailored to fit the task and the user. Based on our quantitative and qualitative findings, we share insights for designing effective LLM agents as daily assistants and synthesize promising directions for further research around LLM agents in the context of human-AI collaboration.
Our work has important theoretical implications for human-AI collaboration with LLM assistance and design implications for plan-then-execute LLM agents to support human-AI collaboration.

### Background and Related Work

Our work proposes to analyze how user involvement in the planning and execution stages of LLM agents shapes user trust in the LLM agents and the overall task performance of LLM agents.
Thus, we position our work in three realms of related literature: human-AI collaboration (§ 2.1), trust and reliance on AI systems (§ 2.2), task support with LLMs and LLM agents (§ 2.3).

#### Human-AI Collaboration

In recent decades, deep learning-based AI systems have shown promising performance across various domains (Yang et al., 2022; Fernando et al., 2021) and applications (Pouyanfar et al., 2018; Dong et al., 2021).
However, such AI systems are not good at dealing with out-of-distribution data (Jia and Liang, 2017; McCoy et al., 2019), and their intrinsic probabilistic nature brings much uncertainty in practice (Ghahramani, 2015).
Such observations raise wide concerns about the accountability and reliability of AI systems (Kaur et al., 2022).
Under such circumstances, human-AI collaboration has been recognized as a well-suited approach to taking advantage of their promising predictive power and ensuring trustworthy outcomes (Lai et al., 2023; Jiang et al., 2021).
While humans can provide more reliable and accountable task outcomes, too much user involvement to check and control AI outcomes is undesirable (Lai et al., 2022).
It goes against the premise that AI systems are introduced to reduce human workload.
In that context, researchers have theorized and empirically analyzed when and where users could and should delegate to AI systems (Lai et al., 2022; Lubars and Tan, 2019).

Task Delegation. While humans prefer to play the leading role in human-AI collaboration (Lubars and Tan, 2019), delegating to AI systems can bring benefits like cost-saving and higher efficiency.
Apart from manual delegation decisions, it is common to apply automatic rules for human delegation (e.g., heuristics obtained from domain expertise or manually crafted rules (Lai et al., 2022)).
Many user factors like trust (Lubars and Tan, 2019), human expertise domain (Erlei et al., 2024), and AI knowledge (Pinski et al., 2023)) have a substantial impact on human delegation behaviors.
Another relevant stream of recent research has explored AI delegation to humans (Madras et al., 2018; Fügener et al., 2022; Pinski et al., 2023).
Researchers have investigated the conditions under which AI systems should defer to a human decision maker, which may bring benefits of improved fairness (Madras et al., 2018), accuracy (Narasimhan et al., 2022), and complementary teaming (Hemmer et al., 2022).
Compared to human delegation, AI delegation has been observed to achieve more consistent benefits in team performance (Fügener et al., 2022; Hemmer et al., 2023). In collaboration with LLM agents, users need to determine when they should be involved in high-level planning and real-time execution. Such involvement decisions are similar to the delegation choices made by users. While task delegation is not the focus of our study, future work can explore this further.

AI-assisted Decision Making has attracted a lot of research focus in human-AI collaboration literature.
Most existing work has conducted empirical studies (Lai et al., 2023) and structured interviews (Jiang et al., 2021) to understand how factors surrounding the user, task, and AI systems affect human-AI collaboration.
User factors like AI literacy (Chiang and Yin, 2022), cognitive bias (Rastogi et al., 2022), and risk perception (Fogliato et al., 2021; Green and Chen, 2021) have been observed to substantially impact user trust and reliance on the AI system.
Similarly, task characteristics like task complexity and uncertainty (Salimzadeh et al., 2023, 2024) and factors of the AI system (e.g., performance feedback (Bansal et al., 2019; Lu and Yin, 2021), AI transparency (Vössing et al., 2022) and confidence of AI advice (Tomsett et al., 2020; Zhang et al., 2020)) also affect user trust and reliance on the AI system.
For a more comprehensive survey of existing work on AI-assisted decision making, readers can refer to (Lai et al., 2023).

While machine learning and deep learning methods have been extensively analyzed in existing human-AI collaboration literature, to our knowledge, human-AI collaboration with LLM agents is still under-explored.
Unlike previous studies where AI systems only follow a fixed mode to generate advice, LLM agents can be equipped with more logical clarity and can provide a step-wise plan and can follow a step-by-step execution.
With such a plan-then-execute setup, LLM agents can bring high flexibility as well as uncertainty in high-level planning and real-time execution. Little is known about
how well LLM agents can work as daily assistants while handling tasks entailing varying stakes and potential risks. In our study, we analyzed the impact of user involvement in such AI systems by adjusting their intermediate outcomes (plan and step-by-step execution) to calibrate their trust and improve task outcomes.
Our findings and implications can help advance the understanding of the effectiveness of LLM agents in human-AI collaboration.

#### Trust and Reliance on AI systems

Trust and reliance have been important research topics since human adoption of automation systems (Lee and See, 2004; Dzindolet et al., 2003). Due to the widespread integration of AI systems in nearly all walks of society, there has been a growing interest in understanding user trust (Vereschak et al., 2021; Mehrotra et al., 2024) and reliance (Eckhardt et al., 2024) on AI systems.
User trust in the context of human-AI collaboration is typically operationalized as a subjective attitude toward AI systems/AI advice (Lee and See, 2004).
In comparison, user reliance on AI systems is based on user behaviors (e.g., adoption of AI advice and modification of AI outcomes).
The two constructs have been shown to be highly related (Lee and Moray, 1992; Lee and See, 2004): for example, user trust can substantially affect user reliance (Lee and See, 2004).
However, they are intrinsically different and cannot be viewed as a direct reflection of each other (Kahr et al., 2024).
Most existing work has, therefore, studied the two constructs separately in terms of subjective trust and objective reliance.

Earlier work exploring human-AI trust primarily focused on the impact of different contextual factors surrounding user (e.g., risk perception (Green and Chen, 2021)), task (e.g., task complexity (Salimzadeh et al., 2023)), and system (e.g., stated accuracy (Yin et al., 2019; Zhang et al., 2020)).
Empirical studies have shown that most users tend to trust AI systems that are perceived to be highly accurate (Yin et al., 2019).
Such trust is vulnerable, as the AI system may provide an illusion of competence with persuasive technology (e.g., explanations (Chromik et al., 2021; He et al., 2025)) or overclaimed performance (Yin et al., 2019).
Even if the AI systems are accurate on specific datasets, they still suffer from out-of-distribution data (Liu et al., 2021; Chiang and Yin, 2021).
The misplaced trust in the AI systems can lead to misuse of the systems.
Several empirical studies (Tolmeijer et al., 2021) have shown that once users realize the AI system errs or performs worse than expected, their trust in the AI system can be violated, even resulting in the disuse of the AI system.
Both the misuse and disuse of the AI system hinder optimal human-AI collaboration.

To address such concerns, researchers have explored how to help users calibrate their trust in the AI system. Different techniques to help users realize the trustworthiness of the AI system have been proposed (Kaur et al., 2022; Rechkemmer and Yin, 2022; Ma et al., 2023).
For example, increasing the transparency of AI systems by providing confidence scores (Zhang et al., 2020), explanations (Wang and Yin, 2021), trustworthiness cues (Liao and Sundar, 2022), and uncertainty communication (Kim et al., 2024).
However, the actual trustworthiness of the AI system does not always align with user perception.
As found by Banovic et al. (2023), untrustworthy AI systems can deceive end users to gain their trust.
Another example is that users can develop an illusion of explanatory depth brought by explainable AI techniques (Chromik et al., 2021), which leads to uncalibrated trust in the AI system.
Even if users have indicated trust in the AI system, they may turn to rely more on themselves in final decision-making.
The reasons are complex, and many factors, such as accountability concerns (Lima et al., 2021; Tolmeijer et al., 2022) and cognitive bias (He et al., 2023), may affect user reliance behaviors.

While trust calibration is an important goal in human-AI collaboration, it may be not enough to ensure complementary team performance.
Through empirical user studies with different confidence levels of AI predictions, Zhang et al. (Zhang et al., 2020) found that “trust calibration alone is not sufficient to improve AI-assisted decision making”.
To achieve optimal human-AI collaboration, humans and AI systems need to play complementary roles (Hemmer et al., 2021, 2024), and humans need to know when they should adopt AI assistance.
In other words, humans should rely on AI advice when AI systems are correct and outperform them, and override AI advice when AI systems are incorrect or less capable than humans.
Such user reliance patterns are denoted as appropriate reliance (Schemmer et al., 2022, 2023), which is the key to
achieving complementary team performance.

The main issues that lead to sub-optimal human-AI collaboration are: under-reliance (i.e., disuse AI assistance when AI systems outperform humans) and over-reliance (i.e., misuse AI assistance when AI systems are wrong or perform worse than humans) (Schemmer et al., 2022).
Users with an uncalibrated trust in the AI system can be easily misled to disuse or misuse AI systems (Jacovi et al., 2021).
Researchers have proposed various interventions to promote appropriate reliance (He et al., 2023; Lu and Yin, 2021; Lu et al., 2024; Chiang and Yin, 2021, 2022) and calibrate user trust in AI systems (Buçinca et al., 2021; Zhang et al., 2020).
For example, explainable AI methods have been shown to help reduce over-reliance (Vasconcelos et al., 2023) and under-reliance (Wang and Yin, 2021) in different scenarios albeit with little consistency across contexts.
Another example is tutorial interventions, which have shown effectiveness in user onboarding (Lai et al., 2020), mitigating cognitive biases (He et al., 2023) and developing AI literacy (Chiang and Yin, 2022).
For a more comprehensive overview of interventions to facilitate trust calibration and appropriate reliance, readers can refer to  (Lai et al., 2023; Eckhardt et al., 2024; Mehrotra et al., 2024; Kahr et al., 2024).

LLM agents (Wang et al., 2024b) have gained much popularity in recent years, distinguishing them from most prior AI systems.
They can communicate through conversation, plan logically, and can be built to leverage powerful external tools to achieve complex functions.
While trust and reliance have been extensively analyzed in existing human-AI collaboration literature, it is still unclear how users trust and rely on AI systems powered by LLM agents.
In our work, calibrated trust is adopted as an important goal for human-AI collaboration in the planning and execution stage.
Meanwhile, users are expected to fix potential errors in the planning and execution stages, reflecting their reliance on the AI system.
Our work can substantially advance the understanding of trust and reliance on plan-then-execute LLM agents.

#### Task Support with LLMs and LLM Agents

LLMs and LLM agents bring new opportunities and challenges to human-AI collaboration (Bommasani et al., 2021).
It is evident that their generation capabilities can help reduce the cognitive effort from humans. But LLMs are also riddled with challenges such as hallucination (Ji et al., 2023) (i.e., generated text seems plausible but is factually incorrect).
Failure to handle such issues may bring fatal errors with unaffordable costs depending on the context (e.g., medical diagnosis).

Due to the capability of generating coherent, knowledgeable, and high-quality responses to diverse human input (Wei et al., 2022), a wide community of human-computer interaction researchers has paid attention to large language models (Liao and Vaughan, 2023).
Researchers have actively explored how LLMs can assist users in various tasks like data annotation (Wang et al., 2024a; He et al., 2024b), programming (Omidvar Tehrani and Anubhai, 2024), scientific writing (Shen et al., 2023), and fact verification (Si et al., 2024).
All the above functions can be achieved with elaborate prompt engineering using a single LLM.
By chaining multiple LLMs with different functions, humans can customize task-specific workflows to solve complex tasks (Wu et al., 2022).
Apart from obtaining answers with a one-shot text generation, LLMs also provide convenient conversational interactions.
Through empirical studies, such conversational interactions have been shown to be effective in human-AI collaboration with multiple applications, such as decision making (Slack et al., 2023; Lin et al., 2024; Ma et al., 2024a), scientific writing (Shen et al., 2023), and mental health support (Sharma et al., 2023).
With the growing popularity of LLMs, more and more humans have begun to adopt LLMs (e.g., ChatGPT) to boost their work efficiency and productivity  (Zhao et al., 2023).

LLM agents have been shown to have good planning, memory, and toolkit usage capabilities (Xi et al., 2023; Wang et al., 2024b).
When suitable toolkits are provided, LLM agents can readily generate a task-specific plan and solve the tasks using toolkits.
Attracted by the promise of LLM agents, there have been some early explorations (Geissler et al., 2024; Zheng et al., 2023; Zhang et al., 2024) of adopting them in human-AI collaboration contexts.
These works were mostly analyzed in specific use cases (e.g., design creation (Geissler et al., 2024)).
It is unclear how user trust and team performance are affected by user interactions with LLM agents in a sequential decision making setup (i.e., solving a task by executing a sequence of actions) where users can be in control of the execution. To fill this research gap and advance our understanding of user control over LLM agents, we carried out a quantitative empirical study.

### Method

#### Overview of User Involvement in Plan-then-execute LLM Agents

In our study, we adopted plan-then-execute LLM Agents (Wang et al., 2023b) as assistants to help users handle daily tasks, e.g., itinerary planning and currency transactions. Figure 1 illustrates how users collaborate with plan-then-execute LLM agents.
First, the LLM agents will generate a step-wise plan based on a prompt specifying the plan format adopted from (Huang et al., 2024).
Then, users will make necessary edits to the plan based on the provided edit tools (will be further detailed in Section 3.2).
After the user edit, we obtained the step-wise plan as outcomes of the planning stage.
Next, the LLM agents will transform the step-wise plan into a sequence of action predictions, which will be served in a step-by-step manner.
Users will join the real-time execution process and check whether they approve the current predicted action (i.e., blue card shown in Figure 1) or they would like to modify the current action prediction. The user involvement in execution stages will be introduced in Section 3.3.
After the iterative execution of all steps, the task is solved. The evaluation of task performance is mainly based on the plan quality and execution accuracy of the action sequences.

Implementation details. In our study, we adopted GPT-3.5-turbo as the backbone LLM to serve the plan-then-execute LLM agent. The backend LLM agent implementation is mainly based on the Langchain plan and execute agent.22https://api.python.langchain.com/en/latest/plan_and_execute/langchain_experimental.plan_and_execute.agent_executor.PlanAndExecute.html The execution of tasks are based on a simulation environment, where all tools/actions of the LLM agents are pre-defined as backend APIs hosted with Flask33https://github.com/pallets/flask.
In the spirit of open science, all code and data analysis results can be found at Github.44https://github.com/RichardHGL/CHI2025_Plan-then-Execute_LLMAgent

#### Planning

While LLMs can generate high-quality plans, there is no guarantee of their correctness and their further impact on the execution of the plan.
Thus, involving users in the planning stage and controlling the plan quality would be essential to ensure successful subsequent execution.

Plan Format.
The step-wise plan in our study followed a hierarchical structure, adapted from a benchmark for LLM agents toolkit usage (Huang et al., 2024).
The whole plan consists of multiple sub-steps, which are at most three levels (e.g., 1., 1.x, 1.x.y where x,y are integers).
All sub-steps started with the same prefix index are denoted as one primary step (e.g., the three blocks of planning outcome in Figure 1).
A high-level step (e.g., 1.) will provide high-level instruction of the current primary step, while low-level steps (e.g., 1.x, 1.x.y) will provide subsequent details.
In the execution stage, each primary step will be used as the execution unit.
The LLM agent will transform one primary step into a predicted action filled with parameters.
Thus, we ask participants to provide all necessary details in sub-steps of each primary step. Each primary step will be transformed into single action in the follow-up execution stage.
If one primary step requires two actions to accomplish, it may cause a potential loss of one action.
Thus, when a plan contains one primary step that contains information about two potential actions (e.g., the initial plan in Figure 1), we consider it as a low-quality plan with ‘grammar errors.’55Note that this is not to be confused with the notion of grammar in language.
All these plan format designs are informed in our onboarding tutorial.

User-involved Planning. Figure 2 shows one screenshot of user-involved planning in our study.
At the top of the interface, we provide a task description along with three buttons: ‘Show Potential Actions’, ‘Plan Edit Instruction’, and ‘Add one step’.
By clicking ‘Show Potential Actions’, we provide a prompt window to show concrete documentary descriptions of all potential actions (including action purpose and parameters) to be used in the execution stage. All instructions used in our tutorial are accessible with clicking the button ‘Plan Edit Instruction’.
After users join the planning stage, an initial plan generated by LLM will be presented in the orange area. We allow users to edit the plan with following interactions:

Add step. By clicking ‘Add one step’ button, users can insert a valid sub-step index into the whole plan, and then they can edit the plan text.

Delete step. By clicking the ‘Delete step’ button at the end of one step, all sub-steps associated with that step will be deleted from the plan.

Edit step. By clicking the text input area in each step, users are allowed to edit the text with keyboard input.

Split step. By clicking the ‘Split step’ button associated with one step, we will split the original primary step into two primary steps. A new primary step will start the current step and contain all follow-up sub-steps. For example, if we click ‘Split step’ for the plan show in Figure 2 at index ‘2.2’. We will generate a new blank step ‘3.’ (where user input is expected) and re-index all sub-steps with ‘2.2.x’ to ‘3.1.x’. At the same time, the original plan steps behind it will be automatically updated. Through this action, users can easily split one step that contains too much information into two primary steps. Figure 1 shows an example of plan edit with ‘split step’.

#### Execution

After the planning stage, we obtain a plan with a step-wise structure.
In the execution stage, the LLM agent executes the outcome of the planning stage (i.e., a step-wise plan in text) in a step-by-step manner.
In each step, the LLM agent translates a single step of the plan into one action, which is implemented with an API call in the backend.
This setup is a simulation of real-world applications, which provide services with API calls (commonly implemented as langchain tools66https://python.langchain.com/v0.1/docs/modules/tools/). Such a simulation setup is effective in developing and validating theory (Davis et al., 2007) and has been widely adopted in existing research on agent-based modeling and HCI studies (Olson and Kellogg, 2014). To provide a smooth user experience, we adopted a conversational interface to present the execution process.
Figure 3 shows one screenshot of user-involved execution in our study.
As we can see, after a message of the first primary step of the plan, the LLM agent predicts one action ‘create_alarm’.
In our study, to provide a tidy view of the action prediction, we wrap the predicted action as one card (the blue area in Figure 3).

User-involved Execution.
Figure 3 presents a flow-chart to illustrate a primary step executed by the daily assistant (i.e., LLM agent). First, given one primary step, the daily assistant predicts an action based on a given list of prepared actions (i.e., pre-defined APIs in the backend). After users check the predicted action, they can choose from one of the following three buttons to respond. (1)‘Proceed’: It indicates users agree that the predicted action is correct. After clicking this button, the LLM agent moves forward to execute it and shows the execution result of this action.
(2) ‘Feedback’: Users can give text feedback based on the message input area at the bottom of the conversational interface. This triggers another action prediction based on the current primary step and user feedback. Then, users are provided with the three options to proceed again. (3) ‘Specify Action’: Users can override the current action prediction with the manual specification of one action. If users choose this response, they are first asked to choose one action from the prepared action list and then fill in the parameters manually. The LLM agent directly executes the user-specified action.
After one action is executed, if users are not satisfied with the results, they can choose to re-execute this step by providing text feedback (i.e., by clicking button ‘Give feedback and try again’), which works similarly to the ‘Feedback’ option.
If users are satisfied with the execution results, they can click the ‘Next Step’ button and move to execute the next primary step.
By iterating over this process through the step-wise plan, users can choose to either approve or get involved in modifying the execution outcomes in each step. All actions are predicted and executed in the backend (i.e., the respective API calls are triggered).

#### Hypotheses

Our experiment is designed to answer questions of how human involvement in the planning and execution stages will shape their trust and overall task performance.
To analyze such impact, we regulate the levels of automation in the LLM agent through the planning and execution stage as baselines for comparison.
The automatic planning and execution denotes that the LLM agent directly generates the task outcomes without user involvement.

With user involvement in the planning stage, users have the opportunity to fix potential mistakes or issues in the plan generated by LLMs.
Working on such plan editing tasks is similar to debugging, which has been argued to bring about a critical mindset (He et al., 2024a) to the generated plan.
With a critical mindset, users may better calibrate their trust in the planning outcome.
We also consider user involvement in planning to be beneficial to the plan quality, which can then contribute to the overall task performance.
Thus, we hypothesize that:

(H1): Compared to automatic planning, user-involved planning will result in a higher calibrated trust in the plan.
(H2): Compared to automatic planning, user-involved planning will result in better overall task performance.

In the user-involved execution process, users manually check the action prediction and execution results of each primary step.
Such user involvement increases the chances of discovering potential mistakes of LLM agents.
Once users realize that the LLM agent made mistakes, they can get involved in modifying the execution outcome of the current step.
By fixing these mistakes, the overall task performance gets improved.
With such involvement in fixing potential errors, users will be more critical of trusting the task outcome.
Therefore, we hypothesize that:

(H3): Compared to automatic execution, user-involved execution will result in a higher calibrated trust in execution outcome.
(H4): Compared to automatic execution, user-involved execution will result in better overall task performance.

### Study Design

This section describes our experimental conditions, tasks, variables, procedure, and participants in our study. Our
study was approved by the human research ethics committee of our institution.

#### Experimental Conditions

In our study, users collaborate with LLM agent-based daily assistants in two stages: planning and execution.
To comprehensively understand the effect of user involvement at each stage, we considered a 2 × 2 factorial design with four experimental conditions: (1) automatic planning, automatic execution (represented as AP-AE), (2) automatic planning, user-involved execution (represented as AP-UE), (3) user-involved planning, automatic execution (represented as UP-AE), (4) user-involved planning, user-involved execution (represented as UP-UE).
In conditions with user-involved planning, users are allowed to edit the plan generated by LLM with the actions of edit/add/delete/split step.
By comparison, in conditions with automatic planning, users will directly adopt the plan generated by the daily assistant.
In conditions with user-involved execution, users can interact with the step-by-step execution LLM agent (cf. Section 3.3) and refine execution results with text feedback or manual specification.
By comparison, in conditions with automatic execution, users will directly accept the automatic execution results.

#### Tasks

To analyze how LLM agents can serve as daily assistants, we adopted tasks from a planning dataset designed for LLM agents — UltraTool (Huang et al., 2024).
We selected daily scenarios: currency transactions, credit card payments, repair service appointments, alarm setting, flight ticket booking, and trip itinerary planning.
The selected tasks are shown in Table 1. For more details about how the plan-then-execute LLM agent works on the selected tasks (e.g., automatic plan, pre-defined actions, automatic evaluation, and explanation for errors in automation), please refer to the appendix.
All tasks in UltraTool dataset are annotated with the step-wise plan format described in Section 3.2. The execution of these tasks is based on a simulation environment (described in Section 3.3) where all required actions are implemented as backend APIs.
In our study, all tasks are executed in a simulation setup, which has been a popular method for orchestrating meaningful human-centered AI studies (Doshi-Velez and Kim, 2017; Salimzadeh et al., 2024).

Task Selection. First, based on the domain distribution of the UltraTool dataset, we selected seven domains: Finance, Alarm, Travel, Tracking, Restaurant, Flight, and Repair.
For each domain, we only consider tasks that contain more than ten steps (including all sub-steps) and require at least three uses of actions.
Then, we manually selected ten tasks: four from the finance domain and one for each of the others.
With a pilot study, we tested how users work on the ten tasks.
We recruited 10 participants from the Prolific platform and only considered the feedback of 9 participants who passed all attention checks.
Using the question “How much risk do you perceive in this task when relying on this daily AI assistant?”, we collected the perceived risk of working with the LLM agents on each task using a 5-point Likert scale, ranging from 1: not risky at all—to—5:very risky. We categorize the ten tasks into a high-risk group (top 5) and a low-risk group (bottom 5).
We selected three tasks from each group while balancing the complexity of the task description (three simple tasks and three complex tasks) and the correctness of the provided plan (three correct plans and three imperfect plans).
Based on existing literature on task complexity (Wood, 1986; Salimzadeh et al., 2023), we considered component complexity to inform our selection.
This is assessed as the ‘total number of distinct information cues that need to be processed to perform the task’.
Here, we considered the number of unique actions and the number of named concepts provided in each task.
According to prior work (Miller, 1956), most people can only handle 5 to 9 concepts at the same time.
The component complexity of all complex tasks in our study is more than nine.
The six tasks selected are shown in Table 1.
Besides the six tasks, we used one simple task (i.e., checking bank account balance) as the example in the onboarding tutorial.

#### Measures and Variables

The variables and measures used in our study refer to existing empirical studies of human-AI collaboration (Lai et al., 2023).
All measures adopted in our study can be summarized in Table 2.

Calibrated Trust. To assess calibrated trust in the planning stage and execution stage, we assessed user trust at each stage with a question “Do you trust that [the execution of this plan / the execution process] can provide a correct outcome based on the task instructions?”.
Based on the plan quality evaluation (5-point Likert), the calibrated trust in the planning (CTp) is calculated based on the frequency at which users trusted the high-quality plan (expert annotation with 5) and users distrusted the plan with other evaluation results.
Similarly, for the calibrated trust in execution (CTe), we calculated the frequency at which users trusted the correct execution results and distrusted the wrong execution results.
The two measures can be calculated as:

To assess the task performance, we mainly considered the task outcome from the planning and execution stages.

Plan Quality. As for the planning outcome, we evaluate the plan quality based on a 5-point Likert scale:
1. low-quality plan, task requirements not covered;
2. low-quality plan, task requirements covered but with grammar errors;
3. medium-quality plan, task requirement covered but with at least one action intent mismatch with ground truth action sequence;
4. medium-quality plan, task requirements covered but miss or have wrong details for action parameters;
5. high-quality plan, covering all task requirements and providing all necessary details.

Execution Performance.
The execution of the step-wise plan will result in an action sequence.
We provide a ground truth action sequence as a reference to evaluate the generated action sequence.
We measure the action sequence accuracy (ACCs) as the strict match of the action sequence and ground truth.
Meanwhile, if one action sequence contains some redundant actions that are not harmful (e.g., searching for flights), the execution results should still be correct.
Thus, we also consider execution accuracy (ACCe) as a task performance measure.

Subjective Trust and Covariates. To enrich our analysis of user trust, we followed existing work to adopt the six subscales from the Trust-in-automation questionnaire (Körber, 2019).
The four subscales — Reliability/Competence, Understanding/Predictability, Intention of Developers, Trust in Automation are used as subjective measures of user trust in the LLM agent.
Meanwhile, the Familiarity and Propensity to Trust are also used as covariates. Besides them, we considered user expertise in LLMs and user expertise in automatic assistants as covariates.

Exploratory Variables. To enrich our understanding of LLM agent as daily assistant, we assessed user confidence (both planning and execution) and risk perception along with each task.
After users finish the study, we also ask for their open-text feedback on the planning and execution stages as well as other comments.
To check the cognitive load of user involvement in our study, we adopted the NASA-TLX questionnaire (Colligan et al., 2015), which contains six subscales.

#### Participants

Sample Size Estimation.
To ensure sufficient statistical power, we estimated the required sample size for a 2 × 2 factorial design based on G*Power (Faul et al., 2009).
To correct for testing multiple hypotheses, we applied a Bonferroni correction so that the significance threshold decreased to $\frac{0.05}{4}=0.0125$.
We specified the default effect size $f=0.25$
(i.e., indicating a moderate effect), a significance threshold $\alpha=0.0125$ (i.e., due to testing multiple hypotheses), a statistical power of $(1-\beta)=0.8$, and that we will investigate $4$ different experimental conditions/groups.
This resulted in a required sample size of $244$ participants.
We thereby recruited 347 participants from the crowdsourcing platform Prolific77https://www.prolific.co, to accommodate potential exclusion.

Compensation. All participants were rewarded with an hourly wage of £8.1 deemed to be “Fair” payment by the platform (estimated completion time was 30 minutes).
As participants in condition UP-UE spent longer in the study, we paid each participant a commensurate bonus accounting for an extra 10 minutes. We rewarded participants with extra bonuses of £0.05 for every high-quality plan and correct execution result.
According to existing literature (Lee and See, 2004), such a bonus setup can help incentivize participants to reach a correct decision.
In comparison with existing literature exploring human-AI decision making (Lai et al., 2023), our reward setup is above the average payment and can be considered as being sufficient to elicit ecologically valid behavior among participants (i.e., aiming to arrive at accurate execution results). Moreover, similar bonus structures akin to our setup have been effective in incentivizing reliable participant behavior and improving data quality across different studies with crowdsourced participants (Fan et al., 2020; Salimzadeh et al., 2024; Li and Yin, [n. d.]; Ma et al., 2024b).

Filter Criteria. All participants were proficient English speakers between the ages of 18 - 50.
We also constrained their prior experience (at least 40 successful submissions) and had an approval rate of above 90% on the Prolific platform.
We excluded participants from our analysis if they failed any attention check, or represented an outlier regarding the plan quality.
Outliers were 4 participants who generated more than three low-quality plans among six tasks.
The reserved 248 participants had an average age of 32.5 ($SD$= 8.1) and a balanced gender distribution
($50\%$, $49.6\%$ female, $0.4\%$ other).

#### Procedure

At the beginning of our study, we showed informed consent for data collection and the study’s purpose.
Only participants who signed the informed consent were allowed to continue to work on our study.
Next, participants were asked to complete a pre-task questionnaire to measure their expertise in LLM and automatic assistants.

Participants were then assigned to one of the experimental conditions, which differed in the level of user involvement in the planning stage and execution stage.
With an onboarding tutorial, we showcased the necessary interactions that participants were expected to perform in the planning and execution stages.
We used an example task to help participants understand how to work with the plan-then-execute LLM agent.
After the onboarding tutorial, participants worked on the selected tasks, which were shuffled at random for every participant to prevent task ordering effects.
After the participants finished the task batch, we measured their perceived cognitive load using the NASA-TLX questionnaire (Colligan et al., 2015), their overall trust in the daily assistant using the trust in automation questionnaire (Körber, 2019), and we gathered their feedback on our system (related to planning, execution, and other aspects) using open-ended text.

### Results

In this section, we will present the main experimental results and exploratory analysis for our study.

#### Descriptive Statistics

In total, our analysis is based on 248 participants, who are balanced across conditions: AP-AE (63), AP-UE (64), UP-AE (61), and UP-UE (60).
All edited plans in user-involved planning conditions are evaluated by the authors following the plan quality criteria described in Section 4.3.

Distribution of Covariates. In our study, most participants claimed to have some experience with using large language models ($M=3.6,SD=1.0$) and automatic assistants ($M=3.4,SD=1.1$). In the trust in automation questionnaire, participants indicated a medium level of Familiarity ($M=2.9,SD=1.2$) and Propensity to Trust ($M=3.0,SD=0.7$).

Performance Overview. Overall, users show calibrated trust in the planning ($M=0.50,SD=0.13$) and calibrated trust in the execution ($M=0.64,SD=0.19$).
For the execution outcome, we find that although it is tricky to obtain a ground truth action sequence ($M=0.48,SD=0.17$), the action sequence has a relatively high recall of ground truth actions ($M=0.77,SD=0.11$). The successful rate for correct execution ($M=0.52,SD=0.18$) is higher than the strict evaluation of the action sequence.
We also collected user subjective trust with four subscales of the trust in automation questionnaire: Reliability/Competence ($M=3.49,SD=0.77$), Understanding/Predictability ($M=3.30,SD=0.56$), Intention of Developers ($M=3.61,SD=0.81$), Trust in Automation ($M=3.52,SD=1.01$).
With a two-way ANOVA analysis considering user involvement in planning and execution, we do not find any significant impact of user involvement on subjective user trust in AI systems across conditions.

Cognitive Load. The cognitive load of participants across the four experimental conditions is shown in Figure 4.
Based on two-way ANOVA, we analyzed the impact of user involvement in planning and execution affect user cognitive load.
User involvement in planning shows a significant impact on Mental Demand, Temporal Demand, and Frustration. User involvement in execution shows a significant impact on Performance and Effort.
With post-hoc Tukey HSD test, we confirmed such impact — involvement in both planning and execution posed a higher cognitive load on participants.

User Involvement. Among 121 participants in conditions with user-involved planning, 104 participants edited at least one task plan. Meanwhile, 90 participants used the provided buttons (i.e., add/delete/split step) in our study. In total, delete step is used 394 times, add step is used 183 times, split step is used 126 times. Among 124 participants in conditions with user-involved execution, 114 participants interacted with the conversation interface to change action prediction (i.e., have at least one task where they choose to give feedback or override predicted action).
Meanwhile, 105 participants specified at least one action in the task batch.
In total, Specify Action is used 445 times, feedback to the LLM agent is used 91 times before action execution, and feedback to the LLM agent is used 163 times after execution.

#### Hypothesis Verification

As the tasks selected in our study are of different initial plan quality and risk levels, we conducted a task-specific analysis in each hypothesis verification.

###### The Impact of User Involvement in Planning on Calibrated Trust

To verify H1, we adopted the one-way ANOVA test and post-hoc Tukey HSD test on the calibrated user trust in planning (i.e., CTp).
The results are shown in Table 3.
Only in task-4, we found user involvement in planning will have a negative impact on calibrated trust in planning.
To avoid a potential impact of user involvement in the execution stage, we conducted a two-way ANOVA test to confirm the findings.
We only find a significant difference in task-4.
Post-hoc Tukey HSD results show that participants in conditions with automatic planning (AP) showed significantly higher calibrated trust in planning outcomes than those in conditions with user-involved planning (UP).
Thus, our experimental results do not support H1.

We noticed that the calibrated trust in planning is quite low in the high-risk tasks where all initial plans are imperfect.
This indicates that many users across all conditions consider the generated plan trustworthy.
On tasks with low risk, where the initial plan is of high quality, users achieved much higher calibrated trust in the planning outcome.
We also find that conditions with user-involved execution (UE) show slightly higher CTp in task-1 and task-4 than conditions with automatic execution (AE). With the same statistical test as H1 analysis, such differences are not significant.

###### The Impact of User Involvement in Planning on Task Performance

To verify H2, we considered plan quality, the accuracy of action sequences (ACCs), and the execution accuracy of the plan (ACCe) for analysis.
For plan quality (cf. Table 3), we conducted one-way ANOVA on plan quality considering the user involvement in the planning stage.
We found that overall user involvement in the planning stage caused a decrease plan quality, especially on tasks with a perfect plan (i.e., task 4, 5, 6, where plan quality = 5) and task-3.
However, in task-1, where the original plan contains a grammar error, we find that user involvement in planning can improve the plan quality.
As the action sequence accuracy (ACCs) and execution accuracy (ACCe) are not normally distributed, we conducted the Kruskal-Wallis H-test by considering the user involvement in the planning as the independent variable. The results are shown in Table 4.
With further post-hoc Mann-Whitney tests, we found that while participants achieved a relatively higher accuracy of action sequences in condition AP-AE, the condition UP-UE achieved the best execution accuracy.
In most tasks, condition UP-UE achieved better or compatible performance as other conditions. The only exception is task-4, where user involvement in the planning caused a significantly worse performance (both ACCs and ACCe).
As user involvement does not consistently lead to improved performance, these results are not enough to support H2.

We found that in task-1 and task-6 most participants in the AP-AE condition achieved a very low success rate. This is mainly due to the imperfect plans and imperfect execution generated by LLMs.
In task-1, the plan generated by LLMs includes one step which contains two actions to execute.
Due to the inability to edit the plan, the LLM agent execution missed one transaction in conditions with automatic planning.
In task-6, the plan generated by LLMs is correct.
However, in the automatic execution of step 2 of the plan (i.e., selecting an itinerary suggested), the LLM agent has a high probability of choosing an itinerary that does not match the task description.
If the participants do not carefully check the task description, and correct this agent behavior, the execution results would be wrong.
This also helps explain why user involvement substantially improves the task outcome accuracy in task-6. More details about tasks can be found in the appendix.

###### The Impact of User Involvement in Execution on Calibrated Trust in Execution Outcome

As we observe in Table 3, user involvement in planning can have some negative impact on the plan quality, which further impacts the execution stage.
To control such impact, we filtered out the tasks where plan quality decreased after user-involved planning in the analysis of user involvement in the execution stage.
To verify H3, we conducted one-way ANOVA on calibrated trust in execution outcome (CTe). The results are shown in Table 6.
We found that user involvement in execution causes no significant difference across conditions.
Thus, H3 is not supported by our experimental results.

###### The Impact of User Involvement on Overall Task Performance

Similar to the verification of H3, we excluded the tasks where plan quality decreased after user-involved planning in this analysis.
As the plan is generated before user involvement in the execution, we only considered ACCs and ACCe in the analysis of user involvement in the execution stage.
To verify H4, we conducted Kruskal-Wallis H-test by considering the user involvement in the execution as the independent variable. The results are shown in Table 5.
With post-hoc Mann-Whitney tests, we found that user involvement in the execution stage showed significantly higher ACCs and ACCe in task-6 (where the LLM assistant mainly failed to choose the most suitable itinerary plan).
We found that participants in the AP-AE condition achieved the best accuracy of action sequences (i.e., ACCs), and participants in condition UP-UE achieved the best execution accuracy (i.e., ACCe).
In other words, the executed action sequence in condition AP-AE is more aligned with the ground truth action sequence annotated by the authors.
However, with user involvement in the execution stage, participants in condition UP-UE have a better opportunity to obtain correct task outcomes by correcting potentially flawed actions.
Such a difference is due to our measure of ACCe, which tolerates the non-risky actions (e.g., search flight) and failure of action predictions.
In contrast, our measure of ACCs considers this as a wrong action sequence.
 Thus, in task-3, even if we find automatic execution achieved significantly better ACCs than user-involved execution, participants in condition AP-UE and UP-UE obtained comparable or higher execution accuracy (i.e., ACCe) than conditions with automatic execution.
While user involvement shows some positive impact on the execution accuracy, such impact is not significant and consistent across all tasks.
Only in task-6, where users can correct the errors made by the LLM agent (i.e., the wrong itinerary selection mentioned in Section 5.2.2), user involvement in the execution shows a significant contribution to the task performance.
Thus, these results are not enough to strictly support H4.

#### Exploratory Analysis

###### The Impact of Covariates

For further insights into all user factors on user trust and team performance, we calculated Spearman rank-order correlation coefficients for user trust, calibrated trust, risk perception, and task performance.
As can be seen in Table 7, we found these covariates mainly show correlations with subjective user trust, calibrated trust in execution, and risk perception.
First, all covariates (i.e., user factors) positively correlated with user trust (four subscales in the trust in automation questionnaire (Körber, 2019)) and negatively correlated with perceived risk (average over six tasks).
It indicates that users with more expertise or familiarity with such systems tend to trust the daily assistant and show less perceived risk when using it.
Meanwhile, users with a general propensity to trust also tend to trust the AI system.
Besides user trust, Assistant Expertise and Propensity to Trust show a significant negative correlation with calibrated trust in the execution outcome.
Apart from the above correlation, these user factors do not significantly correlate with task performance measures or calibrated trust in the planning outcome.

###### Impact of Plan Quality and Risk Percetion.

Besides the measures calculated over task batch, a task-level
analysis of plan quality and risk perception can deepen our understanding of their impacts.
Besides measures adopted in Table 7, we include task-level confidence in this analysis and exclude the subscales from the trust in automation questionnaire.
Thus, we calculated Spearman rank-order correlation coefficients for task-level measures across all groups of participants (shown in Table 8).
As we can see, both plan quality and risk perception significantly correlate with user trust, calibrated trust, task performance, and user confidence.
The plan quality shows a significant positive correlation with most measures, which indicates users perform better and calibrate their trust in the LLM agents in tasks with a high-quality plan.
By contrast, the risk perceptions shows a negative correlation with most measures and also a negative correlation with the plan quality.

###### Failure Analysis

As we find that plan quality substantially affects task execution accuracy, we look into task performance across different plan qualities.
For the tasks with low-quality plans (plans fail to cover task information or plan with grammar errors, i.e., plan quality=1, 2), the execution accuracy is $1.8\%$.
While for tasks with a plan that may mislead action prediction (plan quality = 3, 4), our LLM agent-based daily assistant achieved $59\%$ execution accuracy.
The average execution accuracy for tasks with a high-quality plan (plan quality =5) is $66.7\%$.

We further check 717 tasks where a high-quality plan (plan quality = 5) is provided. Among them, 235 tasks provide wrong execution results. The main causes are:
(1) Wrong action parameter prediction ($48.9\%$).
While action names match, one or more parameters mismatch the expected value at some step of the action sequence.
(2) Invalid actions ($48.5\%$). Given a perfect plan, the LLM agent failed to predict one valid action (failed to predict one action name or failed to predict some action parameter value) to execute in some steps.
(3) Wrong action name prediction ($2.6\%$). The generated action sequence has at least one action name prediction that mismatches the ground truth.

###### Confidence Dynamics

To visualize the user confidence in the planning and execution stage, we draw point plots (see Figure 5) for user confidence in the task order.
Overall, condition AP-AE shows the highest confidence in both the planning and execution stages.
To verify the impact of user involvement in confidence, we adopted two-way ANOVA and post-hoc Tukey HSD test.
We find that: (1) with user involvement in the planning, participants showed significantly lower confidence in planning (AP-AE ¿ UP-AE, UP-UE); (2) with user involvement in the execution, participants showed a significantly lower confidence in execution (AP-AE ¿ AP-UE, UP-UE).
Meanwhile, users typically showed a higher confidence in the execution stage.
Compared with conditions with automation execution (i.e., condition AP-AE and UP-AE), the confidence gap narrows down in the conditions with user-involved execution (i.e., condition AP-UE and UP-UE).

#### Analysis of Open Feedback

At the end of our study, we collected open feedback regarding the planning stage, execution stage, and any other feedback using the following question: ‘Please share any comments, remarks or suggestions regarding the planning/execution stage of LLM Assistant’ and ‘Do you have any other comments, remarks or suggestions regarding the study?’.
Overall, we analyzed all the feedback based on user opinions (positive, negative, mixed, neutral) and their suggestions.
In our analysis, we ignored all phrases without any useful information like ‘None’, ‘N/A’, and ‘No comment’.

Feedback and Suggestions. While most comments tended to show positive opinions (more than $80\%$) towards LLM agents as daily assistants, there are also negative opinions regarding the difficulty, expertise, trust, etc. We provide example excerpts from participants in Table 9. Besides opinions towards the system, some participants also appreciated our user-centric setup:”The study does a good job of emphasizing user experience by asking about perceptions of risk, trust, and confidence. This approach ensures that the evaluation is user-centric, which is important for assessing the real-world applicability of the LLM Assistant.”

Some participants also provided suggestions on how to further improve the design of LLM agent-based daily assistants.
Regarding the plan edit, participants hope we can provide more convenient edit operations like ‘drop/drag’ to adjust plan text ordering and ‘undo’ operation to tolerate unexpected mistakes.
Some participants also found the plans too detailed, which could increase the cognitive load (cf. Table 9 except 3).
As for the execution, many participants found it to be smooth. At the same time, they think additional verification in each step may further enhance the reliability of daily assistants: “For the execution stage, I commend it for creating an input formatting box to execute the user’s request validating each requirement.”
There are also comments about the whole plan-then-execute workflow: “The planning was really challenging, and I mostly left the default plans (they looked fine).
This worked in the main, but a couple clearly needed revisiting. I would approach this iteratively: plan, test, observe, back to planning, then another test, before reaching the desired outcome.” Our findings suggest open research opportunities to explore more effective ways to provide an overview of plans that trade-off user cognitive load resulting from granular descriptions, with the need to provide details to help users identify flaws. For example, we can consider developing methods to interactively allow users to flesh out further details in a plan.

##### The Impact of User Involvement in Planning on Calibrated Trust

To verify H1, we adopted the one-way ANOVA test and post-hoc Tukey HSD test on the calibrated user trust in planning (i.e., CTp).
The results are shown in Table 3.
Only in task-4, we found user involvement in planning will have a negative impact on calibrated trust in planning.
To avoid a potential impact of user involvement in the execution stage, we conducted a two-way ANOVA test to confirm the findings.
We only find a significant difference in task-4.
Post-hoc Tukey HSD results show that participants in conditions with automatic planning (AP) showed significantly higher calibrated trust in planning outcomes than those in conditions with user-involved planning (UP).
Thus, our experimental results do not support H1.

We noticed that the calibrated trust in planning is quite low in the high-risk tasks where all initial plans are imperfect.
This indicates that many users across all conditions consider the generated plan trustworthy.
On tasks with low risk, where the initial plan is of high quality, users achieved much higher calibrated trust in the planning outcome.
We also find that conditions with user-involved execution (UE) show slightly higher CTp in task-1 and task-4 than conditions with automatic execution (AE). With the same statistical test as H1 analysis, such differences are not significant.

##### The Impact of User Involvement in Planning on Task Performance

To verify H2, we considered plan quality, the accuracy of action sequences (ACCs), and the execution accuracy of the plan (ACCe) for analysis.
For plan quality (cf. Table 3), we conducted one-way ANOVA on plan quality considering the user involvement in the planning stage.
We found that overall user involvement in the planning stage caused a decrease plan quality, especially on tasks with a perfect plan (i.e., task 4, 5, 6, where plan quality = 5) and task-3.
However, in task-1, where the original plan contains a grammar error, we find that user involvement in planning can improve the plan quality.
As the action sequence accuracy (ACCs) and execution accuracy (ACCe) are not normally distributed, we conducted the Kruskal-Wallis H-test by considering the user involvement in the planning as the independent variable. The results are shown in Table 4.
With further post-hoc Mann-Whitney tests, we found that while participants achieved a relatively higher accuracy of action sequences in condition AP-AE, the condition UP-UE achieved the best execution accuracy.
In most tasks, condition UP-UE achieved better or compatible performance as other conditions. The only exception is task-4, where user involvement in the planning caused a significantly worse performance (both ACCs and ACCe).
As user involvement does not consistently lead to improved performance, these results are not enough to support H2.

We found that in task-1 and task-6 most participants in the AP-AE condition achieved a very low success rate. This is mainly due to the imperfect plans and imperfect execution generated by LLMs.
In task-1, the plan generated by LLMs includes one step which contains two actions to execute.
Due to the inability to edit the plan, the LLM agent execution missed one transaction in conditions with automatic planning.
In task-6, the plan generated by LLMs is correct.
However, in the automatic execution of step 2 of the plan (i.e., selecting an itinerary suggested), the LLM agent has a high probability of choosing an itinerary that does not match the task description.
If the participants do not carefully check the task description, and correct this agent behavior, the execution results would be wrong.
This also helps explain why user involvement substantially improves the task outcome accuracy in task-6. More details about tasks can be found in the appendix.

##### The Impact of User Involvement in Execution on Calibrated Trust in Execution Outcome

As we observe in Table 3, user involvement in planning can have some negative impact on the plan quality, which further impacts the execution stage.
To control such impact, we filtered out the tasks where plan quality decreased after user-involved planning in the analysis of user involvement in the execution stage.
To verify H3, we conducted one-way ANOVA on calibrated trust in execution outcome (CTe). The results are shown in Table 6.
We found that user involvement in execution causes no significant difference across conditions.
Thus, H3 is not supported by our experimental results.

##### The Impact of User Involvement on Overall Task Performance

Similar to the verification of H3, we excluded the tasks where plan quality decreased after user-involved planning in this analysis.
As the plan is generated before user involvement in the execution, we only considered ACCs and ACCe in the analysis of user involvement in the execution stage.
To verify H4, we conducted Kruskal-Wallis H-test by considering the user involvement in the execution as the independent variable. The results are shown in Table 5.
With post-hoc Mann-Whitney tests, we found that user involvement in the execution stage showed significantly higher ACCs and ACCe in task-6 (where the LLM assistant mainly failed to choose the most suitable itinerary plan).
We found that participants in the AP-AE condition achieved the best accuracy of action sequences (i.e., ACCs), and participants in condition UP-UE achieved the best execution accuracy (i.e., ACCe).
In other words, the executed action sequence in condition AP-AE is more aligned with the ground truth action sequence annotated by the authors.
However, with user involvement in the execution stage, participants in condition UP-UE have a better opportunity to obtain correct task outcomes by correcting potentially flawed actions.
Such a difference is due to our measure of ACCe, which tolerates the non-risky actions (e.g., search flight) and failure of action predictions.
In contrast, our measure of ACCs considers this as a wrong action sequence.
 Thus, in task-3, even if we find automatic execution achieved significantly better ACCs than user-involved execution, participants in condition AP-UE and UP-UE obtained comparable or higher execution accuracy (i.e., ACCe) than conditions with automatic execution.
While user involvement shows some positive impact on the execution accuracy, such impact is not significant and consistent across all tasks.
Only in task-6, where users can correct the errors made by the LLM agent (i.e., the wrong itinerary selection mentioned in Section 5.2.2), user involvement in the execution shows a significant contribution to the task performance.
Thus, these results are not enough to strictly support H4.

##### The Impact of Covariates

For further insights into all user factors on user trust and team performance, we calculated Spearman rank-order correlation coefficients for user trust, calibrated trust, risk perception, and task performance.
As can be seen in Table 7, we found these covariates mainly show correlations with subjective user trust, calibrated trust in execution, and risk perception.
First, all covariates (i.e., user factors) positively correlated with user trust (four subscales in the trust in automation questionnaire (Körber, 2019)) and negatively correlated with perceived risk (average over six tasks).
It indicates that users with more expertise or familiarity with such systems tend to trust the daily assistant and show less perceived risk when using it.
Meanwhile, users with a general propensity to trust also tend to trust the AI system.
Besides user trust, Assistant Expertise and Propensity to Trust show a significant negative correlation with calibrated trust in the execution outcome.
Apart from the above correlation, these user factors do not significantly correlate with task performance measures or calibrated trust in the planning outcome.

##### Impact of Plan Quality and Risk Percetion.

Besides the measures calculated over task batch, a task-level
analysis of plan quality and risk perception can deepen our understanding of their impacts.
Besides measures adopted in Table 7, we include task-level confidence in this analysis and exclude the subscales from the trust in automation questionnaire.
Thus, we calculated Spearman rank-order correlation coefficients for task-level measures across all groups of participants (shown in Table 8).
As we can see, both plan quality and risk perception significantly correlate with user trust, calibrated trust, task performance, and user confidence.
The plan quality shows a significant positive correlation with most measures, which indicates users perform better and calibrate their trust in the LLM agents in tasks with a high-quality plan.
By contrast, the risk perceptions shows a negative correlation with most measures and also a negative correlation with the plan quality.

##### Failure Analysis

As we find that plan quality substantially affects task execution accuracy, we look into task performance across different plan qualities.
For the tasks with low-quality plans (plans fail to cover task information or plan with grammar errors, i.e., plan quality=1, 2), the execution accuracy is $1.8\%$.
While for tasks with a plan that may mislead action prediction (plan quality = 3, 4), our LLM agent-based daily assistant achieved $59\%$ execution accuracy.
The average execution accuracy for tasks with a high-quality plan (plan quality =5) is $66.7\%$.

We further check 717 tasks where a high-quality plan (plan quality = 5) is provided. Among them, 235 tasks provide wrong execution results. The main causes are:
(1) Wrong action parameter prediction ($48.9\%$).
While action names match, one or more parameters mismatch the expected value at some step of the action sequence.
(2) Invalid actions ($48.5\%$). Given a perfect plan, the LLM agent failed to predict one valid action (failed to predict one action name or failed to predict some action parameter value) to execute in some steps.
(3) Wrong action name prediction ($2.6\%$). The generated action sequence has at least one action name prediction that mismatches the ground truth.

##### Confidence Dynamics

To visualize the user confidence in the planning and execution stage, we draw point plots (see Figure 5) for user confidence in the task order.
Overall, condition AP-AE shows the highest confidence in both the planning and execution stages.
To verify the impact of user involvement in confidence, we adopted two-way ANOVA and post-hoc Tukey HSD test.
We find that: (1) with user involvement in the planning, participants showed significantly lower confidence in planning (AP-AE ¿ UP-AE, UP-UE); (2) with user involvement in the execution, participants showed a significantly lower confidence in execution (AP-AE ¿ AP-UE, UP-UE).
Meanwhile, users typically showed a higher confidence in the execution stage.
Compared with conditions with automation execution (i.e., condition AP-AE and UP-AE), the confidence gap narrows down in the conditions with user-involved execution (i.e., condition AP-UE and UP-UE).

### Discussion

#### Key Findings

Our experimental results show that user involvement in the plan-then-execute workflow with LLM agents can help fix imperfect plans in planning and wrong action predictions in the step-by-step execution.
However, user involvement does not ensure a consistently positive impact on calibrated trust and overall task performance across different tasks.

User Involvement Fails to Calibrate User Trust.
Overall, user involvement in the planning and execution does not significantly impact user trust and calibrated trust in planning and execution outcomes.
As Table 3 shows, user involvement in planning can harm plan quality in tasks with a high-quality initial plan, which may potentially cause worse task performance in the subsequent execution stage.
Our experimental results do not support H1 or H3, which indicates user involvement does not necessarily help calibrate user trust in our study.
Instead, with a task-specific correlation analysis (cf. Table 8), we found that the plan quality has a significant positive correlation with calibrated trust in both planning and execution outcomes.
Combined with task-specific user trust and task-specific confidence, we can infer that users tend to trust the LLM agent overall.
Such trust can be expected and calibrated in tasks with a high-quality plan.
In contrast, users fail to calibrate their trust in the tasks where a low-quality plan is provided. A potential cause of such miscalibrated trust is the plausibility of plans generated by LLMs (i.e., plans that appear to be likely correct).
In our study, all initial plans are formulated with a clear, logical structure, which covers most of the task requirements.
At first glance, such high-quality text pieces seem quite plausible and trustworthy.
We also received some open text feedback such as, — “The plans look nice, I do not find any space for improvement” and “the planning stage of the LLM assistant was helpful and trustworthy.”
Findings from recent work on LLM-assisted fact checking corroborate this, wherein authors found that convincing explanations provided by LLMs can cause over-reliance when LLMs are wrong (Si et al., 2024).

User Involvement can Benefit Task Performance.
User involvement in planning and execution can positively impact overall task performance, especially execution accuracy.
As the results in Table 3 and Table 4 show, user involvement in planning can help address imperfect plans (e.g., task-1 with grammar error). Doing so further contributes to improvements in the execution accuracy.
After controlling the plan quality, we found that user involvement in the execution can provide the best execution accuracy among most tasks considered in our study (cf. Table 5).
Based on the failure analysis (Section 5.3.3), LLM agents can make mistakes in executing high-quality plans, which can be attributed to prediction errors (i.e., wrong action name or action parameters) and prediction failures (i.e., failure to provide valid action prediction).
In practice with deployed LLM services, there is no reliability guarantee for the generated plan in planning or predicted actions in execution.
User involvement can play an important role in the plan quality control and risky action control, ensuring that only correct and safe actions are executed to obtain desirable task outcomes.

Other Findings. We also found some user factors and perceptions that affect user trust and task performance.
As seen in Table 7, nearly all covariates show a significant positive correlation with user trust in the AI system.
Some of these covariates also impact user trust in the planning and execution outcomes.
Overall, these findings indicate that users who are familiar with such systems tend to show higher user trust.
However, some factors also correlate negatively with the calibrated trust in the execution outcomes and risk perception of using the LLM agents as daily assistants.
This reflects that these factors can cause miscalibrated trust and reduced risk perception when working with the LLM agent.
While we found that risk perception negatively correlated with user trust, calibrated trust, task performance, and confidence (cf. Table 8), it does not mean risk perception is harmful in the human-LLM agent collaboration.
The main cause is that users may only notice the risks of using LLM agents when the task is provided with a relatively low-quality plan.
Risk perception is important to calibrate user trust in the planning and execution outcomes. Collaborative workflows should support users with the provision to take over control of planning and/or execution stages based on their perceived risk.

#### Implications

The Impact of Convincingly Wrong LLM Outcomes.
As our study follows a plan-then-execute workflow for users to collaborate with LLM agents, users were not offered a chance to revise the plan after starting with execution.
Users following a wrong plan can lead to negative outcomes. Combined with existing work on algorithm aversion (Dietvorst et al., 2015) and the impact of negative first impressions on user trust (Tolmeijer et al., 2021), we can infer that such convincingly wrong content (Si et al., 2024) can bias user trust and reliance towards the extremes.
Before users take notice, they may develop an uncalibrated trust in the AI system, as observed through our findings in high-risk tasks (i.e., tasks 1,2,3) and corroborating work by Si et al. (2024).
As a result, users over-rely on AI assistance, which is misuse akin to behavior that resonates with algorithm appreciation (Logg et al., 2019).
Once users notice such phenomena, their trust in the LLM-based systems may sharply decrease, resulting in disuse due to algorithm aversion.
This can be a result of the misalignment between perceived AI performance and actual AI performance.
Existing human-AI collaboration literature has provided potential solutions for such problems, ranging from performance feedback interventions (He et al., 2023) to agreement-in-confidence heuristic (Lu and Yin, 2021; Pescetelli and Yeung, 2021).

Future work can combine these insights to explore effective interventions for user trust calibration with convincingly wrong LLM outcomes.

Insights for Effective Collaboration with Plan-then-execute LLM Agents.
Our work has important theoretical implications for effective human-AI collaboration with plan-then-execute LLM agents.
On the one hand, user involvement can be necessary to achieve complementary team performance.
Although LLM agents have shown promising planning and execution capabilities, they are never perfect due to probabilistic uncertainty.
With user involvement in the planning, users can fix imperfect plans with grammar errors (cf. Table 3 task-1).
With user involvement in the execution, users can fix uncertainty issues (e.g., LLM agent predicts invalid actions) and prevent risky actions (e.g., LLM agents choose an itinerary conflicting with task requirements, cf. Table 5, task-6).
On the other hand, user involvement may also bring uncertainty and even harm LLM agent performance.
In tasks where the LLM agent provides a high-quality plan (cf. task 4, 5, 6 in Table 3 and Table 4), user involvement can harm the plan quality, which further negatively impacts the execution accuracy.
Moreover, user involvement in planning and execution poses a significantly higher cognitive load on users (cf. Figure 4) and negatively impacts user confidence (cf. Figure 5).
Thus, too much human involvement in collaboration with plan-then-execute LLM agents can be undesirable.
User involvement in the execution process brings more consistent benefits than user involvement in the planning stage.
As suggested by the participants, iterative LLM agent simulation may be one potential way to decide when users should be involved.
The LLM agent may first conduct a plan-then-execute round to obtain a clear plan and execution results.
With humans checking the whole process and simulated outcomes, humans can decide whether to be involved in revising the plan or the execution process.
In this way, we can minimize user involvement while keeping highly effective task outcomes through LLM agents.

Human Oversight and Designing Flexible Collaborative Workflows.
In our study, we found that human oversight does not consistently lead to improved outcomes.
One potential cause can be the disparity between the planning and execution of LLM agents.
Specifically, it is unclear how one plan step will be transformed into one action. When users realize one plan step can be wrong during the execution stage, they may need to articulate it or manually override the agent action, posing a high cognitive load.
Even worse, when users realize the LLM agent missed one action due to limited steps designed in the plan (in task-1), they do not have a chance to change the plan or add one extra step.
To address such concerns, we may need a more flexible collaborative workflow where humans can fix planning and execution simultaneously.
In this way, users can exercise more flexible control over the workflow and the task outcomes.
For instance,
the action prediction from the LLM agent can be provided along with each step in the planning stage.
Users can thereby be informed of the potential impact of their edited plan, which provides more straightforward feedback and helps users adjust the plan according to the expected actions.

#### Caveats and Limitations

Limitations and Potentail Biases.
To ensure reliable task outcomes, humans are expected to fix imperfect plans (e.g., grammar errors, misleading action intents) in the planning stage.
However, not everyone in conditions UP-AE and UP-UE noticed such grammar errors and split the plan in task-1.
Similarly, not everyone in conditions AP-UE and UP-UE noticed that the LLM agent chose an itinerary that conflicted with task requirements.
As discussed earlier, LLM agents can generate plausible plans, which may mislead user trust in the planning and execution outcomes.
In that case, participants in our study may have easily ignored some convincingly wrong plan steps or execution actions.
In our study, one primary step in the plan is only transformed into a single action. In practice, LLM agents can generate multiple actions for one specific goal.
However, such action generation and execution modes are challenging for humans to get involved in and control, as the execution of the action sequences is automated by the LLM agent within one goal.
Furthermore, using multiple actions to achieve one primary step (i.e., goal) also results in higher task complexity and reduced task clarity, which may impact the task outcomes  (Gadiraju et al., 2017).

Transferability Concerns. Although we selected representative tasks for daily scenarios, our study may not be enough to cover all potential cases of daily assistance with LLM agents.
Some task characteristics (e.g., task complexity, time consumption) may also impact how users are willing to rely on AI assistance.
Meanwhile, full control over the plan-then-execute LLM agents may not be desirable for some simple tasks (e.g., setting alarms).
Once the efforts to control/interact with LLM agents are greater than the efforts to execute the tasks themselves, users will be unwilling to adopt such “assistance.”
Future work can look into what daily user needs are suitable for LLM agents to support.
In our study, the execution of plans is conducted in a simulation environment. While it has been proven to be effective in prior work of agent-based modeling and HCI studies (Olson and Kellogg, 2014), more work is needed to understand how execution of tasks in real-world environments with additional dependencies and complexities can influence our findings.

Participants in our study only followed a relatively fixed mode in collaboration with LLM agents, they can determine when to get involved in the planning and execution stages.
The experimental conditions considered in our study range from full automation (i.e., AP-AE) to full user control (i.e., UP-UE).
Such a setup provides good flexibility, which simulates real-world practice.
Our findings and implications provide valuable insights to guide future research on human-AI collaboration with LLM agents.

### Conclusion

This work empirically studied human-AI collaboration based on plan-then-execute LLM agents.
Adopting such LLM agents in various everyday scenarios, we analyzed the impact of user involvement in the planning and execution stages on user trust and overall task performance.
We provide various interactions in each stage to help users fix imperfect plans and modify execution outcomes.
Our results suggest that the LLM agents can provide plausible text plans to cover task requirements, which can be convincingly wrong.
As a result, users develop uncalibrated trust in the planning and execution outcomes, and user involvement in the planning and execution stages fails to calibrate user trust (RQ1).
We also found that the plan quality substantially affects the subsequent execution accuracy.
Thus, when user involvement in planning can fix imperfect plans, the overall task performance (i.e., plan quality, accuracy of action sequence, and execution accuracy) gets improved.
However, user involvement in planning can also harm task plan quality where the original plan is good to begin with. As a result, the LLM agents demonstrate worse task performance in these tasks.
In contrast, user involvement in execution brings a more stable positive impact on task performance (RQ2).
Our results suggest that plausible but wrong LLM outcomes can be detrimental to user trust calibration and overall task performance.
We discussed the impact of convincingly wrong LLM outcomes and provided potential solutions and insights for future work.
Furthermore, we synthesized key insights for better control and effective collaboration with plan-then-execute LLM agents. We also shed light on opportunities to design flexible collaborative workflows with human oversight for effective collaboration with LLM agents.

Our results indicate that user involvement in the LLM agent workflow can be important in ensuring reliable task outcomes.
Future work can further investigate how to detect and handle plausible but imperfect LLM outcomes and design effective interventions to fix such problems.
We hope that our key findings and implications reported in this work will inspire further research on human-AI collaboration with LLM agents.
