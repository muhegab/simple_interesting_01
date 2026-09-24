from typing import TypedDict, Annotated, Literal
from pydantic import BaseModel, Field
from langchain_openrouter import ChatOpenRouter
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import interrupt, Command

# Use "Abstract Syntax Tree" module to evaluate a dictionary from another text but non-python format file.
import ast
with open("./api/llm/ApiKeys.txt") as apiKeysFile:
    apiKeys = ast.literal_eval(apiKeysFile.read())

# Initialise a chat model
chatOpenRouter = ChatOpenRouter(
    model='inclusionai/ling-3.0-flash-fin:free',
    # model='google/gemma-4-31b-it:free',
    api_key=apiKeys["ChatOpenRouter"],
    temperature=0
)

# Initialise another chat model.
chatGroq = ChatGroq(
    model="openai/gpt-oss-120b", # Text, Tool, Reasoning and multilingual
    # model="qwen/qwen3.8-27b", # image and text model.
    api_key=apiKeys["ChatGroq"]
)

llm = chatGroq

# The desired graph is a to chat, RAG or coding based on the user input. The graph will be designed to handle different types of requests and route them to the appropriate model.
# We will call the routing condition "classifier".
# Declare a class to receive the classification result from the LLM model, which the LLM model will figure out.
class IntentClassifier(BaseModel):
    # The intent of the user request; chat, RAG or coding.
    # "Field(..., )" means that this variable must be filled during initialisation and has no default value, this is the validation importance of pyDantic.
    # "description" is passed by LangChain to the LLM mdoel.
    intent:\
        Literal["chat", "RAG", "coding"] =\
            Field(...,
                  description="Please classify from the user's request whether the user wants to chat, bring data from RAG, or to code.")

# Define a customed state class for LangGraph, that will hold the messages and the intent of the user request. The state class will be used to pass the messages and the intent to the nodes of the graph.
class State(TypedDict):
    messages: Annotated[list, add_messages]
    message_intent: str | None
    next_node: str | None # needed for a conditional edge to work properly.

# Define a function to classify the intent of the user request. The function will take the state as input and return the state with the intent of the user request. The function will use the IntentClassifier to classify the intent of the user request.
# Some variables are passed and accessed by the defined LangGraph node, through the defined TypedDict "state".
def classify_intent(state: State):
    # The LLM model figures out the intent of the user request based on the user message.
    # Extract the classification result from the LLM model in the format of the class IntentClassifier, which inherits from pyDantic BaseModel.
    structured_llm = llm.with_structured_output(IntentClassifier)

    # Ask the LLM model and get a response in a structured format.
    classification_result = structured_llm.invoke(
        [
            {
                "role": "system",
                # Explain to the LLM model what the intent is and what the possible values should be. Explained also in the class IntentClassifier, which the LLM will use to structure the output.
                "content": "Please classify the intent of the user's request. The intent can be either search in your model \"chat\", look in a document \"RAG\" or \"coding\"."
            },
            {
                "role": "user",
                # Pass the user message to the LLM model to classify the intent of the user request.
                "content": state["messages"][-1].content
            }
        ]
    )

    # Return a value to the word "intent" in the input dictionary object "state".
    # LangGraph updates the mentioned member variable in the input dictionary object "state".
    return {"message_intent": classification_result.intent}

# Define the function of the chat node.
def prompt_llm_chat(state: MessagesState):
    # Pass the messages to the model and get a response.
    response = llm.invoke(
        [
            {
                "role": "system",
                "content": "You are a helpful assistant. Please answer the user's request based on the messages provided."
            },
            {
                "role": "user",
                "content": state["messages"][-1].content
            }
        ]
    )

    # return response["messages"][-1].content
    return {"messages": [response]}

texts_document = [
    "Apple makes very good computers.", # Sapce region 01
    "I beleive Apple is innovative!", # Sapce region 01
    "I believe apples are healthy!", # Space region 02
    "I love apples.", # Space region 02
    "I am a fan of MacBooks.", # Sapce region 01
    "I enjoy oranges.", # Space region 02
    "I like Lenovo Thinkpads.", # Sapce region 01
    "I think pears taste very good.", # Space region 02
    "I hate bananas.", # Space region 02
    "I dislike raspberries.", # Space region 02
    "I despise mangos.", # Space region 02
    "I love linux.", # Space region 01
    "I hate windows.", # Space region 01
]

