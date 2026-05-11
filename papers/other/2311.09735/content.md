# GEO: Generative Engine Optimization

**Authors:** Pranjal Aggarwal*♢ Vishvak Murahari* ♠ Tanmay Rajpurohit† Ashwin Kalyan‡ Karthik R Narasimhan♠ Ameet Deshpande♠ ♠♠\spadesuit Princeton University ††\dagger Georgia Tech ‡‡\ddagger The Allen Institute for AI ♢♢\diamondsuit IIT Delhi pranjal2041@gmail.com murahari@cs.princeton.edu

## Abstract

The advent of large language models (LLMs) has ushered in a new paradigm of search engines that use generative models to gather and summarize information to answer user queries. This emerging technology, which we formalize under the unified framework of generative engines (GEs), has the potential to generate accurate and personalized responses, and is rapidly replacing traditional search engines like Google and Bing. Generative Engines typically satisfy queries by synthesizing information from multiple sources and summarizing them with the help of LLMs. While this shift significantly improves user utility and generative search engine traffic, it results in a huge challenge for the third stakeholder – website and content creators. Given the black-box and fast-moving nature of generative engines, content creators have little to no control over when and how their content is displayed. With generative engines here to stay, the right tools should be provided to ensure that creator economy is not severely disadvantaged. To address this, we introduce Generative Engine Optimization (GEO), a novel paradigm to aid content creators in improving the visibility of their content in GE responses through a black-box optimization framework for optimizing and defining visibility metrics. We facilitate systematic evaluation in this new paradigm by introducing GEO-bench, a benchmark of diverse user queries across multiple domains, coupled with sources required to answer these queries. Through rigorous evaluation, we demonstrate that GEO can boost visibility by up to 40% in GE responses. Moreover, we show the efficacy of these strategies varies across domains, underscoring the need for domain-specific optimization methods. Our work opens a new frontier in the field of information discovery systems, with profound implications for both developers of GEs and content creators.111Code and data available at https://GEO-optim.github.io/GEO/. * Equal Contribution

### Introduction

The invention of traditional search engines three decades ago marked a shift in the way information was accessed and disseminated across the globe.
While these search engines were powerful and ushered in a host of applications like academic research and e-commerce, they were limited to providing a list of relevant websites to user queries.
The recent success of large language models (LLMs) however has paved the way for better systems like BingChat, Google’s SGE, and perplexity.ai that combine the strength of conventional search engines with the flexibility of generative models.
We dub these new age systems generative engines (GE) because they not only search for information, but also generate multi-modal responses by synthesizing multiple sources.
From a technical perspective, generative engines involve retrieving relevant documents from a database (such as the internet) and using large neural models to generate a response grounded on the sources, to ensure attribution and a way for the user to verify the information.

The usefulness of generative engines for both their developers and users is evident – users can access information faster and more accurately, while developers can craft precise and personalized responses, both to improve user satisfaction and revenue.
However, generative engines put the third stakeholder – website and content creators – at a disadvantage.
Generative Engines, in contrast to traditional search engines, remove the need to navigate to websites by directly providing a precise and comprehensive response, which can lead to a drop in organic traffic to websites and severely impact their visibility.
With several millions of small businesses and individuals relying on online traffic and visibility for their livelihood, generative engines will significantly disrupt the creator economy.
Further, the black-box and proprietary nature of generative engines makes it prohibitively difficult for content creators to control and understand how their content is ingested and portrayed by generative engines.
In this work, we take a first step towards a general creator-centric framework to optimize content for generative engines, which we dub Generative Engine Optimization (GEO), to empower content creators to navigate this new search paradigm with greater confidence.

GEO is a black-box optimization framework for optimizing the visibility of web content for proprietary and closed-source generative engines (Figure 1).
Generative Engine Optimization ingests a source website and outputs an optimized version of the website by tailoring and calibrating the presentation, text style, and content to increase the likelihood of visibility in generative engines.

