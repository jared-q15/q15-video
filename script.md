# q15 — The AI Agent That Remembers

## Script (Two Minute Papers style, ~5 min)

---

Imagine you have a brilliant colleague. Sharp, fast, encyclopedic knowledge. But every single morning, they walk into the office with total amnesia. Every day, you have to re-explain the project. Re-introduce the team. Re-explain what was decided yesterday. By lunchtime, you have spent all your time on context and almost none on actual work.

That is what using most AI assistants is like. And it is not a bug. It is the design. Every new chat window is a blank slate. The model has no idea who you are, what you care about, or what you discussed last Tuesday. You pour context in, the model answers, the window closes, and everything is gone.

Now, you might say, "But wait, there are memory features. There are custom instructions." And yes, those exist. But they are tiny. A few paragraphs in a system prompt. They do not grow. They do not learn. They are a sticky note on a refrigerator, not a memory.

So a developer in Düsseldorf named Adriaan asked a simple question. What if your AI agent had real memory? Not chat history bolted on as an afterthought, but a layered memory system designed from the ground up. What would that look like?

The answer is q15. And dear friends, it is completely open source, written in Go, and it is absolutely brilliant.

Here is how it works. q15 is not a model. It is not another ChatGPT. It is an agent runtime. Think of it as the operating system around the model. The model is the brain. q15 is everything else: the memory, the hands, the tools, the colleagues down the hall.

Let me walk you through the memory, because this is where it gets exciting. q15 has not one memory system but five, each with a different purpose. Core memory is always loaded into the prompt. It holds the agent's identity, the user's preferences, the agent's personality. It is the stuff that should never be forgotten. Working memory holds the active state: what are we doing right now, what is pending, what was the last thing we figured out. Semantic memory stores durable facts and knowledge, pulled in when needed, not crammed into every prompt. History preserves the full conversational transcript. And then there is a zettelkasten, a network of atomic linked notes that grows over time, connecting ideas across conversations the way a researcher connects citations across papers.

Five memory systems. Each one designed for a different timescale and a different purpose. This is not a context window with a longer tape. This is architecture.

But memory alone is not enough. You also need skills. And here is where q15 does something elegant. A skill in q15 is just a markdown file. It has a name, a description, and a body of instructions. Sometimes it comes with scripts. The agent reads it, understands what it can do, and uses it. Want your agent to transcribe audio? There is a skill for that. Want it to search your library? Skill for that. Want it to manage a zettelkasten? Skill for that. And the agent can even create new skills itself.

This is composable. You do not hardcode capabilities. You describe them, and the model picks them up. It is closer to how a human colleague reads a manual than how a traditional program calls an API.

And then there is delegation. q15 can spawn sub-agents. Specialized agents with their own model, their own tools, their own context window. The main agent can say, "I need you to go research this, I need you to go transcribe that," and the sub-agent goes off and does it. Different models for different tasks. Maybe a fast cheap model for the routine work, a powerful one for the hard reasoning. The parent stays focused, the sub-agent handles the detail.

Now, here is something I really appreciate. q15 is not locked to one AI company. It is multi-provider. You can route to Ollama running locally on your own machine, completely private, nothing leaves your network. You can route to Gemini, to other cloud providers. You choose. The model is a component, not a platform. You are not renting someone else's brain. You own the infrastructure around it.

So what is the key result here? It is not a benchmark number. It is a qualitative shift. Most AI assistants are disposable. You use them, you close the window, they are gone. q15 is accumulative. It gets richer over time. It remembers your projects. It remembers your preferences. It remembers what you read and what you thought about it. The longer you use it, the more useful it becomes. That is a fundamentally different relationship with an AI system.

Now, I want to be honest about limitations. q15 is not a model. It depends on the underlying models being good. If the model is weak, q15 cannot fix that. It is infrastructure, not intelligence. And it is early. There are open issues, active development, rough edges. This is not a finished product on a store shelf. It is a live project on GitHub.

But here is the thing. All of this is open source. The code is on GitHub at github.com/q15co/q15. You can read every line. You can run it yourself. You can contribute. There is no API lock-in, no usage meter ticking in the background, no telemetry phoning home. The memory lives on your disk, in your volumes, under your control.

And I think that matters. Because right now, the dominant model for AI is: you rent access to a brain that forgets you, and the company that owns it decides what it remembers, what it forgets, and what it costs. q15 inverts that. The agent is yours. The memory is yours. The infrastructure is yours.

That is not just a technical decision. It is a decision about who has power. And they give all of it away for free.

What a time to be alive.