from langchain_core.vectorstores import InMemoryVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_cohere import CohereEmbeddings
# Let an AI model assigns dimensions to the texts in a vector space and then store their assignments.
# Dimensions are given to texts, because the texts are not splitted into chunks.
vector_store = InMemoryVectorStore.from_texts(
        # Add the texts to the vector store.
        texts_document,

        # Mention the AI model to use for embedding the texts into a vector space.
        embedding=
            GoogleGenerativeAIEmbeddings( # Google made better sortings in the vector space than Cohere.
                model="gemini-embedding-001",
                api_key=apiKeys["GoogleGenerativeAIEmbeddings"]
            )
            # CohereEmbeddings(
            #     model="embed-english-v3.0",
            #     cohere_api_key=apiKeys["CohereEmbeddings"]
            # )
)

# Define the function of the RAG node.
def prompt_llm_rag(state: MessagesState):
    # Since RAG node is chosen, search the text of the knowledge base for the user request.
    retrieved_texts = vector_store.similarity_search(state["messages"][-1].content, k=3)

    context = "\n\n".join(f"- {text.page_content}" for text in retrieved_texts)

    # Pass the messages to the model and get a response.
    response = llm.invoke(
        [
            {
                "role": "system",
                "content": "Respond with \"I am RAG\", and then answer the user's request based on the provided context.\nConext:\n" + context
        }] + state["messages"]
    )

    # return response["messages"][-1].content
    return {"messages": [response]}

@tool
def edit_file(file_path: str, new_content: str) -> str:
    """
    Edits a file at the given file path with the new content.
    """
    print(f"Editing file: {file_path} with new content:\n{new_content}")
    try:
        with open(file_path, 'a') as f:
            f.write(new_content)
            # The returned message is to be shown on the terminal, only if the state is forwarded into a node that will print the message, such as the print_llm_coding node.
            return {"messages":
                    [
                        {
                            "role": "assistant",
                            "content": f"File {file_path} has been updated."
            }]}
    except Exception as e:
        return {"messages":
                [
                    {
                        "role": "assistant",
                        "content": f"An error occurred while editing the file: {str(e)}"
        }]}

# bind the edit_file tool.
llm = llm.bind_tools([edit_file])

# Define the function of the coding node.
def prompt_llm_coding(state: MessagesState):
    print("Coding node is invoked.")

    # Pass the messages to the model and get a response.
    response = llm.invoke(
        [
            {
                "role": "system",
                "content": "Respond with \"I am coding\". You are a good software developer. Your response can include modifications in local files in the computer. For modifying the local files, you can use the tool \"edit_file\". The tool takes two arguments: the file path and the new content of the file. You can use this tool to edit files in the local computer. Please answer the user's request based on the messages provided."
            }
        ] + state["messages"]
    )

    return {"messages":[response]}
    # Note: The input request was: "please write 123 into 101.md".

# Define the function of the HIL node.
def prompt_llm_hil(state: State):
    # Let this node interrupt the graph flow and request a confirmation decision from the user.
    # The function "interrupt" will print the message and wait for the user to input a decision, and also waits for the script to reinvoke the graph to resume the flow.
    decision = interrupt(
        "Please confirm if you want to proceed with the previouse coding request:\n" + state["messages"][-1].content + "\nType 'yes' to proceed, 'no' to cancel, or  type a revised request.",
    )

    # Strip the decision of the user and check if it is "yes" or "no" or a revised request.
    decisionTexts = str(decision).strip().lower()

    if decisionTexts in ["y", "yes", "ok", "approve", "confirm"]:
        # If the user confirms, proceed with the coding request.
        return {"next_node": "ModifyFile"}
    elif decisionTexts in ["n", "no", "cancel", "reject"]:
        # If the user rejects, cancel the coding request.
        return {
            "messages":[
                {
                    "role":"assistant",
                    "content":"The coding request has been cancelled by the user."
            }],
            # Label "next_node" of the object of the class "state". This will be checked by the conditional edge to determine the next node to go to.
            "next_node": "denied"
        }
    else:
        # If the user provides a revised request, update the messages with the revised request and proceed with the coding request.
        return {
            "messages":[
                {
                    "role":"user",
                    # Pass the revised request as a new coding request.
                    "content":decisionTexts
            }],
            "next_node": "analyseChangeRequest"
        }
    