However, note that the notion of visibility in generative engines is highly nuanced and multi-faceted (Figure 3).
While average ranking on the search results page is a good measure of visibility in traditional search engines which present a linear list of websites, this does not apply to generative engines.
Generative Engines provide rich and highly structured responses and embed websites as inline citations in the response, often embedding them with different lengths, at varying positions, and with diverse styles.
This therefore necessitates the need for visibility metrics tailor-made for generative engines, which measure the visibility of attributed sources over multiple dimensions, such as relevance and influence of citation to query, measured through both an objective and a subjective lens.
Our GEO framework proposes a holistic set of visibility metrics and enables content creators to create their own customized visibility metrics.

To facilitate faithful and extensive evaluation of GEO methods in this new paradigm, we propose GEO-bench, a benchmark consisting of 10K queries from a diverse set of domains and sources, specially adapted for generative engines.
Through systematic evaluation, we demonstrate that our proposed Generative Engine Optimization methods can boost visibility by up to 40% on a diverse set of queries, providing beneficial strategies for content creators to improve their visibility in the rapidly adapted generative engines.
Among other things, we find that including citations, quotations from relevant sources, and statistics can significantly boost source visibility, with an increase of over 40% across various queries.
Further, we discover a dependence of the effectiveness of Generative Engine Optimization methods on the domain of the query.

In summary, our contributions are three-fold:
(1) We propose Generative Engine Optimization, the first general framework for website owners to optimize their websites for generative engines.
(2) Our framework proposes a comprehensive set of visibility metrics designed for generative engines and enables content creators to create their own customized visibility metrics.
(3) To foster faithful evaluation of Generative Engine Optimization methods in the age of Generative Engines, we propose the first large-scale benchmark consisting of diverse search queries from wide-ranging domains and datasets, specially tailored for Generative Engines.

### Formulation & Methodology

#### Formulation of Generative Engines

Despite the deployment of a myriad of generative engines to millions of users already, there is currently no standard framework.
We provide a formulation that can accommodate various modular components incorporated in their design.

We describe a generative engine, which includes several backend generative models and a search engine for source retrieval.
A Generative Engine (GE) takes as input a user query $q_{u}$ and returns a natural language response $r$, where $P_{U}$ represents personalized user information, such as preferences and history.
The GE can be represented as a function:

While the response $r$ can be multimodal, we simplify it to a textual response in this section.

Generative Engines are comprised of two crucial components: a.) A set of generative models $G=\{G_{1},G_{2}...G_{n}\}$, each serving a specific purpose like query reformulation or summarization, and b.) A search engine $SE$ that returns a set of sources $S=\{s_{1},s_{2}...s_{m}\}$ given a query $q$.
We present a representative workflow in Figure 2, which at the time of writing, closely resembles the design of BingChat.
This workflow breaks down the input query into a set of simpler queries that are easier to consume for the search engine.
Given a query, a query re-formulator generative model, $G_{1}=G_{qr}$, generates a set of queries $Q^{1}=\{q_{1},q_{2}...q_{n}\}$, which are then passed to the search engine $SE$ to retrieve a multi-set of ranked sources $S=\{s_{1},s_{2},...,s_{m}\}$.
The sets of sources $S$ are passed to a summarizing model $G_{2}=G_{sum}$, which generates a summary $Sum_{j}$ for each source in $S$, resulting in the summary set ($Sum=\{Sum_{1},Sum_{2},...,Sum_{m}\}$).
The summary set is passed to a response-generating model $G_{3}=G_{resp}$, which generates a cumulative response $r$ backed by sources $S$. We refer readers to Algorithm 1 for a representative pseudocode describing the working of generative engine.
In this work, we focus on single-turn Generative Engines, but the formulation can be easily extended to multi-turn Generative Engines and we provide that formulation in Appendix A.

The response $r$ is typically a structured text response along with citations embedded within the text to support the information provided.
Citations are especially important given the tendency of LLMs to hallucinate information Ji et al. (2023).
Specifically, consider a response $r$ composed of sentences $\{l_{1},l_{2}...l_{o}\}$.
Each sentence may be backed by a set of citations that are a part of the retrieved set of documents $C_{i}\subset S$.
An ideal Generative Engine should ensure that all statements in the response are supported by relevant citations (high citation recall), and all citations accurately support the statements they’re associated with (high citation precision) Liu et al. (2023a).

#### Generative Engine Optimization

The advent of search engines led to the development of search engine optimization (SEO), a process to help website creators optimize their content to improve rankings in search engine results pages (SERP).
Higher rankings correlate with higher visibility and increased website traffic.
However, with generative engines becoming front-and-center in the information delivery paradigm and SEO not directly applicable to it, new techniques need to be developed.

