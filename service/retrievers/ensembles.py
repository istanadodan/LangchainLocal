from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
import logging
from core.llm import get_llm, get_embeddings
from core.query import get_retriever
import re

from service.loader.pdf_loader import get_documents
from service.utils.text_split import split_documents


def query(query: str, doc_path: str, k: int = 1):
    _retriever: EnsembleRetriever = ensembles_retriever(doc_path, k, dense_rate=0.6)
    _result = _retriever.get_relevant_documents(query)

    logging.info(f"retrieve output:\n{_result}")
    return list(map(lambda x: re.sub(r"\n+", "\n", x.page_content), _result))


def ensembles_retriever(doc_path: str, k: int, dense_rate: float = 0.0):
    from service.utils.retrieve_params import get_default_vsparams

    docs = split_documents(get_documents(files=doc_path), chunk_size=300)
    _sparse_retriever = BM25Retriever.from_documents(docs, k=k)
    # _sparse_retriever.k = k

    kwargs = get_default_vsparams(doc_path=doc_path)
    _dense_retriever = get_retriever(search_type="mmr", k=k, **kwargs)
    if not _dense_retriever or not _sparse_retriever:
        raise Exception

    # 앙상블 조회기
    return EnsembleRetriever(
        retrievers=[_sparse_retriever, _dense_retriever],
        weights=[1 - dense_rate, dense_rate],
    )