# Define the function of a node, which summarises the conversation history and adds it into  the context.
def prompt_llm_summarise(state: MessagesState):
    # Pass the messages to the model and get a response.
    response = llm.invoke(
        [
            {
                "role": "system",
                "content": "Please summarise the conversation history and add it into the context for the next request."
            }
        ] + state["messages"]
    )

    return {"messages":[response]}

# Initialise a graph builder with the customised state class.
graph_builder = StateGraph(State)

# Add the pre-designed nodes of the graph.
graph_builder.add_node(classify_intent)
graph_builder.add_node(prompt_llm_chat)
graph_builder.add_node(prompt_llm_rag)
graph_builder.add_node(prompt_llm_coding)
graph_builder.add_node(prompt_llm_hil)
graph_builder.add_node("editFileTool", ToolNode([edit_file]))
graph_builder.add_node(prompt_llm_summarise)

# Add the edges of the graph, including the conditional edge.
graph_builder.add_edge(START, "classify_intent")
graph_builder.add_conditional_edges(
    # The start node of this conditional edge.
    "classify_intent",
    # A function that takes the state as an input and returns the value of the member variable "message_intent" in the state.
    lambda state: state["message_intent"],
    # A dictionary of "string of previous input": "corresponding destination node"
    {"chat": "prompt_llm_chat", "RAG": "prompt_llm_rag", "coding": "prompt_llm_coding"}
)
graph_builder.add_edge("prompt_llm_chat", "prompt_llm_summarise")
graph_builder.add_edge("prompt_llm_rag", "prompt_llm_summarise")
graph_builder.add_edge("prompt_llm_coding", "prompt_llm_hil")
graph_builder.add_conditional_edges(
    "prompt_llm_hil",
    lambda state: state.get("next_node"),
    {
        "ModifyFile": "editFileTool",
        "analyseChangeRequest": "prompt_llm_coding",
        "denied": "prompt_llm_summarise"
    }
)
graph_builder.add_edge("editFileTool", "prompt_llm_summarise")
graph_builder.add_edge("prompt_llm_summarise", END)


# Initialise a checkpointer to save a conversation in memory.
checkpointer = InMemorySaver()

# Compile the graph to make it ready for execution.
# Integrate the checkpointer to save sessions (conversation with the thread IDs) in memory.
graph = graph_builder.compile(checkpointer=checkpointer)

graph.get_graph().draw_mermaid_png(output_file_path="./api/llm/LangGraph_03_Graph.png")

states = ("new_request", "HIL")
state = states[0]

# Define a function to interaact with the graph from any interface, not necessarily the terminal.
# The function takes the user's request and returns the response.
def run_graph(user_message: str) -> str:
    global state
    output_response = ""
    # If it is a new user's request.
    if state == states[0]:
        # Invoke the graph with the user message, the memory and the configuration and the thread ID.
        response = graph.invoke(
            {
                "messages":[
                    {
                        "role": "user",
                        "content": user_message
            }]},

            # Initialise a thread ID for the requests of the same conversation.
            config = {"configurable": {"thread_id": "my_conversation_01"}}
        )

    # Else if the graph was witing for decision from the user about the last previous request.
    elif state == states[1]:
        # After the user's decision, the graph will continue to run and the response will be returned. The returned response will change the value of "__interrupt__" to "None" and the graph will continue to run.
        response = graph.invoke(
            Command(resume=user_message),
            # The thread ID of the previous request.
            config = {"configurable": {"thread_id": "my_conversation_01"}}
        )

    # If the graph is interrupted anytime by a node.
    if "__interrupt__" in response:
        # Print the interrupt message and wait for the user to input a decision.
        output_response = "The graph is interrupted by a node and the interrupt message is:" + "\n"
        output_response += response['__interrupt__'][0].value + "\n"
        output_response += "Please enter your decision to proceed, cancel, or change the coding request: \n> " 

        # Set the state as waiting for a messge regarding a decision for a HIL step in the last previous request.
        state = states[1]

    # No HIL interruption is required as a step from the flow of the graph.
    else:
        # Print the response from the model.
        output_response = "The forelast response from the model is:\n" + response['messages'][-2].content + "\n"
        output_response += "The final response from the model is:\n" + response['messages'][-1].content + "\n"
        output_response += "\n\n\n"

        # Reset the state for the next function call.
        state = states[0]

    return output_response