To this end, we propose Generative Engine Optimization, a new paradigm where content creators aim to increase their visibility (or impression) in the generated responses.
We define the visibility of a website/citation $c_{i}$ in a cited response $r$ from a generative engine by the function $Imp_{wc}(c_{i},r)$ and the website creator wants to maximize this.
Simultaneously, from the perspective of the generative engine, the goal is to maximize the visibility of citations that are most relevant to the user query, i.e., maximize $\sum_{i}Imp_{wc}(c_{i},r)\cdot Rel(c_{i},q,r)$, where $Rel(c_{i},q,r)$ is a measure of the relevance of citation $c_{i}$ to the query $q$ in the context of response $r$.
However, both the functions $g$ and $Rel$ are subjective and not well-defined yet for generative engines, and we define them below.

###### Impressions for Generative Engines

In SEO, the impression (or visibility) of a website is simply determined by the average ranking of the website over a range of real queries.
But given that the nature of the output of generative engines is very different, impression metrics are not yet defined.
Unlike search engines, Generative Engines combine information from multiple sources in a single response.
Thus multiple factors such as length, uniqueness, and the presentation of the cited website determine the true visibility of a citation.
In this section, we use website and citation interchangeably.

To address this, we propose several impression metrics.
The “Word Count” metric is the normalized word count of sentences related to a citation. Mathematically, this is defined as:

Here $S_{c_{i}}$ is the set of sentences citing $c_{i}$, $S_{r}$ is the set of sentences in the response, and $|s|$ is the number of words in sentence $s$.
In cases where a sentence is cited by multiple sources, we simply share the word count with the citations. Intuitively, a higher word count correlates with the source playing a more important part in the answer, and thus the user gets higher exposure to that source.
However, since “Word Count” is not impacted by the ranking of the citations (whether it appears first, for example),
we propose a position-adjusted count that reduces the weight by an exponentially decaying function of the rank of the citation:

The above impression metrics are objective and well-grounded.
However, they ignore the subjective aspects of the impact of citations on the user’s attention.
To address this, we propose the "Subjective Impression" metric, which incorporates multiple facets such as 1.) relevance of the cited material to the user query, 2.) influence of the citation, which evaluates the degree to which the generated response depends on the citation, 3.) uniqueness of the material presented by a citation, 4.) subjective position, which measures how prominently the source is positioned from the user’s perspective, 5.) subjective count, which measures the amount of content presented from the citation as perceived by the user upon reading the citation, 6.) probability of clicking the citation, and 7.) diversity in the material presented.
To measure each of these sub-metrics, we use G-Eval Liu et al. (2023b), the current state-of-the-art for evaluation with LLMs which has a high correlation with human judgment for subjective tasks.
We present general algorithm to measure impression metrics of a response in Algorithm 2 and refer readers to Appendix B.3 for more details.

###### Generative Engine Optimization methods for website

To improve the impression metrics, content creators need to make changes to their websites.
To this end, we present several generative engine-agnostic strategies, referred to as Generative Engine Optimization methods (GEO).
Mathematically, every GEO method is a function $f:W\rightarrow W^{\prime}_{i}$, where $W$ is the initial web content, and $W^{\prime}$ is the modified website content after applying GEOmethod. A well-designed GEO method should increase the visibility of the website on which it is applied.
These methods are designed to implement textual modifications to $W$ in a manner that is independent of the queries. The range of these modifications spans from simple stylistic alterations to the incorporation of new content in a structured format.

We propose and evaluate a series of methods:
1: Authoritative: Modifies text style of the source content to be more persuasive while making authoritative claims, 2. Keyword Stuffing: Modifies content to include more keywords from the query, as would be expected in classical SEO optimization, 3. Statistics Addition: Modifies content to include quantitative statistics instead of qualitative discussion, wherever possible.
4. Cite Sources & 5. Quotation Addition: Adds relevant citations and quotations from credible sources, 6.) 6. Easy-to-Understand: Simplifies the language of website, while 7. Fluency Optimization improves the fluency of website text. 8. Unique Words & 9. Technical Terms: involves adding unique and technical terms respectively wherever posssible.

