from pydantic import BaseModel, Field

class CriticScore(BaseModel):
    score: int = Field(description="Score from 1 to 5")
    reasoning: str = Field(description="Detailed reasoning for the score")
    issues_found: list[str] = Field(description="List of specific issues found in the output")

async def factual_critic_node(state: dict) -> dict:
    """
    Evaluates factual accuracy against the expected output.
    Uses GPT-4o for rigorous checking.
    """
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    structured_llm = llm.with_structured_output(CriticScore)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert Factual Accuracy Critic. Compare the ACTUAL output to the EXPECTED output. Score 1-5 where 5 is perfectly accurate and consistent with the expected facts. Provide reasoning and list any hallucinated or missing facts."),
        ("user", "EXPECTED:\n{expected}\n\nACTUAL:\n{actual}")
    ])
    
    chain = prompt | structured_llm
    result = await chain.ainvoke({"expected": state.get("expected_output"), "actual": state.get("actual_output")})
    
    return {"factual_score": result.score, "factual_reasoning": result.reasoning, "issues": result.issues_found}

async def logical_critic_node(state: dict) -> dict:
    """
    Evaluates logical consistency and instruction following.
    Uses a cheaper/faster model.
    """
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    structured_llm = llm.with_structured_output(CriticScore)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert Logical Consistency Critic. Analyze the ACTUAL output based on the INPUT prompt. Does it follow instructions? Is the reasoning sound? Score 1-5 where 5 is perfectly logical and follows all instructions. Provide reasoning and list any logical flaws."),
        ("user", "INPUT:\n{input}\n\nACTUAL:\n{actual}")
    ])
    
    chain = prompt | structured_llm
    result = await chain.ainvoke({"input": state.get("input"), "actual": state.get("actual_output")})
    
    return {"logical_score": result.score, "logical_reasoning": result.reasoning, "issues": result.issues_found}
