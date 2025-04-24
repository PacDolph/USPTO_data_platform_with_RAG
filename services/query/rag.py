from haystack import Pipeline
from haystack_integrations.components.retrievers.chroma import ChromaQueryTextRetriever
from haystack.components.builders.prompt_builder import PromptBuilder
from haystack.components.generators import OpenAIGenerator

template = """
Given the following information, answer the question.

Context: 
{% for document in documents %}
    {{ document.content }}
{% endfor %}

Question: {{ query }}?
"""

def run_answer(query, document_store):
    answer = Pipeline ()
    answer.add_component("retriever", ChromaQueryTextRetriever(document_store=document_store))
    answer.add_component("prompt_builder", PromptBuilder(template=template))
    answer.add_component("llm_generator", OpenAIGenerator())
    answer.connect("retriever", "prompt_builder")
    answer.connect("prompt_builder", "llm_generator")
    res=answer.run({
        "prompt_builder": {
            "query": query
        },
        "retriever": {
            "query": query
        }
    })
    return res    