With the exception of methods 3, 4, and 5, the remaining methods do not necessitate the addition of new content to the website. Instead, these methods primarily focus on enhancing the presentation of the existing content in a way that increases its persuasiveness or makes it more appealing to the generative engine. These Generative Engine Optimization methods can be categorized into two broad types: Content Addition and Stylistic Optimization. In practice, these Generative Engine Optimization methods will be implemented by website owners modifying their text in accordance with these principles. However, for the purposes of our experiments, we implement Generative Engine Optimization methods by creating suitable prompts for the GPT-3.5 model to convert the source text into the modified text. The exact prompts used are provided in Appendix B.5.

In order to analyze the performance gain of our methods, for each input query, we randomly select one source to be optimized using each of the GEO methods separately. Further, for every method, 5 answers are generated per query to reduce statistical noise in the results. We refer readers to Appendix B.4 for more details.

##### Impressions for Generative Engines

In SEO, the impression (or visibility) of a website is simply determined by the average ranking of the website over a range of real queries.
But given that the nature of the output of generative engines is very different, impression metrics are not yet defined.
Unlike search engines, Generative Engines combine information from multiple sources in a single response.
Thus multiple factors such as length, uniqueness, and the presentation of the cited website determine the true visibility of a citation.
In this section, we use website and citation interchangeably.

To address this, we propose several impression metrics.
The “Word Count” metric is the normalized word count of sentences related to a citation. Mathematically, this is defined as:

Here $S_{c_{i}}$ is the set of sentences citing $c_{i}$, $S_{r}$ is the set of sentences in the response, and $|s|$ is the number of words in sentence $s$.
In cases where a sentence is cited by multiple sources, we simply share the word count with the citations. Intuitively, a higher word count correlates with the source playing a more important part in the answer, and thus the user gets higher exposure to that source.
However, since “Word Count” is not impacted by the ranking of the citations (whether it appears first, for example),
we propose a position-adjusted count that reduces the weight by an exponentially decaying function of the rank of the citation:

The above impression metrics are objective and well-grounded.
However, they ignore the subjective aspects of the impact of citations on the user’s attention.
To address this, we propose the "Subjective Impression" metric, which incorporates multiple facets such as 1.) relevance of the cited material to the user query, 2.) influence of the citation, which evaluates the degree to which the generated response depends on the citation, 3.) uniqueness of the material presented by a citation, 4.) subjective position, which measures how prominently the source is positioned from the user’s perspective, 5.) subjective count, which measures the amount of content presented from the citation as perceived by the user upon reading the citation, 6.) probability of clicking the citation, and 7.) diversity in the material presented.
To measure each of these sub-metrics, we use G-Eval Liu et al. (2023b), the current state-of-the-art for evaluation with LLMs which has a high correlation with human judgment for subjective tasks.
We present general algorithm to measure impression metrics of a response in Algorithm 2 and refer readers to Appendix B.3 for more details.

##### Generative Engine Optimization methods for website

To improve the impression metrics, content creators need to make changes to their websites.
To this end, we present several generative engine-agnostic strategies, referred to as Generative Engine Optimization methods (GEO).
Mathematically, every GEO method is a function $f:W\rightarrow W^{\prime}_{i}$, where $W$ is the initial web content, and $W^{\prime}$ is the modified website content after applying GEOmethod. A well-designed GEO method should increase the visibility of the website on which it is applied.
These methods are designed to implement textual modifications to $W$ in a manner that is independent of the queries. The range of these modifications spans from simple stylistic alterations to the incorporation of new content in a structured format.

We propose and evaluate a series of methods:
1: Authoritative: Modifies text style of the source content to be more persuasive while making authoritative claims, 2. Keyword Stuffing: Modifies content to include more keywords from the query, as would be expected in classical SEO optimization, 3. Statistics Addition: Modifies content to include quantitative statistics instead of qualitative discussion, wherever possible.
4. Cite Sources & 5. Quotation Addition: Adds relevant citations and quotations from credible sources, 6.) 6. Easy-to-Understand: Simplifies the language of website, while 7. Fluency Optimization improves the fluency of website text. 8. Unique Words & 9. Technical Terms: involves adding unique and technical terms respectively wherever posssible.

With the exception of methods 3, 4, and 5, the remaining methods do not necessitate the addition of new content to the website. Instead, these methods primarily focus on enhancing the presentation of the existing content in a way that increases its persuasiveness or makes it more appealing to the generative engine. These Generative Engine Optimization methods can be categorized into two broad types: Content Addition and Stylistic Optimization. In practice, these Generative Engine Optimization methods will be implemented by website owners modifying their text in accordance with these principles. However, for the purposes of our experiments, we implement Generative Engine Optimization methods by creating suitable prompts for the GPT-3.5 model to convert the source text into the modified text. The exact prompts used are provided in Appendix B.5.

In order to analyze the performance gain of our methods, for each input query, we randomly select one source to be optimized using each of the GEO methods separately. Further, for every method, 5 answers are generated per query to reduce statistical noise in the results. We refer readers to Appendix B.4 for more details.

### Experimental Setup

#### Evaluated Generative Engine

We use a 2-step setup for Generative Engine design, in accordance with previous works Liu et al. (2023a) and general design adopted by GEs:
the first step involves fetching relevant sources for input query, followed by a LLM generating response based on the fetched sources. In our setup, we fetch the top 5 sources from the Google search engine for every query. The answer is generated by gpt3.5-turbo model using the prompt same as prior work Liu et al. (2023a). We refer readers to Appendix B for more details.

#### Benchmark

Since there is currently no publicly available dataset containing Generative Engine related queries, we curate GEO-bench, a benchmark consisting of 10K queries from multiple sources, repurposed for generative engines, along with synthetically generated queries. The benchmark includes queries from nine different sources, each further categorized based on their target domain, difficulty, query intent, and other dimensions.

The datasets used in constructing the benchmark are as follows:

1. MS Macro, 2. ORCAS-1, and 3. Natural Questions: Kwiatkowski et al. (2019); Alexander et al. (2022); Craswell et al. (2021) These datasets contain real anonymized user queries from Bing and Google Search Engines.
These three collectively represent the common set of datasets that are used in search engine related research. However, Generative Engines will be posed with far more difficult and specific queries with the intent of synthesizing answers from multiple sources instead of searching for them. To this end, we re-purpose several other publicly available datasets:
4. AllSouls: This dataset contains essay questions from "All Souls College, Oxford University". The queries in this dataset require Generative Engines to perform appropriate reasoning to aggregate information from multiple sources.
5. LIMA: contains challenging questions requiring Generative Engines to not only aggregate information but also perform suitable reasoning to answer the question (eg: writing a short poem, python code.).
6. Davinci-Debtate Liu et al. (2023a) contains debate questions generated for testing Generative Engines.
7. Perplexity.ai Discover: These queries are sourced from Perplexity.ai’s Discover section, which is an updated list of trending queries on the platform.
8. ELI-5: This dataset contains questions from the ELI5 subreddit, where users ask complex questions and expect answers in simple, layman’s terms.
9. GPT-4 Generated Queries: To supplement diversity in query distribution, we prompt GPT-4 to generate queries ranging from various domains (eg: science, history) and based on query intent (eg: navigational, transactional) and based on difficulty and scope of generated response (eg: open-ended, fact-based)

Our benchmark contains 10K queries split into 8K,1K, and 1K train/val/test splits. Every query is tagged into multiple categories gauging various dimensions such as intent, difficulty, domain of query and format of answer type using GPT-4. We maintain the real-world query distribution, with our benchmark containing 80% informational queries, and 10% transactional and 10% navigational queries. We augment every query with cleaned text content of top 5 search results from the Google search engine. We believe GEO-bench is a comprehensive benchmark for evaluating Generative Engines and serves as a standard testbed for evaluating Generative Engines for multiple purposes in this and future works. More details can be found in Appendix B.2.

#### Evaluation Metrics

We evaluate all methods by calculating the Relative Improvement in Impression.
For an initial generated Response $r$ from sources $S_{i}\in\{s_{1},\dots,s_{m}\}$, and a modified response $r^{\prime}$, the relative improvement in impression of each source $s_{i}$ is measured as:

The modified response $r^{\prime}$ is generated by applying the Generative Engine Optimization method to be evaluated on of the sources $s_{i}$. The source $s_{i}$ to be optimized is randomly selected but kept constant for a particular query across all Generative Engine Optimization methods.

### Results

We evaluate a variety of Generative Engine Optimization methods, each designed to optimize website content for better visibility in Generative Engine responses.
These methods are compared against a baseline scenario where no optimization was applied.
Our evaluation was conducted on GEO-bench, a diverse benchmark encompassing a wide array of user queries from multiple domains and settings. The performance of these methods was measured using two distinct metrics: Position-Adjusted Word Count and Subjective Impression. The Position-Adjusted Word Count metric considers both the word count and the position of the citation in the GE’s response, while the Subjective Impression metric incorporates multiple subjective factors to compute an overall impression score.

Our results, detailed in Table 1, reveal that our Generative Engine Optimization methods consistently outperform the baseline across all metrics when evaluated on GEO-bench. This demonstrates the robustness of these methods to varying queries, as they were able to yield significant improvements despite the diversity of the queries. Specifically, our top-performing methods, namely Cite Sources, Quotation Addition, and Statistics Addition, achieved a relative improvement of 30-40% on the Position-Adjusted Word Count metric and 15-30% on the Subjective Impression metric compared to the baseline.

These methods, which involve adding relevant statistics (Statistics Addition), incorporating credible quotes (Quotation Addition), and including citations from reliable sources (Cite Sources) in the website content, require minimal changes to the actual content itself. Yet, they significantly improve the website’s visibility in Generative Engine responses, enhancing both the credibility and richness of the content.

Interestingly, stylistic changes such as improving the fluency and readability of the source text, i.e. methods Fluency Optimization and Easy-to-Understand also resulted in a significant boost of 15-30% in visibility. This suggests that Generative Engines not only value the content but also the presentation of the information.

Further, given generative models used in Generative Engine often are designed to follow instructions, one would expect a more persuasive and authoritative tone in website content can boost visibility.
However, to the contrary we find no significant improvement, demonstrating that Generative Engines are already somewhat robust to such changes. This points towards the need for website owners to focus more towards improving the presentation of content and making it more credible.

Finally, we also evaluate the idea of using keyword stuffing, i.e. adding more relevant keywords to the website content. While this technique has been widely used for Search Engine Optimization, we find such methods have little to no performance improvement on Generative Engine’s responses. This underscores the need for website owners to rethink their optimization strategies for Generative Engines, as techniques effective for traditional SEO may not necessarily translate to success in the new paradigm.

### Analysis

#### Domain-Specific Generative Engine Optimizations

In Section 4, we presented the improvements achieved by Generative Engine Optimization across the entirety of the GEO-bench benchmark. However, it is important to note that in real-world SEO scenarios, domain-specific optimizations are often applied to websites. With this in mind, and considering that we provide categories for every query in GEO-bench, we delve deeper into the performance of various GEO methods across these categories.

Table 2 provides a detailed breakdown of the categories where our GEO methods have proven to be most effective. A careful analysis of these results reveals several intriguing observations.
For instance, Authoritative significantly improves performance in the context of debate-style questions and queries related to the “historical” domain. This observation aligns with our intuition, as a more persuasive form of writing is likely to hold more value in debates like contexts.

Similarly, the addition of citations through Cite Sources is particularly beneficial for factual questions. This is likely because citations provide a source of verification for the facts presented, thereby enhancing the credibility of the response.
The effectiveness of different GEO methods varies across different domains. For example, as shown in row 5 of Table 2, domains such as ‘Law & Government’ and question types like ‘Opinion’ benefit significantly from the addition of relevant statistics in the website content, as implemented by Statistics Addition. This suggests that the incorporation of data-driven evidence can enhance the visibility of a website in particular contexts especially these.
The method Quotation Addition is most effective in the ‘People & Society’, ‘Explanation’, and ‘History’ domains. This could be because these domains often involve personal narratives or historical events, where direct quotes can add authenticity and depth to the content.

Overall, our analysis suggests that website owners should strive towards making domain-specific targeted adjustments to their websites for higher visibility.

#### Simultaneous Optimization of Multiple Websites

In the evolving landscape of Generative Engines, it is anticipated that GEO methods will be widely adopted, leading to a scenario where all source contents are optimized using GEO. To understand the implications of this scenario, we conducted an evaluation of Generative Engine Optimization methods by optimizing all source contents simultaneously. The results of this evaluation are presented in Table 3. A key observation from our analysis is the differential impact of GEO on websites based on their ranking in the Search Engine Results Pages (SERP). Interestingly, websites that are ranked lower in SERP, which typically struggle to gain visibility, benefit significantly more from GEO than those ranked higher. This is evident from the relative improvements in visibility shown in Table 3. For instance, the Cite Sources method led to a substantial 115.1% increase in visibility for websites ranked fifth in SERP, while on average the visibility of the top-ranked website decreased by 30.3%.

This finding underscores the potential of GEO as a tool to democratize the digital space. Importantly, many of these lower-ranked websites are often created by small content creators or independent businesses, who traditionally struggle to compete with larger corporations that dominate the top rankings in search engine results. The advent of Generative Engines may initially seem disadvantageous to these smaller entities. However, the application of GEO methods presents an opportunity for these small content creators to significantly improve their visibility in Generative Engine responses. By enhancing their content using GEO, they can reach a wider audience, thereby leveling the playing field and allowing them to compete more effectively with larger corporations in the digital space.

#### Qualitative Analysis

We present a qualitative analysis of GEO methods in Table 4. The analysis contains representative examples, where GEO methods boost source visibility while making minimal changes. For each of the three methods, a source is optimized by making suitable additions and deletions in the text. In the first example, we see, that simply adding the source of a statement in text, can significantly boost visibility in the final answer, requiring minimal effort on the content creator’s part. The second example demonstrates that the addition of relevant statistics wherever possible, ensures source visibility increasing in the final Generative Engine response. Finally, the third row suggests, that merely emphasizing parts of the text and using a more persuasive text style can also lead to decent improvements in visibility.

### GEO in the Wild : Experiments with Deployed Generative Engine

To further reinforce the efficacy of our proposed Generative Engine Optimization methods, we evaluate them on Perplexity.ai a deployed Generative Engine with a large user base. Since perplexity.ai does not allow the user to specify source URLs, we instead provide source text as file uploads to perlexity.ai. We ensure all answers are generated only using the file sources provided. We evaluate all our methods on a subset of 200 samples of our test set. Other experimental procedures are the same as our main results. Results using Perplexity.ai are shown in Table 5.
We find, similar to our generative engine Quotation Addition performs the best in Position-Adjusted Word Count with a relative improvement of 22% over the baseline. Further, methods that performed well in our generative engine such as Cite Sources, Statistics Addition show high improvements of up to 9% and 37% on the two metrics. Further, our observations such as the ineffectiveness of traditional methods used in SEO such as Keyword Stuffing are further highlighted, as it performs 10% worse than the baseline. The result underscores the importance of developing different Generative Engine Optimization methods to benefit the content-creators and further highlights that our simple-to-implement proposed methods can be used directly by content-creators, thus having a high real-world impact.

### Related Work

### Conclusion

In this work, we formulate the new age search engines that we dub generative engines and propose Generative Engine Optimization (GEO) to help put the power in the hands of content creators to optimize their content.
We define impression metrics for generative engines and propose a benchmark encompassing diverse user queries from multiple domains and settings, along with relevant sources needed to answer those queries.
We propose several ways to optimize content for generative engines and demonstrate that these methods are capable of boosting source visibility by up to 40% in generative engine responses.
Among other things, we find that including citations, quotations from relevant sources, and statistics can significantly boost source visibility.
Further, we discover a dependence of the effectiveness of Generative Engine Optimization methods on the domain of the query.
Our work serves as a first step towards understanding the impact of generative engines on the digital space and the role of Generative Engine Optimization in this new age of search engines.

### Ethical Considerations and Reproducibility Statement

In our study, we focus on enhancing the visibility of websites in generative engines. We do not directly interact with sensitive data or individuals. While the sources we retrieve from search engines may contain biased or inappropriate content, these are already publicly accessible, and our study neither amplifies nor endorses such content. We believe that our work is ethically sound as it primarily deals with publicly available information and aims to improve the user experience in generative engines.

Regarding reproducibility, we have made our code available to allow others to replicate our results. Our main experiments have been conducted with five different seeds to minimize potential statistical deviations.
